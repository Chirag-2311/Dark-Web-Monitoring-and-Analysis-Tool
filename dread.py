import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import re
import pandas as pd
import sys
import json

class DreadCrawler:
    def __init__(self):
        self.proxies = {
            'http': 'socks5h://localhost:9050',
            'https': 'socks5h://localhost:9050'
        }
        

    def initialize_browser(self):
        firefox_options = webdriver.FirefoxOptions()
        firefox_options.set_preference("network.proxy.type", 1)
        firefox_options.set_preference("network.proxy.socks", "127.0.0.1")
        firefox_options.set_preference("network.proxy.socks_port", 9050)
        firefox_options.set_preference('network.proxy.socks_remote_dns', True)
        driver = webdriver.Firefox(options=firefox_options)
        return driver

    def sele_captcha(self, url):
        self.driver = self.initialize_browser()
        self.driver.get(url)
        try:
            if self.driver.find_element("xpath", "//*[contains(text(), '{}')]".format("Queue")):
                init_0_cookies = self.driver.get_cookies()
                init_cookies = self.driver.get_cookies()

                while init_0_cookies == init_cookies:
                    time.sleep(3)
                    init_cookies = self.driver.get_cookies()
        except:
            pass

        captcha_solved = False

        while not captcha_solved:
            current_cookies = self.driver.get_cookies()

            if current_cookies != init_cookies:
                cookies = self.driver.get_cookies()
                captcha_solved = True
                time.sleep(3)
            else:
                print("Captcha was not solved successfully.")
                time.sleep(2)

        return cookies
    
    def parse_crypto_addresses(self, html_content):
        btc_pattern = r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'
        eth_pattern = r'\b0x[a-fA-F0-9]{40}\b'
        btc_addresses = re.findall(btc_pattern, html_content)
        eth_addresses = re.findall(eth_pattern, html_content)
        return btc_addresses, eth_addresses
    
    def parse_crypto_address(self, text):
        btc_pattern = r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'
        eth_pattern = r'\b0x[a-fA-F0-9]{40}\b'
        btc_addresses = re.findall(btc_pattern, text)
        eth_addresses = re.findall(eth_pattern, text)
        if btc_addresses == None:

            return eth_addresses
        elif  eth_addresses == None:
            return btc_addresses
        else:
            return "None"


    def balance(self, address):
        url = "https://cointools.org/balance-checker/?address="
        response = requests.get(url + address).text
        soup = BeautifulSoup(response, 'html.parser')
        try:
            success_div = soup.find('div', class_='success')
            result = success_div.get_text(strip=True).split()
            return result[4] + result[5][:3]
        except:
            return "Invalid Address"
        
    def save_cookies_to_file(cookies, filename="dread_cookies.json"):
        with open(filename, 'w') as cookie_file:
            json.dump(cookies, cookie_file)

    def load_cookies_from_file(filename="dread_cookies.json"):
        try:
            with open(filename, 'r') as cookie_file:
                cookies = json.load(cookie_file)
                return cookies
        except (FileNotFoundError, json.JSONDecodeError):
            return "error loading"


    def fetch_link_data(self, link):
        # try:
        #     session_cookies = self.load_cookies_from_file()

        #     if session_cookies == "error loading" or session_cookies is None:
        #         # If the JSON file is empty or doesn't exist, solve captcha and save cookies
        #         cookies = self.sele_captcha(link)
        #         session_cookies = {cookie['name']: cookie['value'] for cookie in cookies}
        #         self.save_cookies_to_file(session_cookies)
        #         print("Cookies saved to file.")
        #     else:
        #         print("Cookies loaded successfully from file.")
        

            session_cookies = {'dcap': 'ebHmbW6U1bZiPxDo2JRSn1WD3KdfQzjc+f6A8+A51X3W4nBKQm8B2gA86G96HIweKTCS7ja+Ww2qz7hU49A+fUQ00tafzcSikFuaoyNdRDav3CDNQx+TFiXSvRtU5IjRGlfgd/1ytHi1WYcZjXdR+sM9vX1tOgW/pw==', 'dread': 'si87je4nubnjlnstov6rsff81u'}

            response = requests.get(link, cookies=session_cookies, proxies=self.proxies)
            response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code.
            
            soup = BeautifulSoup(response.text, 'html.parser')
            details = soup.find_all('div', class_='details')
            comments = soup.find_all('div', class_='comment-body')

            Output = {}

            for i in range(len(details)):
                
                username = details[i].find('a').text
                date = details[i].find('span')['title'].split(' - ')[0]
                username_with_date = f"{username}_{date}"
                comment_body = comments[i].get_text(strip=True)
                crypto = self.parse_crypto_address(comment_body)
                balance = self.balance(crypto)

                # comments_dict[username_with_date] = comment_body
                Output[username_with_date] = {
                'Comment': comment_body,
                'Crypto': crypto,
                'Balance': balance
            }  # Using the string representation of comments_dict as the key

            return Output

        # except Exception as e:
        #     print(f"An error occurred while fetching the link data: {e}")
        #     return None

    
    def crawl(self, keyword):
        search_url = f"http://g66ol3eb5ujdckzqqfmjsbpdjufmjd5nsgdipvxmsh7rckzlhywlzlqd.onion/search/?q={keyword}&sort=activity&fuzziness=auto"
        link_data = self.fetch_link_data(search_url)
        # print(link_data)
        return link_data
        

