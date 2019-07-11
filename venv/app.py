from bottle import Bottle, run, template, route, request
from meli import Meli
from tqdm import tqdm
from phone import Phone

import json
import unicodedata
import sys
import pandas as pd
import os
import bs4
import requests

sys.path.append('../lib')

meli = Meli(client_id='3076720226288544', client_secret='L8A6zuXf9IsG2qzm1FL7ip3YsOl9do7C')

app = Bottle()


def add_decoded(element, elements_list):
    element = unicodedata.normalize('NFKD', element).encode('ascii', 'ignore')
    elements_list.append(element)


def get_meli_info(phones):
    col_items = []
    col_titles = []
    col_prices = []
    col_states = []
    col_cities = []

    for phone in tqdm(phones):
        for offset in ['0', '50', '100']:
            response = meli.get('/sites/MLA/search?q=' + phone.name + '&limit=50&offset=' + offset)
            json_response = json.loads(response.content)
            for result in json_response['results']:
                col_items.append(phone.name)
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

    csv_df.to_csv('phones-data.csv')

def get_specs_info(phones):
    phones_list = []

    for phone in phones:
        categories_txt = []
        specs_txt = []

        res = requests.get(phone.url)
        soup = bs4.BeautifulSoup(res.text, 'lxml')

        categories = soup.select('.category')
        for category in categories:
            add_decoded(category.text[1:], categories_txt)
        filter(lambda x: x != 'Memory', categories_txt)
        categories_txt.append('Name')
        #categories_txt = list(dict.fromkeys(categories_txt))

        specs = soup.select('.specs')
        for spec in specs:
            add_decoded(spec.text, specs_txt)
        specs_txt.append(phone.name)
        #specs_txt = list(dict.fromkeys(specs_txt))

        cat_specs_dict = dict(zip(categories_txt, specs_txt))

        phones_list.append(cat_specs_dict)

        #phone_dict[phone.name] = cat_specs_dict

    with open('phones-specs.json', 'w') as fp:
        json.dump(phones_list, fp)


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
    iphone_7 = Phone('Iphone 7', 'https://www.phonearena.com/phones/Apple-iPhone-7_id9815')
    samsung_s8 = Phone('Samsung s8', 'https://www.phonearena.com/phones/Samsung-Galaxy-S8_id10311')
    moto_x_style = Phone('Moto X Style', 'https://www.phonearena.com/phones/Motorola-Moto-X-Style_id9553')

    phones = [iphone_7, samsung_s8, moto_x_style]
    get_meli_info(phones)
    get_specs_info(phones)

def main():
    run(app, host='localhost', port=8000, reloader=True)


if __name__ == "__main__":
    main()

