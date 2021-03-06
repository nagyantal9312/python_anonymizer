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
        diseases=datamanager.read_diseases()
):
    """
    A param??terben kapott Series egyes ??rt??kei betegs??gnevek e.
    :param param: az ellen??rzend?? series
    :param diseases: a betegs??geket tartalmaz?? csv. Forr??s: https://www.targetvalidation.org/downloads/data
    :return: egy Series, ahol az ??rt??k True: ha betegs??gn??v, False: egy??bk??nt
    """
    param = param.str.lower()
    return param.isin(diseases)


def is_disease_hungarian(
        param,
        diseases_hu=datamanager.read_hungarian_diseases()
):
    """
    A param??terben kapott Series egyes ??rt??kei magyar betegs??gnevek e.
    :param param: az ellen??rzend?? Series
    :param diseases_hu: a betegs??geket tartalmaz?? csv. Forr??s: https://koronavirus.gov.hu/elhunytak
    :return: egy Series, ahol az ??rt??k True: ha magyar betegs??gn??v, False: egy??bk??nt
    """
    param = param.str.lower().apply(unidecode)
    return param.isin(diseases_hu['0'])


def is_tax_number_hungarian(param):
    """
    A param??terben kapott Series egyes ??rt??kei magyar ad??sz??mok e.
    :param param: az ellen??rzend?? Series
    :return: egy Series, ahol az ??rt??k True: ha magyar ad??sz??m, False: egy??bk??nt
    """
    def check_tax_number(par):
        """
        Az ad??sz??m ellen??rz??s??t v??gz?? bels?? f??ggv??ny. A magyar ad??azonos??t?? sz??mokban az els?? sz??mjegy a konstans 8, ami
        a mag??nszem??ly min??s??gre utal. A 2-6. sz??mjegyek a szem??ly sz??let??si id??pontja ??s az 1867. janu??r 1. k??z??tt
        eltelt napok sz??ma. A 7-9. sz??mjegyek az azonos napon sz??letettek megk??l??nb??ztet??s??re szolg??l?? v??letlenszer??en
        k??pzett sz??m. A 10. sz??mjegy az 1-9. sz??mjegyek felhaszn??l??s??val k??sz??tett ellen??rz?? ??sszeg: ezek ??rt??keit meg
        kell szorozni azzal, ah??nyadik helyet foglalj??k el az azonos??t??n bel??l. A kapott szorzatok ??sszeg??t el kell
        osztani 11-gyel, ??s az oszt??s marad??ka lesz a 10. sz??mjegy.
        :param par: az ellen??rzend?? ??rt??k
        :return: True: ha magyar ad??sz??m, False: egy??bk??nt
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
    A param??terben kapott Series egyes ??rt??kei magyar TAJ sz??mok e.
    :param param: az ellen??rzend?? Series
    :return: egy Series, ahol az ??rt??k True: ha magyar TAJ sz??m, False: egy??bk??nt
    """
    def check_taj_number(par):
        """
        A TAJ sz??m ellen??rz??s??t v??gz?? bels?? f??ggv??ny. A TAJ sz??m 9 sz??mjegyb??l ??ll, ebb??l az els?? 8 sz??mjegyet sorban
        osztj??k ki, a 9. sz??mjegy pedig ellen??rz?? ??sszeg. Ez ??gy k??pz??dik, hogy a p??ratlan sorsz??m?? sz??mejgyek ??rt??keit
        h??rommal, a p??ros sorsz??m??akat pedig h??ttel kell megszorozni. Az ??gy kapott sz??mokat ??ssze kell adni, majd az
        ??sszeget el kell osztani t??zzel, ??s az oszt??s marad??ka lesz 9. sz??mjegy.
        :param par: az ellen??rzend?? ??rt??k
        :return: True: ha magyar TAJ sz??m, False: egy??bk??nt
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
    A param??terben kapott Series egyes ??rt??kei magyar szem??lyi sz??mok e.
    :param param: az ellen??rzend?? Series
    :return: egy Series, ahol az ??rt??k True: ha magyar szem??lyi sz??m, False: egy??bk??nt
    """
    def check_personal_number(par):
        """
        A szem??lyi sz??m ellen??rz??st v??gz?? bels?? f??ggv??ny. A szem??lyi sz??m els?? sz??mjegye 1-8 k??z??tti ??rt??k lehet. Ut??na
        ????HHNN form??tumban a sz??let??si d??tum k??vetkezik. Ezt h??rom sz??mjegy k??veti, ami az ugyanakkor sz??letettek
        megk??l??nb??ztet??s??re szolg??l. A 11. sz??m egy ellen??rz?? ??sszeg, aminet k??t sz??m??t??si m??dja van. Az 1996.12.31
        el??tt sz??letettek eset??n az els?? 10 sz??mjegy ??rt??keit meg kell szorozni azzal a sz??mmal, ah??nyadik helyet
        elfoglalj??k a sorban. A kapott szorzatokat ??ssze kell adni, majd az ??sszeget el kell osztani 11-gyel, ??s az
        oszt??s marad??ka lesz a 11. sz??mjegy. Az 1996.12.31 ut??n sz??letettek eset??n annyi a v??ltoz??s, hogy meg van
        ford??tva teh??t az els?? sz??mjegyet kell 10-zel szorozni ... a tizediket pedig 1-gyel.
        :param par: az ellen??rzend?? ??rt??k
        :return: True: ha magyar szem??lyi sz??m, False: egy??bk??nt
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
    A param??terben kapott Series egyes ??rt??kei tartalmaznak e magyar keresztnevet.
    :param param: az ellen??rzend?? Series
    :param names: a neveket tartalmaz?? csv
    :return: egy Series, ahol az ??rt??k True: ha tartalmaz magyar keresztnevet, False: egy??bk??nt
    """
    param = param.str.lower().apply(unidecode)
    mask = param.apply(lambda x: any(item for item in names.values if item in x))
    return mask


