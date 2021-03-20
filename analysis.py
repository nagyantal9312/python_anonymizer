import pandas as pd
import itertools


def unique_percentage(df):
    """
    Visszaadja, hogy a paraméterben kapott DataFrame egyes oszlopai mekkora valószínűséggel azonosítják az egyént.
    Kiszámítja az oszlop unique értékei számának és az oszlop összes eleme számának a hányadosát, százalékos értéket
    visszaadva. Minél magasabb a százalék, az oszlop annál egyedibb értékekkel rendelkezik.
    :param df: a DataFrame
    :return: a DataFrame oszlopai és a hozzájuk tartozó százalék értékek
    """
    diversity = dict()

    for col in list(df):
        diversity[col] = len(df[col].unique())

    diversity_series = pd.Series(diversity)
    return 100 * diversity_series / len(df)


def combinations_unique_percentage(df, columns: list):
    """
    Visszaadja, hogy a paraméterben kapott DataFrame paraméterben kapott oszlopainak összes lehetséges kombinációi
    mekkora valószínűséggel azonosítják az egyént. Az oszlopok kombinációiban kiszámítja az egyedi sorok és az összes
    sor hányadosát, százalékos értéket visszaadva. Minél magasabb a százalék, az oszlopkombináció annál egyedibb
    értékekkel rendelkezik.
    :param df: a DataFrame
    :param columns: a kombinálandó oszlopok listája
    :return: a kombinált oszlopok és a hozzájuk tartozó százalék érték
    """
    # a lista elemeit az összes lehetséges módon kombinálja
    combinations = []
    for i in range(len(columns)):
        oc = itertools.combinations(columns, i + 1)
        for c in oc:
            combinations.append(list(c))

    diversity = dict()
    for i in combinations:
        key = ', '.join(map(str, i))
        diversity[key] = len(df[i].drop_duplicates()) / len(df) * 100

    diversity_series = pd.Series(diversity)
    return diversity_series



