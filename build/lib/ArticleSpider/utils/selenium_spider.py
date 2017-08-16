from selenium import webdriver
from scrapy.selector import Selector
import time

def zhihu_login_test():
    browser = webdriver.Chrome(executable_path='C:/opt/selenium/chromedriver.exe')

    browser.get("https://www.zhihu.com/#signin")
    browser.find_element_by_css_selector("input[name='account']").send_keys('13571899655')
    browser.find_element_by_css_selector("input[name='password']").send_keys('hejunwei3269982')
    time.sleep(4)

    try:
        # browser.find_element_by_css_selector("input[name='captcha']").send_keys('1234')
        browser.find_element_by_css_selector("button.sign-button").click()
        selector = Selector(text=browser.page_source)
        print(browser.page_source)
        # browser.quit()
    except:
        zhihu_login_test()


def oschina_blog_test():
    browser = webdriver.Chrome(executable_path='C:\opt\selenium\chromedriver.exe')
    browser.get("https://www.oschina.net/blog")
    for i in range(3):
        browser.execute_script(
            """
            window.scrollTo(0,document.body.scrollHeight);
            
            """
        )
        time.sleep(2)


def weibo_login_test():
    chrome_opt = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images":2}
    chrome_opt.add_experimental_option("prefs",prefs)
    browser = webdriver.Chrome(executable_path='C:/opt/selenium/chromedriver.exe', chrome_options=chrome_opt)
    browser.get("https://weibo.com/login")


def taobao_detail_test():
    browser = webdriver.PhantomJS(executable_path='C:/opt/phantomjs-2.1.1-windows/bin/phantomjs.exe')
    browser.get("https://detail.tmall.com/item.htm?id=41696362194&spm=a223v.7835278.t0.1.bHk1ax&pvid=716b6051-9fed-45f3-a1da-c2fe08e635ea&scm=1007.12144.81309.9011_8949")
    print(browser.page_source)
    browser.quit()


taobao_detail_test()