# -*- coding: utf-8 -*-
import os
import pickle
import scrapy
import dateutil.parser as dateparser
from bs4 import BeautifulSoup


class ThemerkleComSpider(scrapy.Spider):
    name = 'themerkle.com'
    allowed_domains = ['themerkle.com']
    start_urls = ['https://themerkle.com/page/1/?s=Bitcoin']
    custom_settings = {
        'ITEM_PIPELINES': {
            'bitspider.pipelines.ThemerkleComPipeline': 300
        }
    }

    history_urls_path = 'data/themerkle.com/urls.pkl'
    c = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if os.path.exists(self.history_urls_path):
            with open(self.history_urls_path, 'rb') as fin:
                self.history_urls = pickle.load(fin)
        else:
            self.history_urls = set()

    def parse(self, response):
        urls = response.xpath('//*[@id="content_box"]/article/header/h2/a/'
                              '@href').extract()
        next_url = response.xpath(
            '//*[@id="content_box"]/nav/div/a[@class="next page-numbers"]/'
            '@href').extract_first()

        for url in urls:
            if url in self.history_urls:
                continue

            yield response.follow(url, callback=self.parse_content,
                                  priority=100)

        if next_url is not None:
            yield response.follow(next_url, self.parse, priority=50)

    def parse_content(self, response):
        url = response.url
        self.history_urls.add(url)
        article_created = response.xpath(
            '//meta[@property="article:published_time"]/@content'
        ).extract_first()
        date = dateparser.parse(article_created)
        title = response.xpath('//*[@id="content_box"]/div/div[2]/header/h1/'
                               'text()').extract_first()
        author = response.xpath('//header/div[1]/span[1]/span/a/text()'
                                ).extract_first()

        content = ' '.join(
            BeautifulSoup(
                ' '.join(response.xpath('//div[@class="thecontent"]/p'
                                        ).extract()[:-1]), 'lxml'
            ).get_text().split())

        year, month, day = date.year, date.month, date.day

        yield {
            'url': url,
            'author': author,
            'title': title,
            'content': content,
            'date': article_created,
            'year': year,
            'month': month,
            'day': day
        }

    def dump(self):
        with open(self.history_urls_path, 'wb') as fout:
            pickle.dump(self.history_urls, fout)
