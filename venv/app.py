from meli import Meli
from tqdm import tqdm
from phone import Phone


import json
import unicodedata
import sys
import os
import bs4
import requests
import ConfigParser

sys.path.append('../lib')

config = ConfigParser.RawConfigParser()
configFilePath = r'config.txt'
config.read(configFilePath)

try:
    code = config.get('file', 'code')
    url = config.get('file', 'url')
    client_id = config.get('file', 'client_id')
    client_secret = config.get('file', 'client_secret')
except ConfigParser.NoOptionError:
    print('Could not read configuration file')
    sys.exit(1)

meli = Meli(client_id=client_id, client_secret=client_secret)


def decode(element):
    """
    Convierte unicode a string
    """
    return unicodedata.normalize('NFKD', element).encode('ascii', 'ignore')


def get_meli_users_info(users, items):
    """
    Genera un .json a partir de informacion extraida de usuarios de la SDK de MercadoLibre
    """
    meli_users_json = []
    users_items = zip(users, items)

    print('Gathering users data...')

    for user, item in tqdm(users_items):
        response = meli.get('/users/' + str(user))
        json_user_response = json.loads(response.content)
        json_user_response['item'] = item
        meli_users_json.append(json_user_response)


    with open('users-data.json', 'w') as fp:
        json.dump(meli_users_json, fp)
    print('users-data.json ready!')


def get_meli_phones_info(phones):
    """
    Genera un .json a partir de informacion extraida de items de la SDK de MercadoLibre
    """
    col_users = []
    col_items = []

    print('Gathering phones data...')
    meli_phones_json = []
    for phone in tqdm(phones):
        # Utilizo  offset por la limitacion de 50 registros del GET
        for offset in ['0', '50', '100']:
            response = meli.get('/sites/MLA/search?q=' + phone.name + '&limit=50&offset=' + offset)
            json_response = json.loads(response.content)
            for result in json_response['results']:
                result['item_name'] = phone.name
                col_users.append(result['seller']['id'])
                col_items.append(phone.name)
            meli_phones_json.append(json_response['results'])

    flat_list = [item for sublist in meli_phones_json for item in sublist]
    with open('phones-data.json', 'w') as fp:
        json.dump(flat_list, fp)

    return col_users, col_items


def get_specs_info(phones):
    """
    Genera un .json a partir de informacion extraida de phonearena.com
    """
    phones_list = []

    print('Gathering specs data...')
    for phone in tqdm(phones):
        categories_txt = []
        specs_txt = []

        res = requests.get(phone.url)
        soup = bs4.BeautifulSoup(res.text, 'lxml')

        # Me traigo solo los datos con clase 'category'
        categories = soup.select('.category')
        for category in categories:
            categories_txt.append(decode(category.text[1:]))
        # Filtro Memory porque phonearena la carga comk oculta y viene sin datos
        filter(lambda x: x != 'Memory', categories_txt)
        categories_txt.append('Name')

        # Filtro los specs
        specs = soup.select('.specs')
        for spec in specs:
            specs_txt.append(decode(spec.text))
        specs_txt.append(phone.name)

        # Meto todo en un diccionario con categoria como clave
        cat_specs_dict = dict(zip(categories_txt, specs_txt))

        phones_list.append(cat_specs_dict)

    with open('phones-specs.json', 'w') as fp:
        json.dump(phones_list, fp)

    print('phones-specs.json ready!')

def main():
    iphone_7 = Phone('Iphone 7', 'https://www.phonearena.com/phones/Apple-iPhone-7_id9815')
    samsung_s8 = Phone('Samsung s8', 'https://www.phonearena.com/phones/Samsung-Galaxy-S8_id10311')
    moto_x_style = Phone('Moto X Style', 'https://www.phonearena.com/phones/Motorola-Moto-X-Style_id9553')

    phones = [iphone_7, samsung_s8, moto_x_style]
    col_users, col_items = get_meli_phones_info(phones)
    get_meli_users_info(col_users, col_items)
    get_specs_info(phones)


if __name__ == "__main__":
    main()