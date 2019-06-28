# -*- coding: utf-8 -*-
import os
import json
import pickle
import logging

import scrapy
from scrapy.http import FormRequest
import dateutil.parser as dateparser
from dateutil.tz import gettz
from bs4 import BeautifulSoup
# from scrapy.spiders import CrawlSpider, Rule
# from scrapy.linkextractors import LinkExtractor


if not os.path.exists('./log'):
    os.mkdir('log')

logging.basicConfig(
    filename='log/cointelegraph.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


class CointelegraphSpider(scrapy.Spider):
    name = 'cointelegraph'
    allowed_domains = ['cointelegraph.com']
    start_urls = ['https://cointelegraph.com']

    custom_settings = {
        'ITEM_PIPELINES': {
            'bitspider.pipelines.CointelegraphComPipeline': 300
        },
        'USER_AGENT': 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X '
        '10_12_6) AppleWebKit/604.5.6 (KHTML, like Gecko) '
        'Version/11.0.3 Safari/604.5.6'
    }

    history_urls_path = 'data/cointelegraph.com/urls.pkl'

    next_page_info = {}

    invalid_counter = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if os.path.exists(self.history_urls_path):
            with open(self.history_urls_path, 'rb') as fin:
                self.history_urls = pickle.load(fin)
        else:
            self.history_urls = set()

        self.next_page = 1

    def dump(self):
        with open(self.history_urls_path, 'wb') as fout:
            pickle.dump(self.history_urls, fout)

    def parse(self, response):
        if response.status != 200:
            return

        for url in response.xpath(
            '//ul[@class="post-preview-list-cards"]//article/header/a/@href'
        ).extract():
            if url in self.history_urls:
                continue

            yield response.follow(
                url,
                callback=self.parse_content_page,
                priority=100)

        token = response.xpath(
            '//meta[@name="csrf-token"]/@content').extract_first()
        self.next_page += 1
        self.formdata = {
            "page": str(self.next_page),
            "lang": 'en',
            "_token": token
        }

        yield FormRequest(
            url='https://cointelegraph.com/api/v1/content/json/_mp',
            formdata=self.formdata,
            callback=self.parse_form_data,
            priority=50)

    def parse_form_data(self, response):
        if response.status != 200:
            return

        logging.info('Downloaded form: {}'.format(response.url))

        try:
            data = json.loads(response.text)
            urls = [d['url'] for d in data['posts']]
        except Exception:
            return

        if len(urls) == 0:
            return

        for url in urls:
            if url in self.history_urls:
                continue

            yield response.follow(
                url,
                callback=self.parse_content_page,
                priority=100)

        self.next_page += 1
        self.formdata["page"] = str(self.next_page)
        yield FormRequest(
            url='https://cointelegraph.com/api/v1/content/json/_mp',
            formdata=self.formdata,
            callback=self.parse_form_data,
            priority=50)

    def parse_content_page(self, response):
        self.history_urls.add(response.url)
        url = response.url
        logging.info('Downloaded article: {}'.format(url))

        birthday = response.xpath(
            '//meta[@property="article:published_time"]/@content'
        ).extract_first()
        date = dateparser.parse(birthday).astimezone(gettz('UTC'))

        title = response.xpath('//h1/text()').extract_first()
        content = BeautifulSoup('\n'.join(response.xpath(
            '//div[@itemprop="articleBody"]/*[position() < last() - 7]'
        ).extract()), 'lxml').get_text()

        yield {
            'url': url,
            'title': title,
            'content': content,
            'birthday': birthday,
            'date': date,
            'year': date.year,
            'month': date.month,
            'day': date.day
        }
