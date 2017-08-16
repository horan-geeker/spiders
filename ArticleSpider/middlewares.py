# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html
import random
import time

from scrapy import signals
from scrapy.http import HtmlResponse
from PIL import Image
from zheye.zheye import zheye
from selenium import webdriver


# from scrapy.contrib.downloadermiddleware.useragent import UserAgentMiddleware


class ArticlespiderSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class RandomUserAgentMiddleware(object):

    def __init__(self, user_agent=''):
        self.user_agent = user_agent

    def process_request(self, request, spider):
        user_agent_list = [
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
            "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
            "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:21.0) Gecko/20100101 Firefox/21.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
            "Mozilla/5.0 (compatible; WOW64; MSIE 10.0; Windows NT 6.2)",
            "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27"
        ]
        ua = random.choice(user_agent_list)
        if ua:
            request.headers.setdefault('User-Agent', ua)

            # Add desired logging message here.
            # spider.log(
            #     u'User-Agent: {} {}'.format(request.headers.get('User-Agent'), request),
            #     level=log.DEBUG
            # )


class RandomIpProxyMiddleware(object):

    def process_request(self, request, spider):
        request.meta["proxy"] = "http://127.0.0.1:1080"


class JsPageMiddleware(object):

    def process_request(self, request, spider):
        if spider.name=='zhihu':
            spider.browser.get(request.url)
            time.sleep(2)
            if request.url == 'https://www.zhihu.com/#signin':
                time.sleep(1)
                spider.browser.find_element_by_css_selector("span.signin-switch-password:nth-child(1)").click()
                spider.browser.find_element_by_css_selector("input[name='account']").send_keys("13571899655")
                spider.browser.find_element_by_css_selector("input[name='password']").send_keys("hejunwei3269982")
                time.sleep(5)

                captcha_element = spider.browser.find_element_by_css_selector("div.Captcha-imageConatiner img.Captcha-image")
                spider.browser.save_screenshot('zhihu_captcha.png')
                left = captcha_element.location['x'] * 2
                top = captcha_element.location['y'] * 2
                right = captcha_element.location['x'] + captcha_element.size['width']
                bottom = captcha_element.location['y'] + captcha_element.size['height']

                im = Image.open('zhihu_captcha.png')
                im = im.crop((left, top, left+400, top+88))
                im.save('zhihu_captcha.png')

                z = zheye()
                positions = z.Recognize('zhihu_captcha.png')
                action = webdriver.common.action_chains.ActionChains(spider.browser)
                for point in positions:
                    action.move_to_element_with_offset(captcha_element, point[0], point[1])
                    action.click()
                    action.perform()
                spider.browser.find_element_by_css_selector("button.submit").click()
            print("访问：{0}".format(request.url))

            body = spider.browser.page_source

            if '/answers' in request.url:
                body = spider.browser.find_element_by_tag_name("pre").text

            return HtmlResponse(url=spider.browser.current_url, body=body, encoding='utf-8', request=request)