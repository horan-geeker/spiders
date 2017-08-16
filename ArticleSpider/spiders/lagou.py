# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from ArticleSpider.items import ArticleItemLoader, LagouJob
import re

class LagouSpider(CrawlSpider):
    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['https://www.lagou.com']

    custom_settings = {
        'COOKIES_ENABLED':True,
        'DOWNLOAD_DELAY': 3,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en',
            # 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
        }
    }

    rules = (
        # Rule(LinkExtractor(allow=r'/zhaopin/.*'), follow=True),
        Rule(LinkExtractor(allow=r'/gongsi/j\d+.html'), follow=True),
        Rule(LinkExtractor(allow=r'/jobs/\d+.html'), callback='parse_job', follow=True),
    )

    def parse_job(self, response):
        item_loader = ArticleItemLoader(item=LagouJob(), response=response)
        match_object = re.match(".*/(\d+).html",response.url)
        id = match_object.group(1)
        item_loader.add_value("id",id)
        item_loader.add_value("url",response.url)
        item_loader.add_css("title", ".position-content span.name::text")
        item_loader.add_css("salary", ".job_request .salary::text")
        item_loader.add_css("city", "body > div.position-head > div > div.position-content-l > dd > p:nth-child(1) > span:nth-child(2)::text")
        item_loader.add_css("work_years", "body > div.position-head > div > div.position-content-l > dd > p:nth-child(1) > span:nth-child(3)::text")
        item_loader.add_css("degree_need", "body > div.position-head > div > div.position-content-l > dd > p:nth-child(1) > span:nth-child(4)::text")
        item_loader.add_css("job_type", "body > div.position-head > div > div.position-content-l > dd > p:nth-child(1) > span:nth-child(5)::text")
        item_loader.add_css("tags",".position-label li::text")
        item_loader.add_css("publish_time", ".publish_time::text")
        item_loader.add_css("job_advantage", ".job-advantage p::text")
        item_loader.add_css("job_desc", ".job_bt div")
        item_loader.add_css("job_addr", ".work_addr")

        item_loader.add_css("company_url", "#job_company dt a::attr(href)")
        item_loader.add_css("company_name", "#job_company dt a div h2::text")

        job_item = item_loader.load_item()
        return job_item
