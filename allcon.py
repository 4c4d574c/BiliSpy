# 最大线程数
MAX_WORKER = 64
# 请求头
HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36",
            "accept-encoding": "gzip, deflate",
            "accept-language": "zh-CN,zh;q=0.9",
            "referer": ""}
# 数据接口基础链接
URL_BASE_TIME = "https://s.search.bilibili.com/cate/search?main_ver=v3&search_type=video&view_type=hot_rank&order=click&copy_right=-1&cate_id={}&page={}&pagesize=20&jsonp=jsonp&time_from={}&time_to={}&callback=jsonCallback_bili_{}"
# 代理链接
PROXYURL = ""
