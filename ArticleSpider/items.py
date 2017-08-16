# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
# from scrapy_djangoitem import DjangoItem
from scrapy.loader.processors import MapCompose, TakeFirst, Join, Identity
from scrapy.loader import ItemLoader
import datetime
import re
from ArticleSpider.settings import SQL_DATETIME_FORMAT
from w3lib.html import remove_tags

from ArticleSpider.models.es import Post,Job,Question,Answer
from elasticsearch_dsl.connections import connections
es = connections.create_connection(hosts=["115.28.82.133"])

# class ArticlespiderItem(scrapy.Item):
#     # define the fields for your item here like:
#     # name = scrapy.Field()
#     pass


def gen_suggest(index, info_tuple):
    used_word = set()
    suggests = []
    for text, weight in info_tuple:
        if text:
            #调用es的analyze接口分析字符串
            words = es.indices.analyze(index=index, analyzer="ik_max_word", params={'filter':['lowercase']}, body=text)
            analyzed_words = set([r['token'] for r in words['tokens'] if len(r['token'])>1])
            new_words = analyzed_words - used_word
        else:
            new_words = set()
        if new_words:
            suggests.append({
                'input':list(new_words),
                'weight':weight
            })
    return suggests

def datetime_convert(value):
    try:
        created_at = datetime.datetime.strptime(value.replace('·', '').strip(), "%Y/%m/%d").date()
    except Exception as e:
        created_at = "0000-00-00 00:00:00"
    return created_at


def get_nums(value):
    match_re = re.match(".*?(\d+).*", value)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0

    return nums


def remove_comment_tags(value):
    # 去掉tag中提取的评论
    if "评论" in value:
        return ""
    else:
        return value


class ArticleItemLoader(ItemLoader):
    default_output_processor = TakeFirst()
    # pass


class JobboleArticleItem(scrapy.Item):
    id = scrapy.Field()
    url = scrapy.Field()
    url_hash = scrapy.Field()
    title = scrapy.Field()
    post_at = scrapy.Field(
        input_processor=MapCompose(datetime_convert),
    )
    like_num = scrapy.Field(
        input_processor=MapCompose(get_nums),
    )
    fav_num = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    comments_num = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    post_thumb = scrapy.Field()
    thumb_path = scrapy.Field()
    content = scrapy.Field()
    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        output_processor=Join(",")
    )

    def get_insert_sql(self):
        insert_sql = """
            insert into jobbole_articles(id, title, url, post_at, fav_num, like_num, comments_num, tags, content) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE fav_num=VALUES(fav_num), like_num=VALUES(like_num), comments_num=VALUES(comments_num)
        """

        thumb_path = ""
        content = self["content"] if 'content' in self else ''

        params = (self["id"], self["title"], self["url"], self["post_at"], self["fav_num"], self["like_num"],
                  self["comments_num"],
                  self["tags"], content)
        return insert_sql, params

    def save_es(self):
        article = Post()
        article.title = self["title"]
        article.content = remove_tags(self["content"])
        article.post_at = self["post_at"]
        article.url = self["url"]
        article.post_thumb = self["post_thumb"]
        article.like_num = self["like_num"]
        article.fav_num = self["fav_num"]
        article.comments_num = self["comments_num"]
        article.tags = self["tags"]
        article.meta.id = self["id"]

        article.suggest = gen_suggest(Post._doc_type.index, ((article.title,10),(article.tags,7)))

        article.save()

        return


class ZhihuQuestionItem(scrapy.Item):
    # 知乎的问题 item
    id = scrapy.Field()
    topics = scrapy.Field(
        output_processor=Join(",")
    )
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    comments_num = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    follow_and_watch = scrapy.Field(
        output_processor=MapCompose()
    )

    # click_num = scrapy.Field()
    # crawl_time = scrapy.Field()

    def get_insert_sql(self):
        sql = "insert into zhihu_questions(id, topics, url, title, content, answer_num, comments_num,follow_user_num, click_num) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE content=VALUES(content), answer_num=VALUES(answer_num), comments_num=VALUES(comments_num),follow_user_num=VALUES(follow_user_num), click_num=VALUES(click_num)"

        follow_user_num = int(self["follow_and_watch"][0])
        click_num = int(self["follow_and_watch"][1])

        content = self["content"] if "content" in self else ""

        answer_num = self["answer_num"] if "answer_num" in self else 0

        params = (
            self["id"], self["topics"], self["url"], self["title"], content, answer_num, self["comments_num"],
            follow_user_num,
            click_num)
        return sql, params

    def save_es(self):
        question = Question()
        question.url = self["url"]
        question.topics = self["topics"]
        question.title = self["title"]
        question.content = self["content"] if 'content' in self else ''
        question.answer_num = self["answer_num"] if "answer_num" in self else 0
        question.comments_num = self["comments_num"]
        question.follow_and_watch = self["follow_and_watch"]

        question.meta.id = self["id"]

        question.save()

        return


