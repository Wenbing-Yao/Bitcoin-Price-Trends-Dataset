# -*- coding: utf-8 -*-
import os
import json
import logging
import pickle
from time import sleep

import scrapy
from scrapy.http import FormRequest
import dateutil.parser as dateparser
from dateutil.tz import gettz
from bs4 import BeautifulSoup

if not os.path.exists('./log'):
    os.mkdir('log')

logging.basicConfig(
    filename='log/coingeek.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


class CoingeekComSpider(scrapy.Spider):
    name = 'coingeek.com'
    allowed_domains = ['coingeek.com']
    start_urls = ['https://coingeek.com/news/category/business/',
                  'https://coingeek.com/news/category/editorial/',
                  'https://coingeek.com/news/category/tech/',
                  'https://coingeek.com/news/category/events/']
    custom_settings = {
        'ITEM_PIPELINES': {
            'bitspider.pipelines.CoingeekComPipeline': 300
        },
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/72.0.3626.109 Safari/537.36'
    }

    history_urls_path = 'data/coingeek.com/urls.pkl'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if os.path.exists(self.history_urls_path):
            with open(self.history_urls_path, 'rb') as fin:
                self.history_urls = pickle.load(fin)
        else:
            self.history_urls = set()

    def parse(self, response):
        article_urls = response.xpath(
            '//div[@class="new"]/a/@href').extract()
        for url in article_urls:
            if url in self.history_urls:
                continue

            yield response.follow(url, self.parse_content, priority=200)

        next_page_url = 'https://coingeek.com/wp-admin/admin-ajax.php'
        max_page = int(response.xpath(
            '//div[@class="load__more--block"]/a/@data-maxpage'
        ).extract_first().replace(',', ''))
        formdata = {
            "action": "get_news_by_taxonomy",
            'max-page': str(max_page),
            'tax': response.xpath('//div[@class="load__more--block"]/a/@data-tax'
                                  ).extract_first(),
            'cat': response.xpath(
                '//div[@class="load__more--block"]/a/@data-category'
            ).extract_first()
        }

        for cur_page in range(2, max_page + 1):
            formdata['page'] = str(cur_page)
            logging.info('Request page: {}, cat: {}'.format(
                cur_page, formdata['cat']))

            yield FormRequest(url=next_page_url,
                              formdata=formdata,
                              callback=self.parse_ajax_page,
                              priority=200,
                              headers={
                                  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                                  'Accept-Language': 'en',
                                  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36',
                                  'Accept-Encoding': 'gzip,deflate',
                                  'Cookie': '__cfduid=ddffe8ac1f254f6773679656b06d805541557128636'})
            # sleep(0.3)

    def parse_ajax_page(self, response):
        article_urls = response.xpath('//a/@href').extract()
        logging.info('Downloaded {}'.format(response.url))

        for url in article_urls:
            if url in self.history_urls:
                continue

            yield response.follow(url, self.parse_content, priority=200)
            # sleep(0.1)

    def parse_content(self, response):
        url = response.url
        self.history_urls.add(url)
        logging.info('Downloaded {}'.format(response.url))

        if response.text == "":
            return

        birthday = response.xpath('//meta[@property="article:published_time"]'
                                  '/@content').extract_first()
        title = response.xpath('//title/text()').extract_first()
        date = dateparser.parse(birthday).astimezone(gettz('UTC'))
        soup = BeautifulSoup(response.xpath('//div[@class="new__container"]'
                                            '/div[@class="content"]'
                                            ).extract_first(), 'lxml')
        for s in soup('script'):
            s.extract()

        content = soup.get_text()
        if not content:
            return

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

    def dump(self):
        with open(self.history_urls_path, 'wb') as fout:
            pickle.dump(self.history_urls, fout)
