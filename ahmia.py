import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, parse_qs
import time

class AhmiaCrawler:
    def __init__(self):
        self.proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050',
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }

    def get_search_results(self, keyword):
        query = '+'.join(keyword.split())
        url = f'https://ahmia.fi/search/?q={query}'
        response = requests.get(url, proxies=self.proxies, headers=self.headers)
        if response.status_code == 200:
            return response.text
        else:
            return None

    def find_onion_links(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        links = soup.find_all('a', href=True)
        onion_links = []
        for link in links:
            href = link['href']
            if "/search/redirect" in href:
                query_string = urlparse(href).query
                params = parse_qs(query_string)
                redirect_url = params.get('redirect_url', [None])[0]
                if redirect_url:
                    onion_links.append(redirect_url)
        return onion_links

    def parse_crypto_addresses(self, html_content):
        patterns = {
            'btc': re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'),
            'eth': re.compile(r'\b0x[a-fA-F0-9]{40}\b'),
            'xrp': re.compile(r'\br[1-9A-HJ-NP-Za-km-z]{25,34}\b'),
            'ltc': re.compile(r'\b[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}\b'),
            'bch': re.compile(r'\b(bitcoincash:)?(q|p)[a-z0-9]{41}\b'),
            'ada': re.compile(r'\baddr1[a-zA-Z0-9]{58}\b'),
            'dot': re.compile(r'\b1[a-km-zA-HJ-NP-Z1-9]{47,51}\b'),
            'doge': re.compile(r'\bD[5-9A-HJ-NP-U][1-9A-HJ-NP-Za-km-z]{32}\b'),
            'xmr': re.compile(r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b'),
            'trx': re.compile(r'\bT[a-zA-Z0-9]{33}\b')
        }
        
        addresses = {coin: set(re.findall(regex, html_content)) for coin, regex in patterns.items()}
        return addresses

    def get_balance(self, coin, address):
        urls = {
            'btc': f"https://api.blockchain.info/haskoin-store/btc/address/{address}/balance",
            'eth': f"https://api.blockchain.info/v2/eth/data/account/{address}/wallet?page=0&size=20",
            'xrp': f"https://api.blockchain.info/v2/xrp/data/account/{address}/wallet?page=0&size=20",
            'ltc': f"https://api.blockchain.info/v2/ltc/data/account/{address}/wallet?page=0&size=20",
            'bch': f"https://api.blockchain.info/v2/bch/data/account/{address}/wallet?page=0&size=20",
            'ada': f"https://api.blockchain.info/v2/ada/data/account/{address}/wallet?page=0&size=20",
            'dot': f"https://api.blockchain.info/v2/dot/data/account/{address}/wallet?page=0&size=20",
            'doge': f"https://api.blockchain.info/v2/doge/data/account/{address}/wallet?page=0&size=20",
            'xmr': f"https://api.blockchain.info/v2/xmr/data/account/{address}/wallet?page=0&size=20",
            'trx': f"https://api.blockchain.info/v2/trx/data/account/{address}/wallet?page=0&size=20"
        }

        url = urls.get(coin)
        if not url:
            return "Unsupported Coin"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            # Standardize the response
            if coin == 'btc':
                balance = data.get('confirmed', 0) + data.get('unconfirmed', 0)
            else:
                balance = data.get('balance', 0)
            
            # Convert balance to the appropriate format (e.g., from satoshis to BTC)
            if coin == 'btc':
                balance = balance / 100000000  # Convert satoshis to BTC
            return f"{balance} {coin.upper()}"
        
        except Exception as e:
            print(f"Error fetching balance for {coin.upper()} address {address}: {e}")
            return "Error"

    def crawl(self, keyword):
        results = []
        html_content = self.get_search_results(keyword)
        if html_content:
            onion_links = self.find_onion_links(html_content)[:40]
            for onion_url in onion_links:
                try:
                    time.sleep(2)
                    response = requests.get(onion_url, proxies=self.proxies, headers=self.headers)
                    if response.status_code == 200:
                        crypto_addresses = self.parse_crypto_addresses(response.text)
                        
                        # Skip if no crypto addresses are found
                        if not any(crypto_addresses.values()):
                            continue

                        balances_info = {}
                        for coin, addresses in crypto_addresses.items():
                            balances_info[coin] = [self.get_balance(coin, addr) for addr in addresses]

                        url_data = {
                            'URL': onion_url,
                            'Addresses': {coin: '; '.join(addresses) for coin, addresses in crypto_addresses.items()},
                            'Balances': {coin: '; '.join(balances) for coin, balances in balances_info.items()},
                        }
                        results.append(url_data)
                    else:
                        print(f"Failed to retrieve content from {onion_url}. Status code: {response.status_code}")
                except Exception as e:
                    print(f"Error fetching {onion_url}: {e}")
        return results
