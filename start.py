import requests


def start_browser():
    response = requests.get('http://127.0.0.1:5000/start_selenium')
    return response.json()


def load_cookies(filename, url):
    response = requests.get(f'http://127.0.0.1:5000/load_cookies/{filename}', params={'url': url})
    print(response.text)  # 打印响应内容，帮助调试
    response.raise_for_status()  # 确保请求成功
    return response.json()


def fetch_and_cache_data():
    response = requests.get('http://127.0.0.1:5000/fetch_and_cache_data')
    response.raise_for_status()  # 确保请求成功
    return response.json()


def open_url(url):
    response = requests.get('http://127.0.0.1:5000/open_url', params={'url': url})
    response.raise_for_status()  # 确保请求成功
    return response.json()


if __name__ == '__main__':
    # 启动浏览器
    start_response = start_browser()
    print(f'Start Browser: {start_response}')

    # 保存Cookies
    # save_cookies_response = save_cookies('ks.feigua.cn')  # 替换为你要保存的Cookie文件名
    # print(f'Save Cookies: {save_cookies_response}')

    # 导入Cookies
    cookies_filename = 'ks.feigua.cn'  # 替换为你的Cookie文件名
    target_url = 'https://ks.feigua.cn/'  # 替换为你要导航的URL
    load_cookies_response = load_cookies(cookies_filename, target_url)
    print(f'Load Cookies: {load_cookies_response}')

    # 获取并缓存数据
    # fetch_data_response = fetch_and_cache_data()
    # print(f'Fetch and Cache Data: {fetch_data_response}')

    # 打开指定网址
    url_to_open = 'https://ks.feigua.cn/Member#/StaticPage/ProductSearchV2'  # 替换为你要打开的网址
    open_url_response = open_url(url_to_open)
    print(f'Open URL: {open_url_response}')
