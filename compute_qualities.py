#!/usr/local/bin/python
#-*- coding: utf-8 -*-
# compute_qualities.py
import sys
import csv
import config
import MySQLdb
import collections
import numpy as np
from sklearn import cluster
def connect_db():
    """Connect to the database"""
    db = MySQLdb.connect(db=config.db, host=config.host,\
            user=config.user, passwd=config.passwd)
    return db

def create_products_info():
    """製品情報のデータセットを作る"""
    # データの取得
    db = connect_db()
    cursor = db.cursor()
    sql = """SELECT * FROM beauty_electronics"""
    rows_count = cursor.execute(sql)
    if rows_count == 0:
        print "No Data"
        sys.exit(1)
    rows = cursor.fetchall()

    # データの整形
    attrs = []
    Attributes = collections.namedtuple('Attributes',\
            'product_id product_nm price purposes review_count')
    for row in rows:
        attr = Attributes(product_id=row[0],\
                product_nm=row[1].decode('utf-8'),\
                price=row[2], purposes=row[3].decode('utf-8').split(','),\
                review_count=row[4])
        attrs.append(attr)

    # 製品情報のデータセットを作る
    products_info = {}
    for attr in attrs:
        products_info[attr.product_id] =\
                {'product_nm': attr.product_nm,\
                 'price': attr.price,\
                 'purposes': attr.purposes,\
                 'review_count': attr.review_count}

    return products_info

def save_result(ref, labels, X, X_header):
    products_info = create_products_info()

    f = open('clustering_result.csv', 'wb')
    writer = csv.writer(f)

    #writer.writerow('label product_id product_nm price purposes review_count'.split(' '))
    X_header = [Xhi.encode('sjis') for Xhi in X_header]
    writer.writerow('label product_id product_nm price review_count'.split(' ') + X_header)
    for label, product_id, Xi in zip(labels, ref, X):
        product_info = products_info[product_id]
        row = [label, product_id]
        row.append(product_info['product_nm'].encode('sjis'))
        row.append(product_info['price'])
        row.append(product_info['review_count'])
        row += list(Xi)
        writer.writerow(row)
    f.close()


def compute_qualities():
    """Compute the qualities of each product"""
    products_info = create_products_info()

    # 効用毎の売上を計算
    sales_of_purposes = collections.defaultdict(float)
    for product_id, product_info in products_info.items():
        for purpose in product_info['purposes']:
            sales_of_purposes[purpose] += product_info['price']

    # 効用毎の売上割合を計算(高級度)
    max_sales = max(sales_of_purposes.values())
    for purpose in sales_of_purposes.keys():
        sales_of_purposes[purpose] /= max_sales

    # 商品ごとに効用の高級度を計算(販売数をかける)
    # このデータを元にクラスタリングを行う
    quality_of_producs = {}
    for product_id, product_info in products_info.items():
        quality_of_producs[product_id] = {}
        for purpose, sales in sales_of_purposes.items():
            quality_of_producs[product_id][purpose] =\
                    sales * product_info['review_count']

    # クラスタリングのためにXを作成する
    ref = []
    X = []
    X_header = quality_of_producs.values()[0].keys()
    for product_id, quality in quality_of_producs.items():
        ref.append(product_id)
        X.append(quality.values())
    X = np.array(X)

    # クラスタリングを行う
    km = cluster.MiniBatchKMeans(n_clusters=8, n_init=10)
    km.fit(X)

    return products_info, ref, km.labels_, X, X_header

def main():
    # データセットの作成, クラスタリングを行う
    products_info, ref, labels, X, X_header = compute_qualities()
    # 結果を保存する
    save_result(ref, labels, X, X_header)

if __name__ == '__main__':
    main()
