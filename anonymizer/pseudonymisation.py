import re
import secrets
import string
import pandas as pd
import datamanager


email_split_regex = re.compile(r'(.+)@(.+)\.(.+)')
reconstruct_regex = re.compile(r"'(.+)', '(.+)', '(.+)'")


def partition_email(email, local_part, domain_part, tld_part):
    """Egy email címet három részre oszt fel, a @ jel és a tld végződés előtt álló pont mentén."""
    email = str(email).lower()
    m = re.search(email_split_regex, email)
    if m:
        groups = m.groups()
    else:
        groups = ("nan", "na", "n")
    local_part.update({groups[0]: ''})
    domain_part.update({groups[1]: ''})
    tld_part.update({groups[2]: ''})
    return str(groups)


def generate_text(hossz) -> str:
    """A paraméterben kapott hosszúságú szöveget generál."""
    alphabet = string.ascii_letters + string.digits
    text = ''.join(secrets.choice(alphabet) for i in range(hossz))
    return text


def generate_secret_text(p_set, p_dictionary, length):
    """A paraméterben kapott set-et tölti fel elemekkel a generate_text függvény hívásával addig, amíg nincs annyi
    eleme, mint a paraméterben kapott szótárnak."""
    while len(p_set) < len(p_dictionary):
        p_set.add(generate_text(length))


def add_value_to_dict(p_dict, p_set):
    """A paraméterben kapott szótárhoz hozzárendeli a paraméterben kapott halmaz elemeit."""
    for key, value in p_dict.items():
        p_dict[key] = p_set.pop()


def reconstruct_email(text, local_part, domain_part, tld_part) -> str:
    """A paraméterben kapott szótárak alapján a pszeudonimizált verzióra írja át a szöveget."""
    m = re.search(reconstruct_regex, text)
    if m:
        groups = m.groups()
        reconstructed = str(local_part.get(groups[0])) + "@" + str(domain_part.get(groups[1])) + "." + str(tld_part.get(
            groups[2]))
        return reconstructed
    else:
        return None


def email_multi_pseudonymise(workdata, column):
    """A paraméterben kapott DataFrame paraméterben kapott oszlopában szereplő email címeket pszeudonimizálja a
    megfelelő függvények meghívásával. Az email cím három részre bontódik, és mindegyik rész külön kerül
    pszeudonimizálásra. """

    # a szótárakba kerülnek kulcsként az egyes email cím részek unique értékei
    local_part = dict()  # az email cím @ jel előtt álló része
    domain_part = dict()  # az email cím domain része, nem számítva a tld végződést
    tld_part = dict()  # az email cím tld végződése

    # a halmazok garantálják, hogy egy pszeudonimizált szöveg ne tartozhasson több eredeti értékhez
    pseudo_local = set()
    pseudo_domain = set()
    pseudo_tld = set()

    # a szótárak kulcsainak feltöltése
    workdata.df[column] = workdata.df[column].apply(lambda x: partition_email(x, local_part, domain_part, tld_part))

    # a pszeudonimizált szövegváltozatok generálása
    generate_secret_text(pseudo_local, local_part, 10)  # 10 hosszú szöveg generálása
    generate_secret_text(pseudo_domain, domain_part, 5)  # 5 hosszú szöveg generálása
    generate_secret_text(pseudo_tld, tld_part, 4)  # 4 hosszú szöveg generálása a tld

    # a szótár kulcsokhoz a halmazbeli értékek hozzárendelése
    add_value_to_dict(local_part, pseudo_local)
    add_value_to_dict(domain_part, pseudo_domain)
    add_value_to_dict(tld_part, pseudo_tld)

    # az eredeti email címek átírása a szótár alapján a pszeudonimizált változatra
    workdata.df[column] = workdata.df[column].apply(lambda x: reconstruct_email(x, local_part, domain_part, tld_part))


