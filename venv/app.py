from bottle import Bottle, run, template, route, request
from meli import Meli
from tqdm import tqdm

import json
import unicodedata
import sys
import pandas as pd
import os

sys.path.append('../lib')

meli = Meli(client_id='3076720226288544', client_secret='L8A6zuXf9IsG2qzm1FL7ip3YsOl9do7C')

app = Bottle()


def add_decoded(element, elements_list):
    element = unicodedata.normalize('NFKD', element).encode('ascii', 'ignore')
    elements_list.append(element)


@app.route('/authorize')
def authorize():
    if request.query.get('TG-5d23e4e8383153000610ce14-200616880'):
        meli.authorize(request.query.get('TG-5d23e4e8383153000610ce14-200616880'), 'http://localhost:8000/authorize')
    return meli.access_token


@app.route('/login')
def login():
    return "<a href='"+meli.auth_url(redirect_URI='http://localhost:8000/authorize')+"'>Login</a>"


@app.route('/get_info')
def get_info():
    col_items = []
    col_titles = []
    col_prices = []
    col_states = []
    col_cities = []
    items = ['iphone 7', 'iphone 8', 'iphone x']
    for item in tqdm(items):
        for offset in ['0', '50', '100']:
            response = meli.get('/sites/MLA/search?q='+item+'&limit=50&offset='+offset)
            json_response = json.loads(response.content)
            for result in json_response['results']:
                col_items.append(item)
                add_decoded(result['title'], col_titles)
                col_prices.append(result['price'])
                add_decoded(result['address']['state_name'], col_states)
                add_decoded(result['address']['city_name'], col_cities)

    csv_df = pd.DataFrame()
    csv_df['Item'] = col_items
    csv_df['Title'] = col_titles
    csv_df['Price'] = col_prices
    csv_df['State'] = col_states
    csv_df['City'] = col_cities

    csv_df.to_csv('iphones-data.csv', index=False)


def main():
    run(app, host='localhost', port=8000, reloader=True)


if __name__ == "__main__":
    main()

