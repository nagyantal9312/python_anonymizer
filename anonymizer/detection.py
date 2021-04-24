import re
import pandas as pd
from unidecode import unidecode
import ipaddress
import numpy as np
import datamanager

tax_regex = re.compile(r'^8[0-9]{9}$')
taj_regex = re.compile(r'^[0-9]{9}$')
personal_number_regex = re.compile(r'^[1-8]([0-9]{2})(0[1-9]|1[0-2])(0[1-9]|[1-2][0-9]|[3][0-1])[0-9]{4}$')
phone_number_regex = re.compile(r'^(?:(?:\+?3|0)6)(?:[-( ])?(?:[0-9]{1,2})(?:[-) ])?(?:[0-9]{3})[- ]?(?:[0-9]{3,4})$')
mac_regex = re.compile(r'^(([0-9A-Fa-f]{2}[-:. ]){5}[0-9A-Fa-f]{2})|(([0-9A-Fa-f]{4}[:. ]){2}[0-9A-Fa-f]{4})$')
email_regex = re.compile(r'^.+@.+\..+$')

# magyar rendszamokat felismero regex, a tema szempontjabol kevesbe jelentosek kikommentezhetok
licence_plate_regex = re.compile(
    r'^([a-z]{3}[- ]?[0-9]{3}'  # atlag rendszam: 3betu 3szam
    r'|[m][- ]?[0-9]{6}'  # mezogazdasagi: m betu es 6 szam
    r'|[a-z]{4}[- ]?[0-9][- ]?[0-9]'  # egyedi rendszam 4betu 2szam
    r'|[a-z]{5}[- ]?[0-9]'  # egyedi rendszam 5betu 1szam
    r'|[s][- ]?[a-z]{3}[- ]?[0-9]{3}'  # mopedautok
    r'|[s][p][- ]?[0-9]{2}[- ]?[0-9]{2}'  # versenyautok
    r'|[o][t][- ]?[0-9]{2}[- ]?[0-9]{2}'  # old timer, veteran jarmuvek
    r'|[epvz][- ]?[0-9]{5}'  # ideiglenes, proba, vamugyintezes alatt allo (be / ki)
    r'|[c][- ]?[cx][- ]?[0-9]{2}[- ]?[0-9]{2}'  # kulfoldi allampolgarok Mo-n uzemeltetett jarmuvei 2009.04.01 elott
    r'|[x][- ]?[abc][- ]?[0-9]{2}[- ]?[0-9]{2})$'  # berautok 2004.07.01 elott
    # r'|[c][d][- ]?[0-9]{3}[- ]?[0-9]{3}'  # diplomaciai testuletek hivatalos jarmuvei 2017.05.01 utan
    # r'|[c][k][- ]?[0-9]{2}[- ]?[0-9]{2}'  # konzuli testuletek diplomaciai mentesseget nem elvezo tagjainak jarmuvei
    # r'|[d][t][- ]?[0-9]{2}[- ]?[0-9]{2}' # diplomaciai testuletek hivatalos jarmuvei 2017.05.01 elott
    # r'|[h][c][- ]?[0-9]{2}[- ]?[0-9]{2}' # tiszteletbeli konzul, 2004.07.01 elott
    # r'|[c][d][- ]?[0-9]{2}[- ]?[0-9]{2}' # diplomaciai testuletek jarmuveinek az orszag vegleges elhagyasaval jaro hazaszallitasara hasznalt jarmuvei 2017.05.01 elott
    # r'|[h][abefiklmnprstvx][- ]?[0-9]{2}[- ]?[0-9]{2}' # honvedseg jarmuvei
    # r'|[m][a][- ]?[0-9]{2}[- ]?[0-9]{2}' # mentoszolgalat
    # r'|[r][a-z][- ]?[0-9]{2}[- ]?[0-9]{2}' # rendorseg
    # r'|[r]{2}[- ]?[0459][0-9][- ]?[0-9]{2}' # buntetesvegrehajtas
)


def is_disease(
        param,
        diseases=pd.read_csv("data/local/21.02_disease_list.csv", usecols=["disease_full_name"])
):
    """
    A paraméterben kapott Series egyes értékei betegségnevek e.
    :param param: az ellenőrzendő series
    :param diseases: a betegségeket tartalmazó csv. Forrás: https://www.targetvalidation.org/downloads/data
    :return: egy Series, ahol az érték True: ha betegségnév, False: egyébként
    """
    param = param.str.lower()
    diseases_series = diseases[diseases.columns[0]].str.lower()

    return param.isin(diseases_series)


def is_disease_hungarian(
        param,
        diseases_hu=pd.read_csv('data/local/diseases_hungarian.csv')
):
    """
    A paraméterben kapott Series egyes értékei magyar betegségnevek e.
    :param param: az ellenőrzendő Series
    :param diseases_hu: a betegségeket tartalmazó csv. Forrás: https://koronavirus.gov.hu/elhunytak
    :return: egy Series, ahol az érték True: ha magyar betegségnév, False: egyébként
    """
    param = param.str.lower().apply(unidecode)
    return param.isin(diseases_hu['0'])


