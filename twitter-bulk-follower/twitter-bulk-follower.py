import os
import time
import random
import logging
import sys
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

# 确保日志输出使用 UTF-8 编码
if sys.stdout.encoding != 'UTF-8':
    sys.stdout.reconfigure(encoding='UTF-8')

def click_element(driver, xpath):
    element = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    driver.execute_script("arguments[0].click();", element)

def login_to_twitter(driver, username, password):
    logger.info("开始登录 Twitter")
    driver.get("https://twitter.com/login")
    time.sleep(5)  # 等待页面加载
    logger.info(f"当前页面标题: {driver.title}")
    logger.info(f"当前页面 URL: {driver.current_url}")
    
    if "challenge" in driver.current_url or "security" in driver.current_url:
        logger.warning("检测到安全检查或验证码，可能需要人工干预")
        input("请手动完成验证，然后按回车继续...")
    
    try:
        username_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='text']"))
        )
        username_input.send_keys(username)
        click_element(driver, "//span[text()='Next']")
        
        password_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_input.send_keys(password)
        click_element(driver, "//span[text()='Log in']")
        
        WebDriverWait(driver, 30).until(EC.url_contains("home"))
        logger.info("成功登录 Twitter")
    except Exception as e:
        logger.error(f"登录失败: {str(e)}", exc_info=True)
        raise

def bulk_follow(driver, page_url):
    logger.info(f"开始访问页面: {page_url}")
    driver.get(page_url)
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # 使用正则表达式匹配 Twitter 用户链接
        twitter_pattern = re.compile(r'https?://(?:www\.)?(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)/?$')
        
        user_links = driver.find_elements(By.XPATH, "//a[@href]")
        usernames = []
        for link in user_links:
            href = link.get_attribute('href')
            match = twitter_pattern.match(href)
            if match:
                usernames.append(match.group(1))
        
        logger.info(f"找到 {len(usernames)} 个有效的 Twitter 用户链接")
        
        for username in usernames:
            logger.info(f"尝试关注用户: {username}")
            try:
                driver.get(f"https://twitter.com/{username}")
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                follow_button = None
                for attempt in range(5):  # 增加尝试次数
                    try:
                        follow_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'css-1jxf684') and .//span[text()='关注' or text()='Follow']]"))
                        )
                        break
                    except:
                        logger.info(f"尝试 {attempt + 1}: 未找到关注按钮，刷新页面")
                        driver.refresh()
                        time.sleep(5)
                
                if follow_button:
                    driver.execute_script("arguments[0].click();", follow_button)
                    logger.info(f"成功关注用户: {username}")
                else:
                    logger.warning(f"无法找到关注按钮: {username}")
                    logger.debug(f"页面源代码: {driver.page_source}")
            except Exception as e:
                logger.warning(f"无法关注用户 {username}: {str(e)}")
            time.sleep(random.uniform(5, 10))  # 增加随机延迟时间
    except Exception as e:
        logger.error(f"批量关注过程中发生错误: {str(e)}", exc_info=True)

if __name__ == "__main__":
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.58 Safari/537.36")
    chrome_options.binary_location = "/opt/google/chrome/chrome"  # 指定 Chrome 二进制文件的位置

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.set_page_load_timeout(60)  # 增加页面加载超时时间
    driver.implicitly_wait(20)  # 添加隐式等待

    username = os.environ.get("TWITTER_USERNAME", "your username")
    password = os.environ.get("TWITTER_PASSWORD", "your password")
    page_url = "https://github.com/DennisThink/awesome_twitter_CN"

    try:
        login_to_twitter(driver, username, password)
        time.sleep(10)  # 增加登录后的等待时间
        logger.info("准备开始批量关注")
        bulk_follow(driver, page_url)
    except Exception as e:
        logger.error(f"主程序发生错误: {str(e)}", exc_info=True)
    finally:
        logger.info("关闭浏览器")
        driver.quit()