import json
import requests
from bs4 import BeautifulSoup
import sys
import logging
import pymysql
import dbinfo

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create the database connection outside of the handler to allow connections to be
# re-used by subsequent function invocations.
try:
    conn = pymysql.connect(
        host = os.environ['DB_HOST'],
        user = os.environ['DB_USERNAME'],
        passwd = os.environ['DB_PASSWORD'],
        db = os.environ['DB_NAME'],
        port = int(os.environ['DB_PORT']),
        charset='utf8mb4')
except pymysql.MySQLError as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit()

def lambda_handler(event, context):
    
    url = event['url']
    
    return {
        'statusCode': 200,
        'body': json.dumps(crawling(url))
    }

def crawling(url):
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3"
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser') 
    
    #11번가니?
    if url.startswith("https://www.11st.co.kr/"):
        title = soup.select_one('meta[property="og:title"]')['content']
        image = soup.select_one('meta[property="og:image"]')['content']
        price = soup.select_one('meta[property="og:description"]')['content'].split(':')[1][1:]
        
        sql_string = f"insert into product (url, title, image, price, site) values('{url}','{title}','{image}','{price}','11번가')"
    
    elif url.startswith("https://www.coupang.com/"):
        title = soup.select_one('meta[property="og:title"]')['content']
        image = soup.select_one('meta[property="og:image"]')['content']
        
        price = "알 수 없습니다."
        price_selector = "#contents > div.prod-atf > div > div.prod-buy.new-oos-style.not-loyalty-member.eligible-address.without-subscribe-buy-type.DISPLAY_0 > div.prod-price-container > div.prod-price > div > div.prod-coupon-price.price-align.major-price-coupon > span.total-price > strong"
        element = soup.select_one(price_selector)
        price = element.text
        
        sql_string = f"insert into product (url, title, image, price, site) values('{url}','{title}','https:{image}','{price}','쿠팡')"
    
    else:    
        print("11번가, 쿠팡이 아닙니다.")
        
    with conn.cursor() as cur:
        cur.execute(sql_string)
        conn.commit()
        cur.execute("select * from product")
        logger.info("The following products have been added to the database:")
        for row in cur:
            logger.info(row)
        conn.commit()

    return title + price

    
