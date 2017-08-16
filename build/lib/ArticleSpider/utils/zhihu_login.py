import re
import requests

try:
    import cookielib
except:
    import http.cookiejar as cookielib


session = requests.session()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36"
header = {
    # "HOST":"www.zhihu.com",
    "User-Agent": user_agent
}
session.cookies = cookielib.LWPCookieJar(filename="cookies.txt")
try:
    session.cookies.load(ignore_discard=True)
except:
    print("cookie fail to loaded")


def get_zhihu_xsrf():
    response = session.get("https://www.zhihu.com/", headers=header)
    response_text = response.text
    match_obj = re.match('.*name="_xsrf" value="(.*)"', response_text, re.DOTALL)
    xsrf = ''
    if match_obj:
        xsrf = match_obj.group(1)

    return xsrf


def is_login():
    inbox_url = "https://www.zhihu.com/inbox"
    response = session.get(inbox_url,headers=header,allow_redirects=False)
    if response.status_code == 200:
        return True
    else:
        return False


def get_index():
    response = session.get("https://www.zhihu.com", headers=header)
    with open("index_page.html", "wb") as f:
        f.write(response.text.encode("utf-8"))
    print("ok")


def get_captcha():
    import time
    t = str(int(time.time() * 1000))
    captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(t)
    response = session.get(captcha_url, headers=header)
    with open("captcha.jpg", "wb") as f:
        f.write(response.content)
        f.close()

    from PIL import Image
    try:
        img = Image.open("captcha.jpg")
        img.show()
        img.close()
    except:
        pass
    captcha = input("输入验证码\n")
    return captcha


def zhihu_login(uname, password):
    if is_login():
        print("already login")
    else:
        if re.match(r"^1\d{10}", uname):
            print("手机号登录")
            post_url = "https://www.zhihu.com/login/phone_num"
            post_data = {
                "_xsrf": get_zhihu_xsrf(),
                "phone_num": uname,
                "password": password,
                "captcha": get_captcha()
            }
            response = session.post(post_url, data=post_data, headers=header)
            session.cookies.save()
            print(response.text.encode().decode('unicode_escape'))
        else:
            if "@" in uname:
                print("邮箱登录")
                post_url = "https://www.zhihu.com/login/email"
                post_data = {
                    "_xsrf": get_zhihu_xsrf(),
                    "phone_num": uname,
                    "password": password,
                    "captcha": get_captcha()
                }
                response = session.post(post_url, data=post_data, headers=header)
                session.cookies.save()
                print(response.text.encode().decode('unicode_escape'))

if __name__ == '__main__':
    zhihu_login("13571899655","hejunwei3269982")
    response = session.get("https://www.zhihu.com/api/v4/questions/59080378/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccollapsed_counts%2Creviewing_comments_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.author.is_blocking%2Cis_blocked%2Cis_followed%2Cvoteup_count%2Cmessage_thread_token%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit=20&offset=0", headers=header)
    print(response.text)
