import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import os
import subprocess
import pandas as pd
import re
import html_text

class DefaultCrawler:
    def __init__(self, url):
        self.url = url
        self.proxies = {
            'http': 'socks5h://localhost:9050',
            'https': 'socks5h://localhost:9050'
        }

    def get_url(self):
        try:
            response = requests.get(self.url, proxies=self.proxies)
            if response.status_code == 200:
                print("Successfully reached the onion site.")
                return response.content
            else:
                print(f"Failed to reach the onion site. Status code: {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"Error reaching the onion site: {e}")
            return None

    def captcha_check(self, content):
        captcha_keywords = [
            "Captcha", "Verification", "Human", "Challenge", "Security", "Authentication", 
            "Verification code", "Access control", "Turing test", "Puzzle", "Solving", 
            "Image recognition", "Character recognition", "Anti-bot", "Proof of humanity", 
            "Confirm identity", "Distorted text", "Click verification", "Select all images", 
            "Solve this puzzle", "Verify yourself", "Are you human?", "Confirm you're not a robot", 
            "Enter the code", "Complete the challenge", "Pass the test", "Identity confirmation", 
            "Human interaction", "Challenge-response", "Queue", "Select "
        ]
        soup = BeautifulSoup(content, 'html.parser')
        text_content = soup.get_text().lower()
        return any(keyword.lower() in text_content for keyword in captcha_keywords)

    def solve_captcha(self):
        firefox_options = webdriver.FirefoxOptions()
        firefox_options.set_preference("network.proxy.type", 1)
        firefox_options.set_preference("network.proxy.socks", "127.0.0.1")
        firefox_options.set_preference("network.proxy.socks_port", 9050)
        firefox_options.set_preference('network.proxy.socks_remote_dns', True)

        driver = webdriver.Firefox(options=firefox_options)
        driver.get(self.url)

        captcha_solved = False
        init_cookies = driver.get_cookies()

        while not captcha_solved:
            current_cookies = driver.get_cookies()
            if current_cookies != init_cookies:
                captcha_solved = True
                cookies = current_cookies
                time.sleep(3)
            else:
                print("Captcha was not solved successfully.")
                time.sleep(2)
        
        return cookies

    def scrape_bs4(self, response):
        try:
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a', href=True)
                onion_links = [link['href'] for link in links if '.onion' in link['href']]
                with open("link.txt", "a") as handle:
                    handle.write("\n".join(onion_links))
                return "Links Collected"
            else:
                print("Failed to fetch the content from the URL")
                return []
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    def parse_crypto_addresses(self, html_content):
        btc_pattern = r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'
        eth_pattern = r'\b0x[a-fA-F0-9]{40}\b'
        btc_addresses = re.findall(btc_pattern, html_content)
        eth_addresses = re.findall(eth_pattern, html_content)
        return btc_addresses, eth_addresses

    def find_onion_links(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        return [link['href'] for link in soup.find_all('a', href=True) if '.onion' in link['href']]

    def exif_images(self, response, save_dir="images"):
        try:
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                img_tags = soup.find_all('img', src=True)
                image_links = [img['src'] for img in img_tags]

                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)

                for img_link in image_links:
                    img_link = f"{self.url}/{img_link}"
                    img_name = img_link.split('/')[-1]
                    img_path = os.path.join(save_dir, img_name)

                    img_response = requests.get(img_link, proxies=self.proxies)
                    with open(img_path, 'wb') as f:
                        f.write(img_response.content)

                    exiftool_command = ['exiftool', img_path]
                    exif_process = subprocess.run(exiftool_command, capture_output=True, text=True)
                    return str(exif_process.stdout)
            else:
                print("Failed to fetch the content from the URL")
        except Exception as e:
            print(f"An error occurred: {e}")

    def crawl(self):
        response = self.get_url()
        if response:
            if self.captcha_check(response):
                cookies = self.solve_captcha()
                session_cookies = {cookie['name']: cookie['value'] for cookie in cookies}
                response = requests.get(self.url, cookies=session_cookies, proxies=self.proxies)
            else:
                response = requests.get(self.url, proxies=self.proxies)

            headers = response.headers
            server_details = headers.get('Server', 'Server details not available')

            soup = BeautifulSoup(response.text, 'html.parser')
            try:
                title_tag = soup.find('title')
                site_name = title_tag.text
            except:
                site_name = "No title found"

            response_text = response.text
            self.scrape_bs4(response)
            exif_response = self.exif_images(response)

            btc_addresses, eth_addresses = self.parse_crypto_addresses(response_text)
            btc_balances = [f"{address}: {self.balance(address)}" for address in btc_addresses]
            eth_balances = [f"{address}: {self.balance(address)}" for address in eth_addresses]
            links = self.find_onion_links(response_text)

            data = {
                'URL': self.url,
                'Server Details': server_details,
                'Title': site_name,
                'Bitcoin Addresses': '; '.join(btc_addresses),
                'Ethereum Addresses': '; '.join(eth_addresses),
                'Links': '; '.join(links),
                'EXIF Data': exif_response,
                'Classify': self.classify()
            }

            return data

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

    def classify(self):
        response = requests.get(self.url, proxies=self.proxies)
        text = response.text
        text = html_text.extract_text(text)
        print(text)

        terms_list = [
            "Supports drug intake/market", "Against drug intake/market", "Support arms/weapons", 
            "Against arms/weapons", "Illicit Social", "Supports violence", "Against violence", 
            "Hacking", "Selling credentials", "Child abuse/pornography", "General pornography", 
            "Illegal markets"
        ]

        output = self.query({
            "inputs": {
                "source_sentence": text,
                "sentences": terms_list
            },
        })

        top = sorted(output, reverse=True)[:2]
        result = [terms_list[output.index(i)] for i in top if isinstance(output, list)]
        return result

    def query(self, payload):
        API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/bert-base-nli-mean-tokens"
        headers = {"Authorization": "Bearer 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"}
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()
