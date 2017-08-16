import hashlib
import re

def md5(url):
    if isinstance(url, str):
        url = url.encode('utf-8')
    hash = hashlib.md5(url)
    return hash.hexdigest()

def get_num(value):
    match_re = re.match(".*?(\d+).*", value)
    if match_re:
        num = int(match_re.group(1))
    else:
        num = 0

    return num
