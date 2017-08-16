# -*- coding: utf-8 -*-
import scrapy
import re
import json
import os
try:
    from urllib import parse
except:
    import urlparse as parse
from ArticleSpider.items import ZhihuQuestionItem,ArticleItemLoader,ZhihuAnswerItem


class ZhihuSpider(scrapy.Spider):
    # handle_httpstatus_list = [401]
    name = "zhihu"
    allowed_domains = ["www.zhihu.com"]
    start_urls = ['https://www.zhihu.com/']

    answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccollapsed_counts%2Creviewing_comments_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.author.is_blocking%2Cis_blocked%2Cis_followed%2Cvoteup_count%2Cmessage_thread_token%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}"

    # captcha_file = "zhihu_login_captcha.jpg"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36"

    custom_settings = {
        "COOKIES_ENABLED": True,
        'DOWNLOAD_DELAY': 3,
    }

    with open(os.path.join(os.path.dirname(__file__),'cookies.txt')) as f:
        cookies = f.read()
    cookie_dict = {}
    for cookie in cookies.split(';'):
        cookie_list = cookie.split('=')
        cookie_dict[cookie_list[0]] = cookie_list[1]

    headers = {
        'Accept': '*/*',
        "Host": "www.zhihu.com",
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36",
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, cookies=self.cookie_dict)
            # def __init__(self, **kwargs):
    #     self.browser = webdriver.Chrome(executable_path="/opt/chromedriver")
    #     super().__init__()
        #触发关闭信号时回调函数进行处理

    def parse(self, response):
        url_list = response.css("a::attr(href)").extract()
        url_list = [parse.urljoin(response.url, url) for url in url_list]
        url_list = filter(lambda x: True if x.startswith("https") else False, url_list)
        for url in url_list:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
            if match_obj:
                request_url = match_obj.group(1)
                question_id = match_obj.group(2)
                yield scrapy.Request(url=request_url, cookies=self.cookie_dict, meta={"question_id":question_id} ,callback=self.parse_question)
            else:
                # 如果不是question页面则直接进一步跟踪
                if "/logout" not in url:
                    yield scrapy.Request(url, cookies=self.cookie_dict, callback=self.parse)

    def parse_question(self, response):
        item_loader = ArticleItemLoader(item=ZhihuQuestionItem(), response=response)

        if "List-headerText" in response.text:
            #旧版知乎https://www.zhihu.com/question/34544815
            item_loader.add_css("answer_num",".List-headerText span::text")
        else:
            item_loader.add_css("answer_num",
                                "#root > div > main > div > div.Question-main > div.Question-mainColumn > div:nth-child(1) > a::text")
        item_loader.add_value("id",response.meta.get("question_id"))
        item_loader.add_value("url",response.url)
        item_loader.add_css("topics",".QuestionTopic .Popover div::text")
        item_loader.add_css("title","h1.QuestionHeader-title::text")
        item_loader.add_css("content",".QuestionHeader-detail span.RichText::text")
        item_loader.add_value("content","")
        item_loader.add_css("comments_num",".QuestionHeader-Comment .Button--plain::text")
        item_loader.add_css("follow_and_watch",".NumberBoard-value::text")

        question_item = item_loader.load_item()

        # 不想花太多时间 debug cookie和header设置的不正确，所以现在就每次都打开文件看看吧
        cookies = {}
        with open(os.path.join(os.path.dirname(__file__),'cookies.txt')) as f:
            raw_cookies = f.read()
        for line in raw_cookies.split(';'):
            key, value = line.split('=', 1)
            cookies[key] = value

        # json_response = requests.get(self.answer_url.format(response.meta.get("question_id"), 20, 0), cookies=cookies, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36'})
        yield scrapy.Request(self.answer_url.format(response.meta.get("question_id"), 20, 0), headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36'}, cookies=cookies,callback=self.parse_answer)

        yield question_item

    def parse_answer(self, response):
        # 处理question的answer
        ans_json = json.loads(response.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        # 提取answer的具体字段
        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["vote_up_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["created_time"] = answer["created_time"]
            answer_item["updated_time"] = answer["updated_time"]

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, cookies=self.cookie_dict, callback=self.parse_answer)

    # def start_requests(self):
    #     return [scrapy.Request('https://www.zhihu.com/#signin', headers=self.header, callback=self.login)]

    # def login(self, response):
    #     # with open(self.captcha_file, "wb") as f:
    #     #     f.write(response.body)
    #         # f.close()
    #
    #     # from PIL import Image
    #     # try:
    #     #     with Image.open("zhihu_login_captcha.jpg") as img:
    #     #         img.show()
    #     # except:
    #     #     pass
    #     # captcha = input("输入验证码\n")
    #
    #     # # 用户名
    #     # username = 'horan'
    #     # # 密码
    #     # password = 'hejunwei3269982'
    #     # # 软件ＩＤ，开发者分成必要参数。登录开发者后台【我的软件】获得！
    #     # appid = 3432
    #     # # 软件密钥，开发者分成必要参数。登录开发者后台【我的软件】获得！
    #     # appkey = '36acb6062bf4a27cc564baa68aa9afc7'
    #     # # 验证码类型，# 例：1004表示4位字母数字，不同类型收费不同。请准确填写，否则影响识别率。在此查询所有类型 http://www.yundama.com/price.html
    #     # codetype = 1004
    #     # # 超时时间，秒
    #     # timeout = 60
    #     # yundama = YDMHttp(username, password, appid, appkey)
    #     # captcha = yundama.decode(self.captcha_file, codetype, timeout)
    #     # if not captcha:
    #     #     print("验证方式不正确")
    #     #     sys.exit(0)
    #     # solve ERR_VERIFY_CAPTCHA_TOO_QUICK
    #     # 将xsrf域放入meta
    #     response_text = response.text
    #     match_obj = re.match('.*name="_xsrf" value="(.*)"', response_text, re.DOTALL)
    #     if match_obj:
    #         xsrf = match_obj.group(1)
    #         post_url = "https://www.zhihu.com/login/phone_num"
    #         post_data = {
    #             "_xsrf": xsrf,
    #             "phone_num": "13571899655",
    #             "password": "hejunwei3269982",
    #             # "captcha": captcha
    #             'capycha_type': 'cn'
    #         }
    #
    #         return [scrapy.FormRequest(
    #             url=post_url,
    #             formdata=post_data,
    #             headers=self.header,
    #             callback=self.check_login,
    #             method='POST'
    #         )]
    #
    # def get_captcha(self, response):
    #     # 将xsrf域放入meta
    #     response_text = response.text
    #     match_obj = re.match('.*name="_xsrf" value="(.*)"', response_text, re.DOTALL)
    #     if match_obj:
    #         xsrf = match_obj.group(1)
    #         # 请求验证码
    #         import time
    #         t = str(int(time.time() * 1000))
    #         captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(t)
    #         yield scrapy.Request(captcha_url, headers=self.header, meta={"xsrf": xsrf}, callback=self.login)
    #     else:
    #         print("not match xsrf")
    #
    # def check_login(self, response):
    #     # 验证服务器的返回数据判断是否成功
    #     if "登录" in response.text and "注册" in response.text:
    #         print("登录失败", response.text)
    #     else:
    #         print("登录成功")
    #         for url in self.start_urls:
    #             yield scrapy.Request(url, dont_filter=True, headers=self.header)
