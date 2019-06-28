# -*- coding: utf-8 -*-
import os
import logging
import pickle

import scrapy
import dateutil.parser as dateparser
from dateutil.tz import gettz
from datetime import datetime
from bs4 import BeautifulSoup


if not os.path.exists('./log'):
    os.mkdir('log')

logging.basicConfig(
    filename='log/investing.com.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


class InvestingComSpider(scrapy.Spider):
    name = 'investing.com'
    allowed_domains = ['investing.com']
    start_urls = ['https://www.investing.com/crypto/bitcoin/news/1',
                  'https://www.investing.com/news/cryptocurrency-news',
                  'https://www.investing.com/news/stock-market-news']

    custom_settings = {
        'ITEM_PIPELINES': {
            'bitspider.pipelines.InvestingComPipeline': 300
        },
        'USER_AGENT': 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X '
        '10_12_6) AppleWebKit/604.5.6 (KHTML, like Gecko) '
        'Version/11.0.3 Safari/604.5.6'
    }

    history_urls_path = 'data/investing.com/urls.pkl'

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
        for url in response.xpath('//article/a/@href').extract():
            if url in self.history_urls:
                continue

            yield response.follow(url, self.parse_content, priority=200)

        nxt = response.xpath(
            '//*[@id="paginationWrap"]/div[3]/a/@href').extract_first()

        if nxt is not None:
            yield response.follow(nxt, self.parse, priority=50)

    def parse_content(self, response):
        url = response.url
        self.history_urls.add(url)
        birthday = None
        try:
            birthday = datetime.fromtimestamp(int(
                response.xpath('//time[@class="article--time"]/@datetime'
                               ).extract_first())).astimezone(gettz('UTC'))
        except:
            pass

        if birthday is None:
            birthday = response.xpath(
                '//div[@class="contentSectionDetails"]/span/text()'
            ).extract_first()
            try:
                birthday = dateparser.parse(birthday).astimezone(gettz('UTC'))
            except:
                pass

            if isinstance(birthday, str) and '(' in birthday and ')' in birthday:
                l, r = birthday.find('('), birthday.find(')')
                try:
                    birthday = dateparser.parse(
                        birthday[l + 1:r]).astimezone(gettz('UTC'))
                except:
                    pass

        # if birthday is None:
        if not isinstance(birthday, datetime):
            logging.info('Invalid datetime, url: {}'.format(url))
            return

        date = birthday
        title = response.xpath('//h1/text()').extract_first()
        soup = BeautifulSoup('\n'.join(response.xpath(
            '//*[@id="leftColumn"]/div[@class="WYSIWYG articlePage"]/'
            '*[position() < last()]').extract()), 'lxml')
        for s in soup('script'):
            s.extract()
        content = soup.get_text()

        yield {
            'url': url,
            'title': title,
            'birthday': birthday,
            'date': str(date),
            'content': content,
            'year': date.year,
            'month': date.month,
            'day': date.day
        }
