import os
import pickle
import time

from selenium.common import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import json
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from browsermobproxy import Server

# 初始化 Flask 应用
app = Flask(__name__)

# 指定 ChromeDriver 的绝对路径
chromedriver_path = r"C:\Program Files\Google\Chrome\Application\chromedriver-win64\chromedriver.exe"
service = Service(executable_path=chromedriver_path)
cookies_dir = os.path.join(os.getcwd(), 'cookies')
data_dir = os.path.join(os.getcwd(), 'data')
if not os.path.exists(cookies_dir):
    os.makedirs(cookies_dir)

# 启动 BrowserMob Proxy 服务器
server = Server('./browsermob-proxy-2.1.4/bin/browsermob-proxy')
server.start()
proxy = server.create_proxy()

driver = None


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/start_selenium', methods=['GET'])
def start_selenium():
    global driver
    if driver is None:
        # 配置 Selenium 使用 BrowserMob Proxy
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(f"--proxy-server={proxy.proxy}")

        # 开始拦截和修改网络请求
        proxy.new_har("test_har", options={'captureContent': True, 'captureHeaders': True})

        driver = webdriver.Chrome(service=service, options=chrome_options)

        return jsonify({"status": "Selenium started and example.com opened."})
    else:
        return jsonify({"status": "Selenium is already running."})


@app.route('/get_har', methods=['GET'])
def get_har():
    if proxy:
        har = proxy.har
        return jsonify(har)
    else:
        return jsonify({"status": "No proxy available."})


@app.route('/save_cookies/<filename>', methods=['GET'])
def save_cookies(filename):
    global driver
    if driver is not None:
        cookies = driver.get_cookies()
        cookie_file_path = os.path.join(cookies_dir, f'{filename}.pkl')
        with open(cookie_file_path, 'wb') as file:
            pickle.dump(cookies, file)
        return jsonify({"status": f"Cookies saved as {filename}.pkl"})
    else:
        return jsonify({"status": "Selenium is not running."})


@app.route('/load_cookies/<filename>', methods=['GET'])
def load_cookies(filename):
    global driver
    if driver is not None:
        url = request.args.get('url')
        if not url:
            return jsonify({"status": "URL parameter is required."})

        cookie_file_path = os.path.join(cookies_dir, f'{filename}.pkl')
        if os.path.exists(cookie_file_path):
            try:
                with open(cookie_file_path, 'rb') as file:
                    cookies = pickle.load(file)

                # 导航到相关域名
                driver.get(url)

                # 加载 cookie
                for cookie in cookies:
                    driver.add_cookie(cookie)

                driver.refresh()
                return jsonify({"status": f"Cookies loaded from {filename}.pkl and page refreshed."})
            except Exception as e:
                return jsonify({"status": "An error occurred while loading cookies", "error": str(e)})
        else:
            return jsonify({"status": f"Cookie file {filename}.pkl not found."})
    else:
        return jsonify({"status": "Selenium is not running."})


@app.route('/stop_selenium', methods=['GET'])
def stop_selenium():
    global driver
    if driver is not None:
        driver.quit()
        driver = None
        return jsonify({"status": "Selenium stopped."})
    else:
        return jsonify({"status": "Selenium is not running."})


@app.route('/open_url', methods=['GET'])
def open_url():
    global driver
    if driver is None:
        return jsonify({"status": "Selenium is not running."})

    url = request.args.get('url')
    if not url:
        return jsonify({"status": "URL is required."})

    driver.get(url)
    return jsonify({"status": f"Opened URL: {url}"})


