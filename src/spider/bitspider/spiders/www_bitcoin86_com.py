# -*- coding: utf-8 -*-
import os
# import sys
import re
# import json
# import time
import logging
import pickle
# from datetime import datetime, timedelta

import scrapy
# from scrapy import Selector
# from scrapy.http import FormRequest
# from scrapy.spiders import CrawlSpider, Rule
# from scrapy.linkextractors import LinkExtractor

from bs4 import BeautifulSoup


if not os.path.exists('./log'):
    os.mkdir('log')

logging.basicConfig(
    filename='log/bitcoin86.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


class WwwBitcoin86ComSpider(scrapy.Spider):
    name = 'www.bitcoin86.com'
    allowed_domains = ['www.bitcoin86.com']
    start_urls = ['http://www.bitcoin86.com/news/list_1_1.html']
    description = {}
    custom_settings = {
        'ITEM_PIPELINES': {
            'bitspider.pipelines.Bitcoin86ComPipeline': 300
        }
    }

    def parse(self, response):
        articles = response.xpath('/html/body/section/div/div/article')
        titles = articles.xpath('header/h2/a/b/font/text()|'
                                'header/h2/a/b/text()|'
                                'header/h2/a/text()').extract()
        urls = [response.urljoin(url) for url in articles.xpath(
            'header/h2/a/@href').extract()]
        dates = articles.xpath(
            'p[1]/time/font/text()|p[1]/time/text()').extract()
        views = [int(re.search('阅读\((?P<view>\d*)\)', view).group('view'))
                 for view in articles.xpath('p[1]/span[1]/text()').extract()]

        for title, url, date, view in zip(titles, urls, dates, views):
            self.description[url] = {
                'title': title,
                'date': date,
                'view': view
            }

        for url in urls:
            yield response.follow(url, callback=self.parse_content)

        max_page = int(response.xpath(
            '/html/body/section/div/div/div/ul/'
            'li[last()]/span/strong[1]/text()').extract_first())
        cur_page = int(response.xpath(
            '/html/body/section/div/div/div/ul/'
            'li[@class="thisclass"]/text()').extract_first())

        if cur_page >= max_page:
            return

        next_url = response.url.replace(
            'list_1_' + str(cur_page), 'list_1_' + str(cur_page + 1))
        yield response.follow(next_url, callback=self.parse)

    def parse_content(self, response):
        soup = BeautifulSoup(response.xpath(
            '/html/body/section/div/div/article').extract_first(), 'lxml')
        content = ' '.join(soup.get_text().split())
        desc = self.description[response.url]

        year, month, day = [int(i) for i in desc['date'].split('-')]

        yield {
            'title': desc['title'],
            'date': desc['date'],
            'view': desc['view'],
            'url': response.url,
            'content': content,
            'year': year,
            'month': month,
            'day': day
        }

    def dump(self):
        with open('data/bitcoin86.com/description.pkl', 'wb') as fout:
            pickle.dump(self.description, fout)
