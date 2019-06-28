# -*- coding: utf-8 -*-
import os
import logging
import pickle
import scrapy

import dateutil.parser as dateparser
from dateutil.tz import gettz
from bs4 import BeautifulSoup

if not os.path.exists('./log'):
    os.mkdir('log')

logging.basicConfig(
    filename='log/cnbc.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


class CnbcComSpider(scrapy.Spider):
    name = 'cnbc.com'
    allowed_domains = ['cnbc.com']
    start_urls = ['https://www.cnbc.com/bitcoin/']
    next_page = 1

    custom_settings = {
        'ITEM_PIPELINES': {
            'bitspider.pipelines.CnbcComPipeline': 300
        },
        'USER_AGENT': 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X '
        '10_12_6) AppleWebKit/604.5.6 (KHTML, like Gecko) '
        'Version/11.0.3 Safari/604.5.6'
    }

    history_urls_path = 'data/cnbc.com/urls.pkl'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if os.path.exists(self.history_urls_path):
            with open(self.history_urls_path, 'rb') as fin:
                self.history_urls = pickle.load(fin)
        else:
            self.history_urls = set()

    def dump(self):
        with open(self.history_urls_path, 'wb') as fout:
            pickle.dump(self.history_urls, fout)

    def parse(self, response):
        for url in response.xpath('//a[@class="Card-title"]/@href').extract():
            if response.urljoin(url) in self.history_urls:
                continue

            yield response.follow(url,
                                  callback=self.parse_content,
                                  priority=100)

        next_link = response.xpath(
            '//a[@class="LoadMoreButton-loadMore"]/@href').extract_first()

        if next_link is None:
            return

        yield response.follow(
            next_link,
            callback=self.parse,
            priority=50)

    def parse_content(self, response):
        logging.info('Downloaded {}'.format(response.url))

        self.history_urls.add(response.url)

        title = response.xpath('//h1/text()').extract_first()
        content = BeautifulSoup('\n'.join(response.xpath(
            '//div[@data-module="ArticleBody"]/*').extract()), 'lxml').get_text()
        birthday = response.xpath(
            '//meta[@property="article:published_time"]/@content'
        ).extract_first()
        if not birthday:
            return
        date = dateparser.parse(birthday).astimezone(gettz('UTC'))

        yield {
            'url': response.url,
            'title': title,
            'content': content,
            'birthday': birthday,
            'date': date,
            'year': date.year,
            'month': date.month,
            'day': date.day
        }