@app.route('/interact_with_element', methods=['POST'])
def interact_with_element():
    global driver
    if driver is None:
        return jsonify({"status": "Selenium is not running."})

    try:
        data = request.json
        method = data.get('method')
        value = data.get('value')
        click = data.get('click', False)
        wait_time = data.get('wait_time', 10)  # 默认等待时间为10秒

        if not method or not value:
            return jsonify({"status": "Method and value are required."})

        # 显式等待设置
        wait = WebDriverWait(driver, wait_time)

        # 查找元素的方法映射
        locator_methods = {
            'id': By.ID,
            'name': By.NAME,
            'xpath': By.XPATH,
            'css': By.CSS_SELECTOR,
            'class': By.CLASS_NAME,
            'tag': By.TAG_NAME,
            'link_text': By.LINK_TEXT,
            'partial_link_text': By.PARTIAL_LINK_TEXT
        }

        if method not in locator_methods:
            return jsonify({"status": "Invalid method specified."})

        # 查找元素
        element = wait.until(EC.presence_of_element_located((locator_methods[method], value)))

        if element is None:
            return jsonify({"status": "Element not found."})

        # 点击元素
        if click:
            element.click()

        return jsonify({"status": "Element interacted successfully."})
    except TimeoutException:
        return jsonify({"status": "Element not found within the specified wait time."})
    except Exception as e:
        return jsonify({"status": f"Error occurred: {e}"})


@app.route('/fetch_and_cache_data', methods=['GET'])
def fetch_and_cache_data():
    global driver
    if driver is None:
        return jsonify({"error": "Selenium is not started. Please start it first."})

    # 新建一个 HAR 文件，避免之前的包冲突
    proxy.new_har("test_har", options={'captureContent': True, 'captureHeaders': True})

    # 等待页面加载
    time.sleep(5)

    # 初始化数据列表
    item_list = []
    fetched_items = set()

    while True:
        # 获取页面内容
        page_source = driver.page_source

        # 使用BeautifulSoup解析页面内容
        soup = BeautifulSoup(page_source, 'html.parser')

        # 查找虚拟项目的包装器
        virtual_item_wrapper = soup.find('div', class_='virtual-item-wrapper')

        if not virtual_item_wrapper:
            return jsonify({"status": "未找到虚拟项目的包装器"})

        # 获取所有子元素
        virtual_item_views = virtual_item_wrapper.find_all('div', class_='virtual-item-view')

        new_data_count = 0

        for item in virtual_item_views:
            product_name_elem = item.find('div', class_='el-tooltip title')
            product_name = product_name_elem.text if product_name_elem else ""

            # 使用商品名称作为唯一标识符
            if product_name in fetched_items:
                continue

            fetched_items.add(product_name)
            item_list.append({'商品': product_name})
            new_data_count += 1

        print(f"下滑页面完成，已获取 {new_data_count} 条新数据")

        # 检查是否没有新数据
        if new_data_count == 0:
            break

        # 模拟鼠标滚轮下滑
        actions = ActionChains(driver)
        for _ in range(5):  # 增加滚动次数
            actions.send_keys(Keys.PAGE_DOWN).perform()
            time.sleep(0.2)  # 每次滚动后等待0.2秒

        # 显式等待页面加载完成
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )

    # 从 HAR 文件中获取请求和响应数据
    har_data = proxy.har

    # 打印 HAR 数据以调试
    debug_har_path = os.path.join(data_dir, 'debug_har.json')
    with open(debug_har_path, 'w', encoding='utf-8') as debug_file:
        json.dump(har_data, debug_file, ensure_ascii=False, indent=4)

    # 处理 HAR 文件中的数据
    for entry in har_data['log']['entries']:
        if entry['request']['url'].startswith('https://ks.feigua.cn/api/v1/product/GetProductGetSearchListV2'):
            content = entry['response']['content']
            response_data = content.get('text') or content.get('body') or ''
            if response_data:
                try:
                    response_json = json.loads(response_data)
                    items = response_json.get("Data", {}).get("ItemList", [])
                    item_list.extend(items)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                    print(f"Response data: {response_data}")

    if item_list:
        # 将响应数据缓存到文件中
        cache_file_path = os.path.join(data_dir, 'cached_response.json')
        with open(cache_file_path, 'w', encoding='utf-8') as cache_file:
            json.dump(item_list, cache_file, ensure_ascii=False, indent=4)

        return jsonify({"status": "Data fetched and cached successfully.", "data": item_list})
    else:
        return jsonify({"error": "Failed to fetch data from the target URL."})


if __name__ == '__main__':
    app.run(debug=True)