def is_tax_number_hungarian(param):
    """
    A paraméterben kapott Series egyes értékei magyar adószámok e.
    :param param: az ellenőrzendő Series
    :return: egy Series, ahol az érték True: ha magyar adószám, False: egyébként
    """
    def check_tax_number(par):
        """
        Az adószám ellenőrzését végző belső függvény. A magyar adóazonosító számokban az első számjegy a konstans 8, ami
        a magánszemély minőségre utal. A 2-6. számjegyek a személy születési időpontja és az 1867. január 1. között
        eltelt napok száma. A 7-9. számjegyek az azonos napon születettek megkülönböztetésére szolgáló véletlenszerűen
        képzett szám. A 10. számjegy az 1-9. számjegyek felhasználásával készített ellenőrző összeg: ezek értékeit meg
        kell szorozni azzal, ahányadik helyet foglalják el az azonosítón belül. A kapott szorzatok összegét el kell
        osztani 11-gyel, és az osztás maradéka lesz a 10. számjegy.
        :param par: az ellenőrzendő érték
        :return: True: ha magyar adószám, False: egyébként
        """
        if not re.match(tax_regex, par):
            return False
        numbers = [int(x) for x in par]
        sum = 0
        for i in range(len(numbers) - 1):
            sum += numbers[i] * (i + 1)

        if sum % 11 != numbers[9]:
            return False
        return True

    mask = param.apply(lambda x: check_tax_number(x))
    return mask


def is_taj_number_hungarian(param):
    """
    A paraméterben kapott Series egyes értékei magyar TAJ számok e.
    :param param: az ellenőrzendő Series
    :return: egy Series, ahol az érték True: ha magyar TAJ szám, False: egyébként
    """
    def check_taj_number(par):
        """
        A TAJ szám ellenőrzését végző belső függvény. A TAJ szám 9 számjegyből áll, ebből az első 8 számjegyet sorban
        osztják ki, a 9. számjegy pedig ellenőrző összeg. Ez úgy képződik, hogy a páratlan sorszámú számejgyek értékeit
        hárommal, a páros sorszámúakat pedig héttel kell megszorozni. Az így kapott számokat össze kell adni, majd az
        összeget el kell osztani tízzel, és az osztás maradéka lesz 9. számjegy.
        :param par: az ellenőrzendő érték
        :return: True: ha magyar TAJ szám, False: egyébként
        """
        if not re.match(taj_regex, par):
            return False
        numbers = [int(x) for x in par]
        sum = 0
        for i in range(len(numbers) - 1):
            if i % 2 == 0 or i == 0:
                sum += numbers[i] * 3
            else:
                sum += numbers[i] * 7
        if sum % 10 != numbers[8]:
            return False
        return True

    mask = param.apply(lambda x: check_taj_number(x))
    return mask


def is_personal_number_hungarian(param):
    """
    A paraméterben kapott Series egyes értékei magyar személyi számok e.
    :param param: az ellenőrzendő Series
    :return: egy Series, ahol az érték True: ha magyar személyi szám, False: egyébként
    """
    def check_personal_number(par):
        """
        A személyi szám ellenőrzést végző belső függvény. A személyi szám első számjegye 1-8 közötti érték lehet. Utána
        ÉÉHHNN formátumban a születési dátum következik. Ezt három számjegy követi, ami az ugyanakkor születettek
        megkülönböztetésére szolgál. A 11. szám egy ellenőrző összeg, aminet két számítási módja van. Az 1996.12.31
        előtt születettek esetén az első 10 számjegy értékeit meg kell szorozni azzal a számmal, ahányadik helyet
        elfoglalják a sorban. A kapott szorzatokat össze kell adni, majd az összeget el kell osztani 11-gyel, és az
        osztás maradéka lesz a 11. számjegy. Az 1996.12.31 után születettek esetén annyi a változás, hogy meg van
        fordítva tehát az első számjegyet kell 10-zel szorozni ... a tizediket pedig 1-gyel.
        :param par: az ellenőrzendő érték
        :return: True: ha magyar személyi szám, False: egyébként
        """
        groups = re.search(personal_number_regex, par)
        if not groups:
            return False
        numbers = [int(x) for x in par]
        sum = 0
        if int(groups[1]) > 96:
            length = len(numbers)
            for i in range(length - 1):
                sum += numbers[i] * (length - 1)
                length -= 1
        else:
            for i in range(len(numbers) - 1):
                sum += numbers[i] * (i + 1)
        if sum % 11 != numbers[10]:
            return False
        return True

    mask = param.apply(lambda x: check_personal_number(x))
    return mask


def is_hungarian_name(
        param,
        names=datamanager.read_hungarian_names()
):
    """
    A paraméterben kapott Series egyes értékei tartalmaznak e magyar keresztnevet.
    :param param: az ellenőrzendő Series
    :param names: a neveket tartalmazó csv
    :return: egy Series, ahol az érték True: ha tartalmaz magyar keresztnevet, False: egyébként
    """
    param = param.str.lower().apply(unidecode)
    mask = param.apply(lambda x: any(item for item in names.values if item in x))
    return mask


