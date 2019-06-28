# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import os
from scrapy.exporters import JsonLinesItemExporter


class CommonPipeline(object):

    def __init__(self, data_dir, need_dump=False):
        self.database_dir = data_dir
        self.need_dump = need_dump

    def open_spider(self, spider):
        self.year_exporters = {}
        if not os.path.exists('data'):
            os.mkdir('data')

        if not os.path.exists(self.database_dir):
            os.mkdir(self.database_dir)

    def close_spider(self, spider):
        for exporter in self.year_exporters.values():
            exporter.finish_exporting()
            exporter.file.close()

        if self.need_dump:
            spider.dump()

    def _get_exporter(self, item):
        year = item['year']
        if year not in self.year_exporters:
            f = open(
                os.path.join(self.database_dir,
                             '{}.json'.format(year)), 'ab')
            exporter = JsonLinesItemExporter(f)
            exporter.start_exporting()
            self.year_exporters[year] = exporter

        return self.year_exporters[year]

    def process_item(self, item, spider):
        self._get_exporter(item).export_item(item)

        return item


class CryptodailyCoUkPipeline(CommonPipeline):

    def __init__(self):
        super().__init__('./data/cryptodaily.co.uk', need_dump=True)


class CnbcComPipeline(CommonPipeline):

    def __init__(self):
        super().__init__('./data/cnbc.com', need_dump=True)


class BtcManagerComPipeline(CommonPipeline):

    def __init__(self):
        super().__init__('./data/btcmanager.com', need_dump=True)


class InvestingComPipeline(CommonPipeline):

    def __init__(self):
        super().__init__('./data/investing.com', need_dump=True)


class CoingeekComPipeline(CommonPipeline):

    def __init__(self):
        super().__init__('./data/coingeek.com', need_dump=True)


class BitcoinistComPipeline(CommonPipeline):

    def __init__(self):
        super().__init__('./data/bitcoinist.com', need_dump=True)


class CcnComPipeline(CommonPipeline):

    def __init__(self):
        super().__init__('./data/ccn.com', need_dump=True)


class CointelegraphComPipeline(CommonPipeline):

    def __init__(self):
        super().__init__('./data/cointelegraph.com', need_dump=True)


class BitcoinComPipeline(CommonPipeline):

    def __init__(self):
        super().__init__('./data/bitcoin.com', need_dump=True)


class CoindeskComPipeline(CommonPipeline):

    def __init__(self):
        super().__init__('./data/coindesk.com', need_dump=True)


class Bitcoin86ComPipeline(CommonPipeline):

    def __init__(self):
        super().__init__('./data/bitcoin86.com', need_dump=True)


class BitcoinMagazineComPipeline(CommonPipeline):

    def __init__(self):
        super().__init__('./data/bitcoinmagazine.com', need_dump=True)


class ThemerkleComPipeline(CommonPipeline):

    def __init__(self):
        super().__init__('./data/themerkle.com', need_dump=True)


class Www8btcComPipeline(CommonPipeline):

    def __init__(self):
        super().__init__('./data/8btc.com')


class HuobiComPipeline(CommonPipeline):

    def __init__(self):
        super().__init__('./data/huobi.com', need_dump=True)


class WanbizuComPipeline(CommonPipeline):

    def __init__(self):
        super().__init__('./data/wanbizu.com')

