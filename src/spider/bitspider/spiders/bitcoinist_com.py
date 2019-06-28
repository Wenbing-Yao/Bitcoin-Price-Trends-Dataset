# -*- coding: utf-8 -*-
import os
import pickle

import scrapy
from dateutil.tz import gettz
import dateutil.parser as dateparser
from bs4 import BeautifulSoup


class BitcoinistComSpider(scrapy.Spider):
    name = 'bitcoinist.com'
    allowed_domains = ['bitcoinist.com']
    start_urls = ['https://bitcoinist.com/category/news/page/{}/'.format(i)
                  for i in range(1, 292)]       # 220
    custom_settings = {
        'ITEM_PIPELINES': {
            'bitspider.pipelines.BitcoinistComPipeline': 300
        }
    }

    history_urls_path = 'data/bitcoinist.com/urls.pkl'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if os.path.exists(self.history_urls_path):
            with open(self.history_urls_path, 'rb') as fin:
                self.history_urls = pickle.load(fin)
        else:
            self.history_urls = set()

    def parse(self, response):
        article_urls = response.xpath('//h3/a/@href').extract()

        for url in article_urls:
            if url in self.history_urls:
                continue

            yield response.follow(url, self.parse_content, priority=200)

    def parse_content(self, response):
        self.history_urls.add(response.url)

        url = response.url
        title = response.xpath('//*[@id="content"]//h2/text()'
                               ).extract_first()
        birthday = response.xpath(
            '/html/head/meta[@property="article:published_time"]/'
            '@content').extract_first()
        date = dateparser.parse(birthday).astimezone(gettz('UTC'))
        art = BeautifulSoup('\n'.join(response.xpath(
            '//div[@class="article-content"]').extract()))
        content = ' '.join(art.get_text().split())

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