def is_licence_plate_hungarian(param):
    """
    A paraméterben kapott Series egyes értékei magyar rendszámok e.
    :param param: az ellenőrzendő Series
    :return: egy Series, ahol az érték True: ha magyar rendszám, False: egyébként
    """
    param = param.str.lower()
    return param.str.match(licence_plate_regex)


def is_phone_number_hungarian(param):
    """
    A paraméterben kapott Series egyes értékei magyar telefonszámok e.
    :param param: az ellenőrzendő Series
    :return: egy Series, ahol az érték True: ha magyar telefonszám, False: egyébként
    """
    return param.str.match(phone_number_regex)


def is_mac_address(param):
    """
    A paraméterben kapott Series egyes értékei MAC címek e.
    :param param: az ellenőrzendő Series
    :return: egy Series, ahol az érték True: ha MAC cím, False: egyébként
    """
    return param.str.match(mac_regex)


def is_email_address(param):
    """
    A paraméterben kapott Series egyes értékei email címek e.
    :param param: az ellenőrzendő Series
    :return: egy Series, ahol az érték True: ha email cím, False: egyébként
    """
    return param.str.match(email_regex)


def is_ip_address(param):
    """
    A paraméterben kapott Series egyes értékei IP címek e.
    :param param: az ellenőrzendő Series
    :return: egy Series, ahol az érték True: ha IP cím, False: egyébként
    """
    def check_ip(par):
        """
        Az IP cím ellenőrzést végző belső függvény.
        :param par: az ellenőrzendő érték
        :return: True: ha IP cím, False: egyébként
        """
        try:
            ipaddress.ip_address(par)
            return True
        except ValueError:
            return False

    mask = param.apply(lambda x: check_ip(x))
    return mask


def is_country_or_region(
        param,
        countries=datamanager.read_countries()
):
    """
    A paraméterben kapott Series egyes értékei országnevek (angol), vagy 2-3 jegyű országkódok e.
    :param param: az ellenőrzendő Series
    :param countries: a országokat és kódokat tartalmazó csv
    :return: egy Series, ahol az érték True: országnév vagy kód, False: egyébként
    """
    return param.str.lower().isin(countries)


def is_human_age(param):
    """
    A paraméterben kapott Series egyes értékei lehetnek e emberi életkorok. Feltehető, hogy az emberi életkor 0 és 129
    év közötti. A függvény megvizsgálja a Series (oszlop) nevét, és csak akkor minősítheti életkornak a Seriest, ha a
    név egy előre meghatározott, nagy valószínűséggel életkort tartalmazó oszlopnév-lista elemei közt már szerepel.
    :param param: az ellenőrzendő Series
    :return: egy Series, ahol az érték True: ha lehet emberi életkor, False: egyébként
    """
    possible_column_names = {"age", "kor", "eletkor"}

    try:
        maximum = int(param.max())
        minimum = int(param.min())
    except (ValueError, TypeError):
        param.values[:] = False
        return param

    if param.name.lower() in possible_column_names and maximum < 130 and minimum >= 0:
        param.values[:] = True
    else:
        param.values[:] = False

    return param


# a kereső függvények és a hozzájuk tartozó címkék
functions_and_labels = {
    is_tax_number_hungarian: ['tax number hungarian', True],
    is_phone_number_hungarian: ['phone number hungarian', True],
    is_licence_plate_hungarian: ['licence plate hungarian', True],
    is_taj_number_hungarian: ['taj number hungarian', True],
    is_personal_number_hungarian: ['personal number hungarian', True],
    is_hungarian_name: ['hungarian first name', np.nan],
    is_disease: ['disease name', np.nan],
    is_disease_hungarian: ['disease name hungarian', np.nan],
    is_ip_address: ['ip address', np.nan],
    is_mac_address: ['mac address', np.nan],
    is_email_address: ['email address', True],
    is_country_or_region: ['country or region', np.nan],
    is_human_age: ['human age', np.nan]
}


def find_and_label(df, labels_frame):
    """
    Megvizsgálja a DataFramet és megmondja, hogy a program milyen típusú adatokat talál benne. A címkéket tartalmazó
    filet bővíti az újonnan talált címkékkel.
    :param df: a vizsgálandó DataFrame
    :param labels_frame: a DataFrame, ahová a címkézett adatok kerülnek
    :return: a talált adatokkal kiegészített, címkéket tartalmazó DataFrame
    """
    for i in list(df):
        for j in functions_and_labels:
            result = j(df[i].dropna().map(str))
            ratio = result.values.sum() / result.size

            if ratio > 0.0:
                new_row = pd.Series(
                    [i, ratio, functions_and_labels[j][0], functions_and_labels[j][1]],
                    index=labels_frame.columns)
                labels_frame = labels_frame.append(new_row, ignore_index=True)

                labels_frame = labels_frame.drop_duplicates(ignore_index=True)
                labels_frame.to_csv(path_or_buf='data/local/labels.csv', index=False)
    return labels_frame
