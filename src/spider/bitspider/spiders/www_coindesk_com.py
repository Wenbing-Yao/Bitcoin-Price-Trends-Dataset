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
    filename='log/www.coindesk.com.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


class WwwCoindeskComSpider(scrapy.Spider):
    name = 'www.coindesk.com'
    allowed_domains = ['www.coindesk.com']
    start_urls = ['https://www.coindesk.com/']
    cur_page = 1
    _404_times = 0
    custom_settings = {
        'ITEM_PIPELINES': {
            'bitspider.pipelines.CoindeskComPipeline': 300
        }
    }

    history_urls_path = 'data/coindesk.com/urls.pkl'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if os.path.exists(self.history_urls_path):
            with open(self.history_urls_path, 'rb') as fin:
                self.history_urls = pickle.load(fin)
        else:
            self.history_urls = set()

    def parse(self, response):
        if response.status == 404:
            return

        artset = response.xpath('//div[@class="article-set"]')
        urls = artset.xpath('//a[@class="stream-article"]/@href').extract()

        for url in urls:
            if url in self.history_urls:
                continue

            yield response.follow(url, callback=self.parse_content,
                                  priority=100)

        if self.cur_page is None:
            return

        self.cur_page += 1

        yield response.follow(
            '{}page/{}/'.format(self.start_urls[0], self.cur_page),
            method='POST',
            callback=self.parse,
            priority=50)

    def parse_content(self, response):
        if response.status != 200 or len(response.text) <= 1:
            self.cur_page = None
        logging.info('Downloaded {}'.format(response.url))
        self.history_urls.add(response.url)
        soup = BeautifulSoup(response.xpath(
            '//section[@class="article-content"]').extract_first(), 'lxml')

        for s in soup('script'):
            s.extract()

        content = soup.get_text()
        title = response.xpath(
            '//meta[@property="og:title"]/@content').extract_first()

        birthday = response.xpath(
            '//meta[@property="article:published_time"]/@content'
        ).extract_first()
        if not birthday:
            logging.warning('No birthday: {}'.format(title))
            return
        date = dateparser.parse(birthday).astimezone(gettz('UTC'))

        yield {
            'url': response.url,
            'title': title,
            'birthday': birthday,
            'date': date,
            'year': date.year,
            'month': date.month,
            'day': date.day,
            'content': content
        }

    def dump(self):

        with open(self.history_urls_path, 'wb') as fout:
            pickle.dump(self.history_urls, fout)
