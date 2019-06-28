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
    filename='log/cryptodaily.co.uk.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


class CryptodailyCoUkSpider(scrapy.Spider):
    name = 'cryptodaily.co.uk'
    allowed_domains = ['cryptodaily.co.uk']
    start_urls = ['https://cryptodaily.co.uk/category/breaking-news/',
                  'https://cryptodaily.co.uk/category/bitcoins/',
                  'https://cryptodaily.co.uk/category/ethereum/']
    custom_settings = {
        'ITEM_PIPELINES': {
            'bitspider.pipelines.CryptodailyCoUkPipeline': 300
        },
    }

    history_urls_path = 'data/cryptodaily.co.uk/urls.pkl'

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
        for url in response.xpath(
                '//div[@class="position-relative mb-50-r"]/a[last()]/@href'
        ).extract():

            if url in self.history_urls:
                return

            yield response.follow(url,
                                  callback=self.parse_content,
                                  priority=100)

        next_page_url = response.xpath('//a[@rel="next"]/@href'
                                       ).extract_first()

        if not next_page_url:
            return

        yield response.follow(next_page_url,
                              callback=self.parse)

    def parse_content(self, response):

        self.history_urls.add(response.url)
        logging.info('Downloaded: {}'.format(response.url))

        title = ' '.join(response.xpath('//h2/text()'
                                        ).extract_first().split())
        soup = BeautifulSoup(response.xpath(
            '//div[@class="news-content news-post-main-content"]'
        ).extract_first(), 'lxml')
        for s in soup('script'):
            s.extract()
        content = soup.get_text().strip()
        soup = BeautifulSoup(response.xpath(
            '//ul[@class="post-info-dark mb-30"]/li[2]/a').extract_first())
        birthday = soup.get_text().strip()
        date = dateparser.parse(birthday).astimezone(gettz('UTC'))

        yield {
            'title': title,
            'url': response.url,
            'birthday': birthday,
            'date': date,
            'year': date.year,
            'month': date.month,
            'day': date.day,
            'content': content
        }
