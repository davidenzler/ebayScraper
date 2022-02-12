import re
from typing import Dict

import PySimpleGUI as sg
import mysql.connector
import numpy as np
import requests
from bs4 import BeautifulSoup
from mysql.connector import errorcode


def build_url(search_params: Dict[str, str]) -> str:
    ebay_base_url = "https://www.ebay.com/sch/i.html?_from=R40"
    # quick reminder: '\s' matches white space character
    search_query = re.sub(r'\s', '+', search_params['search_query'])
    search_url = ebay_base_url + '&_nkw=' + search_query
    if search_params['used']:
        search_url = search_url + "&_LH_ItemCondition=3000"
    if search_params['bin']:  # buy it now
        search_url = search_url + '&_LH_BIN=1'
    if search_params['sold']:
        search_url = search_url + '&_LH_Sold=1&LH_Complete=1'
    search_url = search_url + '&_rt=nc&_ipg=240'  # added at the end of most urls by eBay regardless of other params
    if search_params['min'] != '':  # param for min price
        search_url = search_url + "&_udlo=" + search_params['min']

    return search_url


def parse_price_data(bs_data):
    price_data = []
    gpu_prices = bs_data.find('ul', class_='srp-results srp-list clearfix')
    for gpu_price in gpu_prices.find_all('span', class_="s-item__price"):
        # strips out non-numerical characters from pricing
        formatted_price = re.sub("[^\d\.]", "", gpu_price.text)
        formatted_price = float(formatted_price)
        price_data.append(formatted_price)
    price_data = np.array(price_data) # convert to NumPy array

    return price_data


def query(url):
    headers = {
            'authority': 'www.ebay.com',
            'sec-ch-ua': '^\\^Google',
            'sec-ch-ua-mobile': '?0',
            'upgrade-insecure-requests': '1',
            'dnt': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'referer': 'https://www.yahoo.com',
            'accept-language': 'en-US,en;q=0.9',
        }
    with open('proxyinfo.txt', 'r') as f:
        username = f.readline()
        password = f.readline()
        port = f.readline()
    proxy_url = "http://{}-zone-residential-country-us:{}@zproxy.lum-superproxy.io:{}".format(username, password, port)
    proxies = {
        'http': proxy_url,
        'https': proxy_url,
    }
    return requests.get(url, proxies=proxies, headers=headers).text


sg.theme('Dark Amber')

# everything inside window
layout = [[sg.Text('Search Query: '), sg.InputText(key="search_query")],
          [sg.Checkbox('Used', key='used'), sg.Checkbox('BIN', key='bin'), sg.Checkbox('Sold', key='sold')],
          [sg.Text('Price Min: '), sg.InputText(key='min')],
          [sg.Button('Query'), sg.Button('Exit')]]

# generates window
window = sg.Window('eBay Price Scraper', layout)

while True:
    event, values = window.read()
    # values is map of with key=input fields and values=user entered input
    if event in (sg.WIN_CLOSED, 'Exit'):
        break
    elif event in 'Query':
        url = build_url(values)
        source = query(url)
        soup = BeautifulSoup(source, 'lxml')
        break
window.close()

price_array = parse_price_data(soup)
price_array = np.array(price_array)  # convert to numpy array
mean_price = np.mean(price_array).round(2)
median_price = np.median(price_array).round(2)
deviation = (np.std(price_array)).round(2)

# get DB Information
with open('connection.txt', 'r') as f:
    db_connection_info = []
    db_connection_info['user'] = f.readline()
    db_connection_info['pwd'] = f.readline()
    db_connection_info['host'] = f.readline()
    db_connection_info['db'] = f.readline()

try:
    db_connection = mysql.connector.connect(user=db_connection_info['user'],
                                            password=db_connection_info['pwd'],
                                            host=db_connection_info['host'],
                                            database=db_connection_info['db'])
    # everything inside window
    layout = [[sg.Text('Table to store info: '), sg.InputText(key="table")],
              [sg.Button('Submit'), sg.Button('Exit')]]

    # generates window
    window = sg.Window('Table Select', layout)
    while True:
        event, values = window.read()
        # values is map of with key=input fields and values=user entered input
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        elif event in 'Submit':
            add_pricing = ("INSERT INTO {} (mean, median, deviation) VALUES (%d, %d, %d))".format(values['table']))
            pricing_info = (mean_price, median_price, deviation)
            cursor = db_connection.cursor()
            cursor.execute(add_pricing, pricing_info)
            db_connection.commit()
            db_connection.close()
            break
    window.close()
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Your username or password is incorrect")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database cannot be found")
    else:
        print(err)
else:
    db_connection.close()
