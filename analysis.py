import pandas as pd


def unique_percentage(df):
    """Visszaadja, hogy a paraméterben kapott DataFrame egyes oszlopai milyen valószínűséggel azonosítják az egyént.
    Kiszámítja az oszlop unique értékei számának és az oszlop összes eleme számának a hányadosát, százalékos értéket
    visszaadva. Minél magasabb a százalék, az oszlop annál egyedibb értékekkel rendelkezik. """
    diversity = dict()

    for col in list(df):
        diversity[col] = len(df[col].unique())

    diversity_series = pd.Series(diversity)
    return 100 * diversity_series / len(df)
