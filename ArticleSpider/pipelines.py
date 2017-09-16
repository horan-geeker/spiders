# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import codecs
import json
# from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter
import MySQLdb
import MySQLdb.cursors
from twisted.enterprise import adbapi


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


class JsonWithEncodingPipeline(object):
    def __init__(self):
        self.file = codecs.open('article_json.json', 'w', encoding='utf-8')

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False)
        self.file.write(lines)
        return item

    def spider_closed(self, spider):
        self.file.close()


class JsonExporterPipeline(object):
    def __init__(self):
        self.file = open('article_export.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


# class ArticleImagePipeline(ImagesPipeline):
#     def item_completed(self, results, item, info):
#         if "thumb_path" in item:
#             for ok, value in results:
#                 image_path = value["path"]
#             item["thumb_path"] = image_path
#         return item


class MysqlPipeline(object):
    def __init__(self):
        self.db = MySQLdb.connect('127.0.0.1', 'root', 'root', 'spiders', charset="utf8", use_unicode=True)
        self.cursor = self.db.cursor()

    def process_item(self, item, spider):
        sql = """
            insert into jobbole_articles(title, url, fav_num, created_at) VALUES (%s, %s, %s, %s)
        """
        self.cursor.execute(sql, (item["title"], item["url"], item["fav_num"], item["created_at"]))
        self.db.commit()
        return item


class MysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparams = dict(
            host=settings["DB_HOST"],
            db=settings["DB_DATABASE"],
            user=settings["DB_USERNAME"],
            passwd=settings["DB_PASSWORD"],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparams)
        return cls(dbpool)

    def process_item(self, item, spider):
        # 使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.insert, item)
        query.addErrback(self.handle_error, item, spider)  # 处理异常
        return item

    def handle_error(self, failure, item, spider):
        print(failure)

    def insert(self, cursor, item):
        # 执行具体的插入
        # 根据不同的item 构建不同的sql语句并插入到mysql中
        insert_sql, params = item.get_insert_sql()
        print(insert_sql, params)
        cursor.execute(insert_sql, params)


class ElasticPipeline(object):

    def process_item(self, item, spider):
        item.save_es()

        return item