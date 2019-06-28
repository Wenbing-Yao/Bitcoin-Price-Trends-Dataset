# -*- coding: utf-8 -*-
import os
import scrapy
import pickle
import logging

import dateutil.parser as dateparser
from dateutil.tz import gettz
from bs4 import BeautifulSoup
# from scrapy import Selector

if not os.path.exists('./log'):
    os.mkdir('log')

logging.basicConfig(
    filename='log/news.bitcoin.com.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


class NewsBitcoinComSpider(scrapy.Spider):
    name = 'news.bitcoin.com'
    allowed_domains = ['news.bitcoin.com']
    start_urls = ['https://news.bitcoin.com/page/2/']
    curr_page = 2
    custom_settings = {
        'ITEM_PIPELINES': {
            'bitspider.pipelines.BitcoinComPipeline': 300
        }
    }

    history_urls_path = 'data/bitcoin.com/urls.pkl'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if os.path.exists(self.history_urls_path):
            with open(self.history_urls_path, 'rb') as fin:
                self.history_urls = pickle.load(fin)
        else:
            self.history_urls = set()

    def parse(self, response):
        urls = response.xpath('//div[@class="story story--medium"]/a/@href'
                              ).extract()

        for url in urls:
            if url in self.history_urls:
                continue

            yield response.follow(url, callback=self.parse_content,
                                  priority=100)

        last_page = int(response.xpath(
            '//a[@class="last"]/text()').extract_first().replace(',', ''))

        if self.curr_page <= last_page:
            self.curr_page += 1
            yield response.follow('https://news.bitcoin.com/page/{}/'.format(
                self.curr_page), self.parse, priority=50)

    def parse_content(self, response):
        url = response.url
        self.history_urls.add(url)
        logging.info('Downloaded article: {}'.format(url))

        title = response.xpath('//main/article/header/h1/text()'
                               ).extract_first().strip()
        soup = BeautifulSoup(response.xpath(
            '//article').extract_first(), 'lxml')
        for s in soup('script'):
            s.extract()
        content = soup.get_text()

        birthday = response.xpath(
            '//meta[@property="article:published_time"]/@content'
        ).extract_first()

        if not birthday:
            return

        dt = dateparser.parse(birthday).astimezone(gettz('UTC'))

        yield {
            'url': url,
            'title': title,
            'content': content,
            'birthday': birthday,
            'date': dt,
            'year': dt.year,
            'month': dt.month,
            'day': dt.day
        }

    def dump(self):

        with open(self.history_urls_path, 'wb') as fout:
            pickle.dump(self.history_urls, fout)
