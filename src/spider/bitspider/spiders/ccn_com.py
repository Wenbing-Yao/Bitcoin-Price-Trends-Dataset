# -*- coding: utf-8 -*-
import os
import pickle
import logging
import time

import scrapy
from scrapy.http import FormRequest
from scrapy_splash import SplashRequest, SplashFormRequest
from scrapy_selenium import SeleniumRequest
import dateutil.parser as dateparser
from dateutil.tz import gettz
from bs4 import BeautifulSoup

if not os.path.exists('./log'):
    os.mkdir('log')

logging.basicConfig(
    filename='log/ccn.com.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


class CcnComSpider(scrapy.Spider):
    name = 'ccn.com'
    allowed_domains = ['ccn.com']
    start_urls = ['http://www.ccn.com/']

    custom_settings = {
        'ITEM_PIPELINES': {
            'bitspider.pipelines.CcnComPipeline': 300
        },
    }

    history_urls_path = 'data/ccn.com/urls.pkl'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if os.path.exists(self.history_urls_path):
            with open(self.history_urls_path, 'rb') as fin:
                self.history_urls = pickle.load(fin)
        else:
            self.history_urls = set()

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url=url, callback=self.parse)

    def dump(self):
        with open(self.history_urls_path, 'wb') as fout:
            pickle.dump(self.history_urls, fout)

    def parse(self, response):
        print(response.text)
        articles_urls = response.xpath('//article/header/h2/a/@href').extract()

        for url in articles_urls:
            if url in self.history_urls:
                continue

            # yield response.follow(url, self.parse_content, priority=200)
            yield SeleniumRequest(url, self.parse_content)

        next_page_url = response.xpath('//a[@class="next page-numbers"]/@href'
                                       ).extract_first()

        logging.info('Downloaded page: {}'.format(next_page_url))

        if next_page_url:
            # yield response.follow(next_page_url, self.parse, priority=50)
            yield SeleniumRequest(next_page_url, self.pars)
            # time.sleep(0.5)

    def parse_content(self, response):
        logging.info('Downloaded article: {}'.format(response.url))
        url = response.url
        # print(url)
        if url not in self.history_urls:
            self.history_urls.add(url)

        soup = BeautifulSoup(response.xpath(
            '//div[@class="single_post"]//div[@class="thecontent"]'
        ).extract_first(), 'lxml')

        for s in soup('script'):
            s.extract()

        content = soup.get_text().strip()
        title = response.xpath('//div[@class="single_post"]/header//h1/text()'
                               ).extract_first().strip()
        birthday = response.xpath(
            '//meta[@property="article:published_time"]/@content').extract_first()
        date = dateparser.parse(birthday).astimezone(gettz('UTC'))

        yield {
            'title': title,
            'url': url,
            'birthday': birthday,
            'date': date,
            'year': date.year,
            'month': date.month,
            'day': date.day,
            'content': content
        }
