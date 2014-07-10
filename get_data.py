#!/usr/local/bin/python
#-*- coding: utf-8 -*-
# products.py
import requests
from bs4 import BeautifulSoup
from collections import namedtuple
import MySQLdb
import config
def get_product_urls(page_lim=10):
    """ Get urls of products from product listed web page """
    urls = []
    for i in range(page_lim):
        url = 'http://www.cosme.net/item/item_id/1064/products/page/{0}'.format(i)

        r = requests.get(url)
        html = r.text
        soup = BeautifulSoup(html)

        item_spans = soup.find_all('span', {'class': 'item'})
        for item_span in item_spans:
            a = item_span.a
            if a == None:
                continue
            urls.append(a['href'])
    return urls

def get_product_attributes(product_url):
    """ Get product attributes from product description web page """
    r = requests.get(product_url)
    html = r.text
    soup = BeautifulSoup(html)

    # product_id
    start_index = product_url.find('product_id')
    end_index = product_url.find('top')
    product_id = product_url[start_index+len('product_id/'):end_index-1]

    # product_nm
    product_nm = soup.find('strong', {'class': 'pdct-name'}).text

    # price
    p_item_info = soup.find_all('p', {'class': 'info-desc'})
    price = None
    for i, pii in enumerate(p_item_info):
        if u'円' in pii.text:
            volume_and_price = pii.text
            price = volume_and_price.split(u'・')[-1]
            price = price.replace(u'円', '')
            price = price.replace(',', '')

    # purposes
    dt_purposes = soup.find('dt', text=u'お悩み・効果')
    a_purposes = dt_purposes.parent.find_all('a')
    purposes = [ap.text for ap in a_purposes]

    # review count
    review_count = int(soup.find('span', {'itemprop': 'reviewCount'}).text)

    Attributes = namedtuple('Attributes', 'product_id product_nm price purposes review_count')
    attr = Attributes(product_id, product_nm, price, purposes, review_count)
    return attr

def insert_attributes2mysql(attrs):
    """ Insert products' attributes into mysql"""
    db = MySQLdb.connect(db=config.db, host=config.host, user=config.user, passwd=config.passwd)
    cursor = db.cursor()
    for attr in attrs:
        if None in attr:
            continue
        sql = u"""INSERT INTO beauty_electronics \
                (product_id, product_nm, price, purposes, review_count) \
                VALUES ('{0}', '{1}', {2}, '{3}', {4})"""
        sql = sql.format(attr.product_id, attr.product_nm,\
                attr.price, u','.join(attr.purposes), attr.review_count)
        try:
            cursor.execute(sql)
        except MySQLdb.IntegrityError:
            pass
        except MySQLdb.OperationalError:
            pass
    db.commit()
    db.close()


def main():
    # product description page urls
    urls = get_product_urls(page_lim=53)

    # get attributes of products
    attrs = []
    for product_url in urls:
        attr = get_product_attributes(product_url)
        attrs.append(attr)

    # insert product data into mysql
    insert_attributes2mysql(attrs)

if __name__ == '__main__':
    main()