def is_licence_plate_hungarian(param):
    """
    A param??terben kapott Series egyes ??rt??kei magyar rendsz??mok e.
    :param param: az ellen??rzend?? Series
    :return: egy Series, ahol az ??rt??k True: ha magyar rendsz??m, False: egy??bk??nt
    """
    param = param.str.lower()
    return param.str.match(licence_plate_regex)


def is_phone_number_hungarian(param):
    """
    A param??terben kapott Series egyes ??rt??kei magyar telefonsz??mok e.
    :param param: az ellen??rzend?? Series
    :return: egy Series, ahol az ??rt??k True: ha magyar telefonsz??m, False: egy??bk??nt
    """
    return param.str.match(phone_number_regex)


def is_mac_address(param):
    """
    A param??terben kapott Series egyes ??rt??kei MAC c??mek e.
    :param param: az ellen??rzend?? Series
    :return: egy Series, ahol az ??rt??k True: ha MAC c??m, False: egy??bk??nt
    """
    return param.str.match(mac_regex)


def is_email_address(param):
    """
    A param??terben kapott Series egyes ??rt??kei email c??mek e.
    :param param: az ellen??rzend?? Series
    :return: egy Series, ahol az ??rt??k True: ha email c??m, False: egy??bk??nt
    """
    return param.str.match(email_regex)


def is_ip_address(param):
    """
    A param??terben kapott Series egyes ??rt??kei IP c??mek e.
    :param param: az ellen??rzend?? Series
    :return: egy Series, ahol az ??rt??k True: ha IP c??m, False: egy??bk??nt
    """
    def check_ip(par):
        """
        Az IP c??m ellen??rz??st v??gz?? bels?? f??ggv??ny.
        :param par: az ellen??rzend?? ??rt??k
        :return: True: ha IP c??m, False: egy??bk??nt
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
    A param??terben kapott Series egyes ??rt??kei orsz??gnevek (angol), vagy 2-3 jegy?? orsz??gk??dok e.
    :param param: az ellen??rzend?? Series
    :param countries: a orsz??gokat ??s k??dokat tartalmaz?? csv
    :return: egy Series, ahol az ??rt??k True: orsz??gn??v vagy k??d, False: egy??bk??nt
    """
    return param.str.lower().isin(countries)


def is_human_age(param):
    """
    A param??terben kapott Series egyes ??rt??kei lehetnek e emberi ??letkorok. Feltehet??, hogy az emberi ??letkor 0 ??s 129
    ??v k??z??tti. A f??ggv??ny megvizsg??lja a Series (oszlop) nev??t, ??s csak akkor min??s??theti ??letkornak a Seriest, ha a
    n??v egy el??re meghat??rozott, nagy val??sz??n??s??ggel ??letkort tartalmaz?? oszlopn??v-lista elemei k??zt m??r szerepel.
    :param param: az ellen??rzend?? Series
    :return: egy Series, ahol az ??rt??k True: ha lehet emberi ??letkor, False: egy??bk??nt
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


# a keres?? f??ggv??nyek ??s a hozz??juk tartoz?? c??mk??k
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
    Megvizsg??lja a DataFramet ??s megmondja, hogy a program milyen t??pus?? adatokat tal??l benne. A c??mk??ket tartalmaz??
    filet b??v??ti az ??jonnan tal??lt c??mk??kkel.
    :param df: a vizsg??land?? DataFrame
    :param labels_frame: a DataFrame, ahov?? a c??mk??zett adatok ker??lnek
    :return: a tal??lt adatokkal kieg??sz??tett, c??mk??ket tartalmaz?? DataFrame
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
