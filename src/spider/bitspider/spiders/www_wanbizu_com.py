# -*- coding: utf-8 -*-
import scrapy

import dateutil.parser as dateparser
from bs4 import BeautifulSoup
from dateutil.tz import gettz


class WwwWanbizuComSpider(scrapy.Spider):
    name = 'www.wanbizu.com'
    allowed_domains = ['www.wanbizu.com']
    start_urls = ['http://www.wanbizu.com/plus/search.php?'
                  'keyword=比特币&searchtype=titlekeyword&channeltype=0&'
                  'orderby=&kwtype=0&'
                  'pagesize=100&typeid=0&TotalResult=6793&PageNo={}'.format(i)
                  for i in range(1, 69)]

    custom_settings = {
        'ITEM_PIPELINES': {
            'bitspider.pipelines.WanbizuComPipeline': 300
        }
    }

    def parse(self, response):
        urls = response.xpath('//h2').xpath('a/@href').extract()
        print(response.url, len(urls))

        for url in urls:
            yield response.follow(url, callback=self.parse_content,
                                  priority=100)

    def parse_content(self, response):
        url = response.url
        print(url)
        title = response.xpath(
            '/html/body/div[6]/div[1]/div[2]/h1/text()').extract_first()
        content = BeautifulSoup(
            ''.join(response.css('p').extract()[
                    :-6]).replace('\r\n\t\u3000\u3000', ''),
            'lxml').get_text()
        birthday = response.xpath(
            '/html/body/div[6]/div[1]/div[2]/div[1]/'
            'small[1]/text()').extract_first()
        date = dateparser.parse(birthday).astimezone(gettz('Asia/Shanghai'))

        author = response.xpath(
            '/html/body/div[6]/div[1]/div[2]/div[1]/'
            'small[2]/text()').extract_first()
        source = response.xpath(
            '/html/body/div[6]/div[1]/div[2]/div[1]/'
            'small[3]/text()').extract_first()[3:]

        return {
            'url': url,
            'title': title,
            'content': content,
            'date': str(date),
            'author': author,
            'source': source,
            'year': date.year,
            'month': date.month,
            'day': date.day
        }
