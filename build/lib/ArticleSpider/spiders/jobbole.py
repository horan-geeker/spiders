# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy import Request
from urllib import parse
from ArticleSpider.items import JobboleArticleItem
from ArticleSpider.items import ArticleItemLoader
from ArticleSpider.utils.common import md5
from ArticleSpider.items import ArticleItemLoader
from selenium import webdriver
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals

class JobboleSpider(scrapy.Spider):
    name = "jobbole"
    allowed_domains = ["blog.jobbole.com",'majialichen.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']
    # start_urls = ['https://www.majialichen.com']

    def __init__(self, **kwargs):
        self.browser = webdriver.Chrome(executable_path="C:/opt/selenium/chromedriver.exe")
        super().__init__()
        #触发关闭信号时回调函数进行处理
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        print("close browser")
        self.browser.quit()

    def parse(self, response):
        url_list = response.css('#archive .post-thumb a')
        for url in url_list:
            img = url.css('img::attr(src)').extract_first()
            a_href = url.css('::attr(href)').extract_first()
            yield Request(url=parse.urljoin(response.url, a_href), callback=self.parse_post,
                          meta={"post_thumb": parse.urljoin(response.url, img)})

        next_url = response.css('.next.page-numbers::attr(href)').extract_first()
        if next_url:
            yield Request(url=next_url, callback=self.parse)
        pass

    """
    解析单篇文章
    """

    def parse_post(self, response):
        # article_item = JobboleArticleItem()
        #
        # title = response.css('.entry-header h1::text').extract_first()
        # created_at = response.css('.entry-meta .entry-meta-hide-on-mobile::text').extract_first().replace('·',
        #                                                                                                   '').strip()
        # like_num = int(response.css('h10::text').extract_first() or 0)
        # fav_num = 0
        #
        # favorites = response.css(
        #     'span.btn-bluet-bigger.href-style.bookmark-btn.register-user-only::text').extract_first()
        # match_fav = re.match(r".*?(\d+).*", favorites)
        # if match_fav:
        #     fav_num = int(match_fav.group(1))
        # comments_num = 0
        # comments = response.css('span.btn-bluet-bigger.href-style.hide-on-480::text').extract_first()
        # match_comments = re.match(r".*?(\d+).*", comments)
        # if match_comments:
        #     comments_num = int(match_comments.group(1) or 0)
        #
        # content = response.css('.entry').extract_first()
        #
        # tags = response.css('p.entry-meta-hide-on-mobile a::text').extract()
        # keys = [key for key in tags if not key.strip().endswith("评论")]
        # post_thumb = response.meta.get("post_thumb", "")
        #
        # article_item["url"] = response.url
        # article_item["url_hash"] = md5(response.url)
        # article_item["title"] = title
        # article_item["content"] = content
        # article_item["created_at"] = created_at
        # article_item["post_thumb"] = [post_thumb]
        # article_item["tags"] = keys
        # article_item["fav_num"] = fav_num
        # article_item["comments_num"] = comments_num
        # article_item["like_num"] = like_num

        # 通过itemloader
        item_loader = ArticleItemLoader(item=JobboleArticleItem(), response=response)
        match_object = re.match(".*/(\d+)",response.url)
        id = match_object.group(1)
        item_loader.add_value("id",id)
        item_loader.add_css("title", ".entry-header h1::text")
        item_loader.add_css("content", ".entry")
        item_loader.add_css("post_at", ".entry-meta .entry-meta-hide-on-mobile::text")
        item_loader.add_css("fav_num", "span.btn-bluet-bigger.href-style.bookmark-btn.register-user-only::text")
        item_loader.add_css("like_num", "h10::text")
        item_loader.add_css("comments_num", "span.btn-bluet-bigger.href-style.hide-on-480::text")
        item_loader.add_css("tags", "p.entry-meta-hide-on-mobile a::text")
        # item_loader.add_xpath()
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_hash", md5(response.url))
        item_loader.add_value("post_thumb", [response.meta.get("post_thumb", "")])

        item_loader.add_value("like_num","0")

        article_item = item_loader.load_item()
        yield article_item
