# -*- coding: utf-8 -*-
import os
# import sys
import scrapy
import pickle
import logging
from datetime import datetime

import dateutil.parser as dateparser
from dateutil.tz import gettz
from bs4 import BeautifulSoup
# from scrapy import Selector

if not os.path.exists('./log'):
    os.mkdir('log')

logging.basicConfig(
    filename='log/bitcoinmagazine.com.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


class BitcoinmagazineComSpider(scrapy.Spider):
    name = 'bitcoinmagazine.com'
    allowed_domains = ['bitcoinmagazine.com']
    start_urls = ['https://bitcoinmagazine.com/articles/1']
    pre_date = datetime.now()
    pre_date_str = str(pre_date)
    custom_settings = {
        'ITEM_PIPELINES': {
            'bitspider.pipelines.BitcoinMagazineComPipeline': 300
        }
    }

    history_urls_path = 'data/bitcoinmagazine.com/urls.pkl'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if os.path.exists(self.history_urls_path):
            with open(self.history_urls_path, 'rb') as fin:
                self.history_urls = pickle.load(fin)
        else:
            self.history_urls = set()

    def parse(self, response):
        urls = [response.urljoin(url) for url in response.xpath(
            '//div[@class="bm-card category-list--card"]/div[@class="row"]'
            '/div[@class="col-lg-11"]/a/@href').extract()]

        for url in urls:

            if url in self.history_urls:
                continue

            yield response.follow(url, self.parse_content, priority=200)

        next_page = response.xpath(
            '//ul[@class="pagination justify-content-left btn-group"]/'
            'li[last()]/a/@href').extract_first()

        if not next_page:
            return

        yield response.follow(response.urljoin(next_page),
                              self.parse, priority=100)

    def parse_content(self, response):
        logging.info(response.url)
        self.history_urls.add(response.url)
        pt = response.xpath('//*[@id="authorSidebar"]/div/time')
        birthday = pt.xpath('text()').extract_first()
        if birthday is not None:
            birthday += pt.xpath('span/text()').extract_first()

        title = response.xpath('//h1/text()').extract_first()

        content = BeautifulSoup('\n'.join(response.xpath(
            '//div[@class="rich-text"]/*').extract()), 'lxml').get_text()

        if birthday is None:
            return

        date = dateparser.parse(birthday, fuzzy_with_tokens=True, tzinfos={
            'EST': gettz('EST')})[0].astimezone(gettz('UTC'))

        self.pre_date = date

        yield {
            'title': title,
            'url': response.url,
            'birthday': birthday,
            'date': date,
            'content': content,
            'year': date.year,
            'month': date.month,
            'day': date.day
        }

    def dump(self):
        with open(self.history_urls_path, 'wb') as fout:
            pickle.dump(self.history_urls, fout)