class ZhihuAnswerItem(scrapy.Item):
    # 知乎的问题回答item
    id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    vote_up_num = scrapy.Field()
    comments_num = scrapy.Field()
    created_time = scrapy.Field()
    updated_time = scrapy.Field()

    def get_insert_sql(self):
        # 插入知乎question表的sql语句
        insert_sql = """
            insert into zhihu_answers(id, url, question_id, author_id, content, vote_up_num, comments_num,
              created_time, updated_time
              ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
              ON DUPLICATE KEY UPDATE content=VALUES(content), comments_num=VALUES(comments_num), vote_up_num=VALUES(vote_up_num),
              updated_time=VALUES(updated_time)
        """

        created_time = datetime.datetime.fromtimestamp(self["created_time"]).strftime(SQL_DATETIME_FORMAT)
        updated_time = datetime.datetime.fromtimestamp(self["updated_time"]).strftime(SQL_DATETIME_FORMAT)
        params = (
            self["id"], self["url"], self["question_id"],
            self["author_id"], self["content"], self["vote_up_num"],
            self["comments_num"], created_time, updated_time,
        )

        return insert_sql, params

    def save_es(self):
        answer = Answer()
        answer.url = self["url"]
        answer.question_id = self["question_id"]
        answer.author_id = self['author_id']
        answer.content = self["content"]
        answer.vote_up_num = self["vote_up_num"]
        answer.comments_num = self["comments_num"]
        answer.created_time = self["created_time"]
        answer.updated_time = self["updated_time"]

        answer.meta.id = self["id"]

        answer.save()

        return

def replace_splash(value):
    return value.replace("/", "")


def handle_strip(value):
    return value.strip()


def handle_jobaddr(value):
    addr_list = value.split("\n")
    addr_list = [item.strip() for item in addr_list if item.strip() != "查看地图"]
    return "".join(addr_list)


class LagouJob(scrapy.Item):
    id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    salary = scrapy.Field()
    city = scrapy.Field(
        input_processor=MapCompose(replace_splash)
    )
    work_years = scrapy.Field(
        input_processor=MapCompose(replace_splash)
    )
    degree_need = scrapy.Field(
        input_processor=MapCompose(replace_splash)
    )
    job_type = scrapy.Field()
    tags = scrapy.Field(
        output_processor=Join(",")
    )
    publish_time = scrapy.Field()
    job_advantage = scrapy.Field()
    job_desc = scrapy.Field(
        input_processor=MapCompose(handle_strip),
    )
    job_addr = scrapy.Field(
        input_processor=MapCompose(remove_tags, handle_jobaddr),
    )
    company_name = scrapy.Field(
        input_processor=MapCompose(handle_strip),
    )
    company_url = scrapy.Field()

    def save_es(self):
        job = Job()
        job.url = self["url"]
        job.title = self["title"]
        job.salary = remove_tags(self["salary"])
        job.city = self["city"]
        job.work_years = self["work_years"]
        job.degree_need = self["degree_need"]
        job.job_type = self["job_type"]
        job.job_addr = self["job_addr"]
        job.job_advantage = self["job_advantage"]
        job.job_desc = self["job_desc"]
        job.company_url = self["company_url"]
        job.company_name = self["company_name"]
        job.tags = self["tags"]

        job.meta.id = self["id"]

        job.suggest = gen_suggest(Job._doc_type.index, ((job.title,10),(job.tags,7)))

        job.save()

        return

    def get_insert_sql(self):
        insert_sql = """
            insert into lagou_jobs(id, title, url, tags, salary, city, work_years, degree_need,
            job_type, publish_time, job_advantage, job_desc, job_addr, company_url, company_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE job_desc=VALUES(job_desc)
        """

        params = (self["id"], self["title"], self["url"], self["tags"], self["salary"], self["city"], self["work_years"], self["degree_need"],self["job_type"], self["publish_time"], self["job_advantage"], self["job_desc"], self["job_addr"],self["company_url"], self["company_name"])

        return insert_sql, params
