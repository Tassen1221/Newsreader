from nntplib import NNTP, decode_header
from urllib.request import urlopen
import textwrap
import re
import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="Tassen123",
  database="TEST"
)
mycursor = mydb.cursor()

class NewsAgent:
    """
    An object that can distribute news items from news sources to news
    destinations.
    """
    def __init__(self):
        self.sources = []
        self.destinations = []
    def add_source(self, source):
        self.sources.append(source)
    def addDestination(self, dest):
        self.destinations.append(dest)
    def distribute(self):
        """
        Retrieve all news items from all sources, and Distribute them to all
        destinations.
        """
        items = []
        for source in self.sources:
            items.extend(source.get_items())
        for dest in self.destinations:
            dest.receive_items(items)
class NewsItem:
    """
    A simple news item consisting of a title and body text.
    """
    def __init__(self, title, body):
        self.title = title
        self.body = body
class NNTPSource:
    """
    A news source that retrieves news items from an NNTP group.
    """
    def __init__(self, servername, group, howmany, username=None, password=None):
        self.servername = servername
        self.group = group
        self.howmany = howmany
        self.username = username
        self.password = password
    
    def get_items(self):
        server = NNTP(self.servername, user=self.username, password=self.password)
        resp, count, first, last, name = server.group(self.group)
        start = last - self.howmany + 1
        resp, overviews = server.over((start, last))
        for id, over in overviews:
            title = decode_header(over['subject'])
            resp, info = server.body(id)
            body = '\n'.join(line.decode('latin')
                             for line in info.lines) + '\n\n'
            yield NewsItem(title, body)
        server.quit()

class SimpleWebSource:
    """
    A news source that extracts news items from a web page using regular
    expressions.
    """
    def __init__(self, url, title_pattern, body_pattern, encoding='utf8'):
        self.url = url
        self.title_pattern = re.compile(title_pattern)
        self.body_pattern = re.compile(body_pattern)
        self.encoding = encoding
    def get_items(self):
        text = urlopen(self.url).read().decode(self.encoding)
        titles = self.title_pattern.findall(text)
        bodies = self.body_pattern.findall(text)
        for title, body in zip(titles, bodies):
            yield NewsItem(title, textwrap.fill(body) + '\n')
class PlainDestination:
    """
    A news destination that formats all its news items as plain text.
    """
    def receive_items(self, items):
        for item in items:
            print(item.title)
            print('-' * len(item.title))
            print(item.body)
class HTMLDestination:
    """
    A news destination that formats all its news items as HTML.
    """
    def __init__(self, filename):
        self.filename = filename
    def receive_items(self, items):
        out = open(self.filename, 'w')
        print("""
        <html>
          <head>
            <title>Today's News</title>
          </head>
          <body>
          <h1>Today's News</h1>
        """, file=out)
        print('<ul>', file=out)
        id = 0
        for item in items:
            id += 1
            print('  <li><a href="#{}">{}</a></li>'
                    .format(id, item.title), file=out)
        print('</ul>', file=out)
        id = 0
        for item in items:
            id += 1
            print('<h2><a name="{}">{}</a></h2>'
                    .format(id, item.title), file=out)
            print('<pre>{}</pre>'.format(item.body), file=out)
        print("""
          </body>
        </html>
        """, file=out)
class DatabaseDestination:
    """
    A news destination that formats all its news items as plain text.
    """
    def receive_items(self, items):
        for item in items:
            sql = "INSERT INTO Articles (title, content) VALUES (%s, %s)"
            val = (item.title, item.body)
            mycursor.execute(sql, val)
            mydb.commit()
def runDefaultSetup():
    """
    A default setup of sources and destination. Modify to taste.
    """
    agent = NewsAgent()
    # A SimpleWebSource that retrieves news from Reuters:
    bbc_url = 'https://www.bbc.com/news'
    bbc_title = r'<h3 class="gs-c-promo-heading__title gel-paragon-bold nw-o-link-split__text">(.*?)</a>'
    bbc_body = r'<p class="gs-c-promo-summary gel-long-primer">([^<]*)</p>'
    bbc = SimpleWebSource(bbc_url, bbc_title, bbc_body)
    agent.add_source(bbc)
    # An NNTPSource that retrieves news from comp.lang.python.announce:
    clpa_server = 'news.eternal-september.org'
    clpa_group = 'comp.lang.python.announce'
    clpa_howmany = 10
    username = 'Tassen'
    password = 'xgzbiajhv'
    clpa = NNTPSource(clpa_server, clpa_group, clpa_howmany, username, password)
    agent.add_source(clpa)
    # Add plain-text destination and an HTML destination:
    agent.addDestination(DatabaseDestination())
    # agent.addDestination(PlainDestination())
    # agent.addDestination(HTMLDestination('news.html'))
    # Distribute the news items:
    agent.distribute()
if __name__ == '__main__': runDefaultSetup()