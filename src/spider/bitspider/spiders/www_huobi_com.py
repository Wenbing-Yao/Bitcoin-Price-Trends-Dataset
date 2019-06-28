# -*- coding: utf-8 -*-
import json
import pickle


import scrapy
import dateutil.parser as dateparser
from dateutil.tz import gettz


class WwwHuobiComSpider(scrapy.Spider):
    name = 'www.huobi.com'
    allowed_domains = ['www.huobi.com']
    start_urls = ['https://www.huobi.com/news/article/list?'
                  'currentPage=1&newsColumnId={}'.format(i) for i in [1, 5]]
    custom_settings = {
        'ITEM_PIPELINES': {
            'bitspider.pipelines.HuobiComPipeline': 300
        }
    }

    urls = set()

    def parse(self, response):
        data = json.loads(response.text)

        for item in data['data']['items']:
            if '比特币' in [tag['tagsName'] for tag in item['tags']]:
                url = '/news/article_{}.html'.format(item['id'])
                if url in self.urls:
                    continue
                self.urls.add(url)
                yield response.follow(
                    url, callback=self.parse_content, priority=100)

        next_page = data['data']['currentPage'] + 1
        if next_page > data['data']['pages']:
            return

        yield response.follow(
            '/news/article/list?currentPage={}&newsColumnId=1'.format(
                next_page),
            self.parse, priority=50)

    def parse_content(self, response):
        url = response.url
        title = response.xpath('//*[@id="detailTitle"]/text()').extract_first()
        birthday = response.xpath(
            '/html/body/div/div[2]/div[1]/div[1]/'
            'div/p[1]/span[2]/text()').extract_first()

        date = dateparser.parse('birthday').astimezone(gettz('Asia/Shanghai'))
        content = '\n'.join(response.xpath(
            '//div[@class="newsDetails"]/p/text()').extract()[:-2])

        yield {
            'url': url,
            'title': title,
            'birthday': birthday,
            'date': str(date),
            'content': content,
            'year': date.year,
            'month': date.month,
            'day': date.day
        }

    def dump(self):
        with open('data/huobi.com/urls.pkl', 'wb') as fout:
            pickle.dump(self.urls, fout)
