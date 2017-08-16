import requests
from scrapy.selector import Selector
from scrapy.exporters import JsonItemExporter
import json
import random

def crawl_ips():
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0"}
    file = open('xici_proxy.json', 'wb')
    exporter = JsonItemExporter(file, encoding='utf-8', ensure_ascii=False)
    exporter.start_exporting()
    for i in range(1862):
        response = requests.get("http://www.xicidaili.com/nn/{0}".format(i), headers=headers)
        selector = Selector(text=response.text)
        tr_list = selector.css("tr")
        ip_list = []
        for tr in tr_list[1:]:
            speed = tr.css(".bar::attr(title)").extract()
            if float(speed[0].split('秒')[0])<1 and float(speed[1].split('秒')[0])<1:
                row = tr.css("td::text").extract()
                ip = row[0]
                port = row[1]
                proxy_type = row[5]
                ip_list.append([ip,port,proxy_type])
                json_row = {"ip":ip,"port":port,"proxy_type":proxy_type}
                exporter.export_item(json_row)
    exporter.finish_exporting()
    file.close()


def get_ip():

    import socks
    import socket
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9150)
    socket.socket = socks.socksocket

    ip_pool = json.load(open('xici_proxy.json','r'))
    ip_dict = random.choice(ip_pool)
    ip = ip_dict["ip"]
    port = ip_dict["port"]
    proxy_type = ip_dict["proxy_type"].lower()
    proxy_ip = proxy_type + "://" + ip + ":" + port
    proxies = {
        'http':'http://183.78.183.156:82',
        'https':'https://1.83.124.190:8118'
    }
    print(proxy_ip)
    response = requests.get("https://www.majialichen.com",proxies=proxies)
    print(response.text)
    if response.status_code == 200:
        return proxy_ip
    else:
        get_ip()

def tor_requests():
    ##Download SocksiPy - A Python SOCKS client module. ( http://code.google.com/p/socksipy-branch/downloads/list )
    ##Simply copy the file "socks.py" to your Python's lib/site-packages directory, and initiate a socks socket like this.
    ## NOTE: you must use socks before urllib2.
    from stem import Signal
    from stem.control import Controller

    with Controller.from_port(port=9051) as controller:
        controller.authenticate("torpasswd")
        controller.signal(Signal.NEWNYM)

    import socks
    import socket
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)
    socket.socket = socks.socksocket

    url = 'http://115.28.82.133'
    response = requests.get(url=url)
    print(response.text)

def new_tor_ip():
    from stem import Signal
    from stem.control import Controller

    with Controller.from_port(port=9051) as controller:
        controller.authenticate("torpasswd")
        controller.signal(Signal.NEWNYM)

tor_requests()
