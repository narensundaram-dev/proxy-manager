import requests
import functools
from datetime import datetime as dt

import pandas as pd
from bs4 import BeautifulSoup, NavigableString


class ProxyManager(object):

    url = "https://free-proxy-list.net/"
    proxies = []
    file_proxies = "proxies.csv"
    last_fetch_time = dt(1970, 1, 1)
    func_proxy_usage = {}
    current_proxy = {
        "idx": -1,
        "ip": "",
        "port": "",
        "https": ""
    }

    def __init__(self):
        pass

    @classmethod
    def init(cls):
        # response = requests.get(ProxyManager.url)
        # soup = BeautifulSoup(response.text, "html.parser")

        with open("output.html", "r") as html:
            soup = BeautifulSoup(html.read(), "html.parser")

        table = soup.find("table", attrs={"id": "proxylisttable"})
        body = filter(lambda x: not isinstance(x, NavigableString), table.tbody.children)
        for i, row in enumerate(body):
            columns = list(filter(lambda x: not isinstance(x, NavigableString), row.contents))
            proxy = {"sno": i + 1}
            fields = ["ip", "port", "code", "country", "type", "unknown", "https", "create_date"]
            for idx, key in enumerate(fields):
                proxy[key] = columns[idx].get_text()
            proxy["current"] = "no"
            cls.proxies.append(proxy)

        cls.save()
        cls.set()
        cls.last_fetch_time = dt.now()
        return cls.proxy()

    @classmethod
    def proxy(cls):
        protocol = "https" if cls.current_proxy["https"] == "yes" else "http"
        ip, port = cls.current_proxy["ip"], cls.current_proxy["port"]
        proxy = f"{protocol}://{ip}:{port}"
        return {"http": proxy, "https": proxy}

    @classmethod
    def set(cls, idx=0):
        df = cls.get()
        df.loc[df["ip"] == cls.current_proxy["ip"], "current"] = "no"
        cls.current_proxy = cls.pick(df, idx)
        df.loc[df["ip"] == df.iloc[idx].ip, "current"] = "yes"
        df.to_csv(cls.file_proxies, index=False)
        return cls.proxy()

    @classmethod
    def get(cls):
        df = pd.read_csv(cls.file_proxies)
        return df

    @classmethod
    def pick(cls, df, idx):
        return {
            "idx": idx,
            "ip": df.iloc[idx].ip,
            "port": df.iloc[idx].port,
            "https": df.iloc[idx].https
        }

    @classmethod
    def save(cls):
        df = pd.DataFrame(cls.proxies)
        df_elite_proxies = df[df['type'].str.contains("elite", na=False, case=False)]
        # cls.proxies = df_elite_proxies.to_list()  # Update only elite proxies in proxies
        df_elite_proxies.to_csv(cls.file_proxies, index=False)

    @classmethod
    def rotate(cls, every=1):
        def inner(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                cls.func_proxy_usage.setdefault(func.__name__, 0)

                if (dt.now() - cls.last_fetch_time).seconds >= (60 * 10):
                    proxies = cls.init()
                else:
                    if cls.func_proxy_usage[func.__name__] >= every:
                        proxies = cls.next()
                        cls.func_proxy_usage[func.__name__] = 0
                    else:
                        proxies = cls.proxy()

                cls.func_proxy_usage[func.__name__] += 1
                kwargs["proxies"] = proxies
                return func(*args, **kwargs)
            return wrapper
        return inner

    @classmethod
    def next(cls):
        idx = ProxyManager.current_proxy["idx"]
        return cls.set(idx + 1)


@ProxyManager.rotate(every=3)
def get_my_ip(**kwargs):
    proxies = kwargs.get("proxies", {})
    # response = requests.get("https://httpbin.org/ip", proxies=proxies)
    # print("response: ", response.json())
    return proxies


def main():
    ProxyManager.init()
    for i in range(10):
        proxies = get_my_ip()
        print("{}: {}".format(i+1, proxies["http"]))


if __name__ == '__main__':
    main()
