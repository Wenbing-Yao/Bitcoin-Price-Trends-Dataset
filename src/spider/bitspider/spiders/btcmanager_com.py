# -*- coding: utf-8 -*-
import os
import json
import logging
import pickle

import scrapy
import dateutil.parser as dateparser
from scrapy.http import FormRequest
from dateutil.tz import gettz
from bs4 import BeautifulSoup

if not os.path.exists('./log'):
    os.mkdir('log')

logging.basicConfig(
    filename='log/btcmanager.com.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


class BtcmanagerComSpider(scrapy.Spider):
    name = 'btcmanager.com'
    allowed_domains = ['btcmanager.com']
    start_urls = ['https://btcmanager.com/news/bitcoin/']

    custom_settings = {
        'ITEM_PIPELINES': {
            'bitspider.pipelines.BtcManagerComPipeline': 300
        },
    }

    history_urls_path = 'data/btcmanager.com/urls.pkl'

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
        for url in response.xpath('//div[@class="article_list"]/section/'
                                  'h2/a/@href').extract():
            if url in self.history_urls:
                continue

            yield response.follow(url, self.parse_content, priority=200)

        self.next_page = 1
        self.formdata = {
            "action": "alm_query_posts",
            "nonce": "db1ee3e2a1",
            "query_type": "standard",
            "post_id": "0",
            "slug": "home",
            "canonical_url": "https://btcmanager.com/",
            "cache_logged_in": "false",
            "repeater": "default",
            "theme_repeater": "null",
            "acf": "",
            "nextpage": "",
            "cta": "",
            "comments": "",
            "users": "",
            "post_type[]": "post",
            "sticky_posts": "",
            "post_format": "",
            "category": "News",
            "category__not_in": "",
            "tag": "",
            "tag__not_in": "",
            "taxonomy": "",
            "taxonomy_terms": "",
            "taxonomy_operator": "",
            "taxonomy_relation": "",
            "meta_key": "_featured-post",
            "meta_value": "1",
            "meta_compare": "NOT IN",
            "meta_relation": "",
            "meta_type": "",
            "author": "",
            "year": "",
            "month": "",
            "day": "",
            "post_status": "",
            "order": "DESC",
            "orderby": "date",
            "post__in": "",
            "post__not_in": "",
            "exclude": "",
            "search": "",
            "custom_args": "",
            "posts_per_page": "10",
            "page": "1",
            "offset": "10",
            "preloaded": "false",
            "seo_start_page": "1",
            "paging": "false",
            "previous_post": "",
            "lang": "",
        }

        self.next_page_url = 'https://btcmanager.com/wp-admin/admin-ajax.php'

        yield FormRequest(url=self.next_page_url,
                          formdata=self.formdata,
                          callback=self.parse_ajax_page,
                          priority=5)

    def parse_ajax_page(self, response):
        logging.info('Handlering: {}'.format(response.url))
        if response.status != 200 or not response.text:
            return

        html = json.loads(response.text)['html']
        soup = BeautifulSoup(html, 'lxml')
        for url in [h2.a.get('href') for h2 in
                    soup.select('div[class="h2"]')]:
            if url in self.history_urls:
                continue

            yield response.follow(url, self.parse_content, priority=200)

        self.next_page += 1
        self.formdata['page'] = str(self.next_page)
        self.next_page_url = 'https://btcmanager.com/wp-admin/admin-ajax.php'

        yield FormRequest(url=self.next_page_url,
                          formdata=self.formdata,
                          callback=self.parse_ajax_page,
                          priority=5)

    def parse_content(self, response):
        self.history_urls.add(response.url)
        logging.info('Downloaded: {}'.format(response.url))

        birthday = response.xpath(
            '//meta[@property="article:published_time"]/@content'
        ).extract_first()
        title = response.xpath('//h1/a/text()').extract_first()
        date = dateparser.parse(birthday).astimezone(gettz('UTC'))
        content = BeautifulSoup(''.join(response.xpath(
            '//article//div[@itemprop="articleBody"]/*[name()!="div"]'
        ).extract()), 'lxml').get_text()

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
