import PySimpleGUI as sg
from typing import Dict
import numpy as np
import re
from bs4 import BeautifulSoup
import requests


def build_url(search_params: Dict[str, str]) -> str:
    ebay_base_url = "https://www.ebay.com/sch/i.html?_from=R40"
    search_url = ebay_base_url + search_params['search_query']
    if search_params['used']:
        search_url = search_url + "&LH_ItemCondition=3000"
    if search_params['bin']:  # buy it now
        search_url = search_url + '&LH_BIN=1'
    if search_params['sold']:
        search_url = search_url + search_params['sold']
    search_url = search_url + '&rt=nc'  # added at the end of most urls by eBay regardless of other params
    if search_params['min'] != '':  # param for min price
        search_url = search_url + "&_udlo=" + search_params['min']

    return search_url


def parse_price_data(bs_data):
    price_data = []
    for gpu_price in bs_data.find_all('span', class_='s-item__price'):
        # strips out non-numerical characters from pricing
        formatted_price = re.sub("[^\d\.]", "", gpu_price.text)
        formatted_price = float(formatted_price)
        price_data.append(formatted_price)
    price_data = np.array(price_data) # convert to NumPy array

    return price_data

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
        source = requests.get(url).text
        soup = BeautifulSoup(source, 'lxml')
        price_array = parse_price_data(soup)
window.close()
print(values)
