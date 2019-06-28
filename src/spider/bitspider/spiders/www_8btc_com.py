# -*- coding: utf-8 -*-
import os
import logging


import scrapy
import dateutil.parser as dateparser
from bs4 import BeautifulSoup


if not os.path.exists('./log'):
    os.mkdir('log')

logging.basicConfig(
    filename='log/8btc.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


class Www8btcComSpider(scrapy.Spider):
    name = 'www.8btc.com'
    allowed_domains = ['www.8btc.com']
    start_urls = ['http://www.8btc.com/sitemap?cat={}'.format(i)
                  for i in [7, 572, 897, 413]]
    custom_settings = {
        'ITEM_PIPELINES': {
            'bitspider.pipelines.Www8btcComPipeline': 300
        }
    }
    got_urls = set()

    def parse(self, response):
        urls = response.xpath('//*[@id="zan-bodyer"]/div/div/div/div[2]/'
                              'div[1]/div/div/div/ul/li/a/@href').extract()
        titles = response.xpath('//*[@id="zan-bodyer"]/div/div/div/div[2]/'
                                'div[1]/div/div/div/ul/li/a/text()').extract()
        next_url = response.xpath(
            '//*[@id="zan-bodyer"]/div/div/div/div[2]/'
            'div[1]/div/div/div/ul/li[21]/span/a[text()="下一页"]/@href'
        ).extract_first()

        if len(urls) != len(titles):
            logging.warning('urls and titles length not match: urls:{}\r\n'
                            ', titles: {}\r\n'.format(urls, titles))
        else:
            for url, title in zip(urls, titles):
                if url in self.got_urls or '链周刊' in title:
                    continue

                self.got_urls.add(url)
                yield response.follow(url, callback=self.parse_content,
                                      priority=100)

        if next_url is not None:
            res = response.follow(next_url, self.parse, priority=50)
            if res is not None:
                yield res

    def parse_content(self, response):
        # print(url)
        try:
            url = response.url
            title = response.xpath(
                '//article/div[3]/h1/text()').extract_first()
            author = response.xpath('//article/div[4]/span[2]/a/text()'
                                    ).extract_first().strip()
            birthday = response.xpath('//article/div[4]/span[3]/time/@datetime'
                                      ).extract_first()
            views = response.xpath('//article/div[4]/span[7]/text()'
                                   ).extract_first().strip()
            content = ' '.join(response.xpath(
                '//*[@id="zan-bodyer"]/div/div/'
                'div[1]/article/div[5]/p').extract())
            content = ' '.join(BeautifulSoup(
                content, 'lxml').get_text().split())

            date = dateparser.parse(birthday)
            year, month, day = date.year, date.month, date.day
        except Exception:
            return

        yield {
            'url': url,
            'author': author,
            'title': title,
            'date': birthday,
            'content': content,
            'views': views,
            'year': year,
            'month': month,
            'day': day
        }
