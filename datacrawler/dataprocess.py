import pandas as pd
import numpy as np
from unidecode import unidecode

# TODO scrapy futtatas elott torolni kell az uj.json filet, mert maskepp a regi filehoz fuzi az ujat
# TODO scrapy futtatas scriptbol
# scrapy futtatas: koronavirus mappabol => scrapy crawl koronavirus -o uj.json


def process_disease_hu():

    unique_values = set()
    diseases = pd.read_json('koronavirus/uj.json')
    diseases['alapbetegsegek'].apply(lambda x: unique_values.update(x))

    column = pd.Series(list(unique_values))

    column = column.str.lower()
    column = column.str.strip()
    column = column.apply(lambda x: unidecode(x))
    column.replace("", np.nan, inplace=True)
    column.dropna(inplace=True)

    column = column.drop_duplicates()
    column = column.sort_values()
    column.to_csv(path_or_buf='../data/local/diseases_hungarian.csv', index=False)


process_disease_hu()
