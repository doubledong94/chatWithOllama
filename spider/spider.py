from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import os


def get_rendered_html_selenium(driver, url):
    try:
        print(f"正在加载页面: {url}")
        driver.get(url)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "content"))
            )
            time.sleep(2)
            print("页面加载和JS执行完成。")
        except Exception as e:
            print(f"等待页面元素超时或出错: {e}")
            pass

        return driver.page_source

    except Exception as e:
        print(f"获取网页内容时发生错误: {e}")
        return None


def url_to_file_name(url):
    return url.replace("https://", "").replace("/", "_") + ".txt"


def url_saved(url):
    filepath = os.path.join("extracted_files", url_to_file_name(url))
    return os.path.exists(filepath)


def save_content_to_file(url, content):
    filename = url_to_file_name(url)
    filepath = os.path.join("extracted_files", filename)

    # 保存内容到文件
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"内容已保存到: {filepath}")


def process_urls(file_path, driver_path=None):
    # 创建保存文件的目录
    if not os.path.exists("extracted_files"):
        os.makedirs("extracted_files")

    # 配置 Selenium WebDriver
    options = ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = None
    try:
        if driver_path:
            service = ChromeService(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(options=options)

        # 读取 URL 文件
        with open(file_path, 'r', encoding='utf-8') as url_file:
            urls = [line.strip() for line in url_file.readlines()]

        for url in urls:
            if not url:
                continue
            if url_saved(url):
                print(f"URL 已经处理过，跳过: {url}")
                continue

            # 获取页面内容
            rendered_html = get_rendered_html_selenium(driver, url)
            if rendered_html:
                soup = BeautifulSoup(rendered_html, 'html.parser')
                primary_content_elements = soup.find_all(class_='primary-content')
                content_elements = []
                for element in primary_content_elements:
                    content = element.find(class_='content')
                    if content:
                        content_elements.extend(content.find_all(recursive=False))
                extracted_text = "\n".join([element.text for element in content_elements])
                save_content_to_file(url, extracted_text)

            # 请求间隔 5 秒
            time.sleep(5)

    except Exception as e:
        print(f"处理 URL 时发生错误: {e}")
    finally:
        if driver:
            driver.quit()


if __name__ == '__main__':
    url_file_path = "urls.txt"  # 包含 URL 的 txt 文件路径
    chrome_driver_path = "/Users/ydd/github/chatWithOllama/chromedriver"  # ChromeDriver 路径

    process_urls(url_file_path, driver_path=chrome_driver_path)
