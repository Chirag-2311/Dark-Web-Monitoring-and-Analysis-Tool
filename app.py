from flask import Flask, render_template, request
from default_crawler import DefaultCrawler
from ahmia import AhmiaCrawler
from dread import DreadCrawler

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/default', methods=['GET', 'POST'])
def default_crawler():
    if request.method == 'POST':
        url = request.form['url']
        crawler = DefaultCrawler(url)
        data = crawler.crawl()
        return render_template('result.html', data=data)
    return render_template('defcrawl.html')

@app.route('/keyword-search', methods=['GET', 'POST'])
def keyword_search():
    results = []
    if request.method == 'POST':
        keyword = request.form['keyword']
        crawler = AhmiaCrawler()
        results = crawler.crawl(keyword)
        return render_template('ahmia.html', results=results)
    return render_template('ahmia.html')

@app.route('/crypto', methods=['GET', 'POST'])
def crypto_search():
    if request.method == 'POST':
        keyword = request.form['keyword']
        crawler = DreadCrawler()
        results = crawler.crawl(keyword)
        return render_template('dread.html', results=results)
    return render_template('dread.html', results={})

if __name__ == '__main__':
    app.run(debug=True)
