from bs4 import BeautifulSoup
import requests
import numpy as np
import re

#pulls data from eBay
source = requests.get('https://www.ebay.com/sch/i.html?_from=R40&_nkw=rtx%202080%20ti&_sacat=0&LH_ItemCondition=3000&LH_Sold=1&LH_Complete=1&_ipg=200&LH_BIN=1&rt=nc&_udlo=200').text
soup = BeautifulSoup(source, 'lxml')
price_array = []

for gpu_price in soup.find_all('span', class_='s-item__price'):
    # strips out characters from pricing
    formatted_price = re.sub("[^\d\.]", "", gpu_price.text)
    formatted_price = float(formatted_price)

    price_array.append(formatted_price)

price_array = np.array(price_array)
mean_price = np.mean(price_array).round(2)
median_price = np.median(price_array).round(2)

print('Mean price: ${}'.format(mean_price))
print('Median price: ${}'.format(median_price))
print('Standard deviation: ${}'.format((np.std(price_array)).round(2)))
print('Minimum price: ${}'.format((np.amin(price_array)).round(2)))

#TODO store the price calculations along with an ID in a database / Pandas DataFrame