# def text_to_number(df, column: str):
def text_to_number(workdata, column: str):
    """
    A DataFrame adott oszlopában szereplő értékeket cseréli ki számokra, az inkrementálás módszerét használva. Az
    egymással megegyező adatoknak a pszeudonimizált számértéke is megegyezik.
    :param workdata: a WorkData példány
    :param column: az oszlop neve
    :return:
    """
    workdata.df[column] = pd.factorize(workdata.df[column])[0]


def number_to_interval(workdata, column: str, distance=10):
    """
    A DataFrame paraméterben adott oszlopában található számokat sorolja be egy intervallumba. Az intervallum távolságot
    a distance paraméter tartalamzza. Pozitív számokra működik.
    :param workdata: a WorkData példány
    :param column: az oszlop neve
    :param distance: az intervallum távolság
    :return:
    """
    maximum = workdata.df[column].max()  # az oszlopban szereplő legnagyobb érték

    # a címkék létrehozása, 0-tól a maximum értékig, megadott távolsággal
    labels = ["{0} - {1}".format(i, i + distance - 1) for i in range(0, maximum, distance)]
    # oszlop átírása a címkéknek megfelelően
    workdata.df[column] = pd.cut(workdata.df[column], range(0, maximum + distance, distance), right=False, labels=labels)
    workdata.df[column] = workdata.df[column].astype("category")  # kategorikus adatttípusra állítja az oszlopot
    workdata.categorical.add(column)
    workdata.feature_columns.remove(column)


def generalize_country_to_region(
        workdata,
        column: str,
        countries=pd.read_csv(
            'https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.csv',
            usecols=['name', 'alpha-2', 'alpha-3', 'region'])
):
    """
    A DataFrame adott oszlopában lévő országneveket és kódokat cseréli le annak a régiónak a nevére,
    ahol az ország található.
    :param workdata: a WorkData példány, ami a DataFramet tartalmazza
    :param column: az oszlop neve
    :param countries: az országokat, kódokat, és régiókat tartalmazó file
    :return:
    """
    reshaped = pd.lreshape(countries,
                           {'country': ['name', 'alpha-2', 'alpha-3'], 'region': ['region', 'region', 'region']},
                           dropna=False)
    dictionary = dict(zip(reshaped['country'], reshaped['region']))
    workdata.df[column] = workdata.df[column].map(dictionary)


# az egyes címkékhez tartozó pszeudonimizáló függvények
labels_and_psudonymisation_functions = {
    'country or region': generalize_country_to_region,
    'human age': number_to_interval,
    'email address': email_multi_pseudonymise
}


def auto_pseudonymise_by_label(workdata, labels_df=datamanager.read_labels_file()):
    """
    A DataFrame azon oszlopait pszeudonimizálja a megfelelő függvények hívásával, ahol az oszlopnév címkéjéhez létezik
    specializált pszeudonimizáló függvény.
    :param workdata: a WorkData példány
    :param labels_df: a címkéket tartalmazó DataFrame
    :return:
    """
    filtered = labels_df[labels_df['name'].isin(workdata.df.columns.values)]
    filtered = filtered.to_dict('records')
    for i in filtered:
        for j, func in labels_and_psudonymisation_functions.items():
            if j == i['type']:
                func(workdata, workdata.df[i['name']].name)


def auto_pseudonymise_id_data(workdata, labels_df=datamanager.read_labels_file()):
    """
    Pszeudonimizálja a DataFrame azon oszlopait, amelyek címkéihez nem létezik specializált pszeudonimizáló függvény.
    Ilyenkor a text_to_number() függvény hívódik meg.
    :param workdata: a WorkData példány
    :param labels_df: a címkéket tartalmazó DataFrame
    :return:
    """
    filtered = labels_df[labels_df['name'].isin(workdata.df.columns.values)]
    filtered = filtered.to_dict('records')
    for i in filtered:
        if i['identifier'] == True and i['type'] not in labels_and_psudonymisation_functions:
            text_to_number(workdata, i['name'])
