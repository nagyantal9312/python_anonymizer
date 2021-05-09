import pandas as pd
from unidecode import unidecode


def replace_nan_values(df, categorical):
    """
    A kapott DataFrameben szereplő nan értékeket cseréli le, kategorikus értékeket tartalmazó oszlop esetén a
    'MISSING DATA' stringre, folytonos értékeket tartalmazó oszlop esetén a nem nan értékű cellák mediánjára.
    :param df: a DataFrame
    :param categorical: a DataFrame kategorikus oszlopai
    :return:
    """
    for i in list(df):
        if df[i].name in categorical:
            df[i] = df[i].replace(pd.NA, "MISSING DATA")
        else:
            df[i].fillna(value=df[i].median(), inplace=True)


def read_labels_file():
    return pd.read_csv('data/local/labels.csv', index_col=None, dtype={'identifier': 'boolean'})


def read_hungarian_names():
    female_names = pd.read_csv(filepath_or_buffer="http://www.nytud.mta.hu/oszt/nyelvmuvelo/utonevek/osszesnoi.txt",
                               delimiter="\n", encoding="ISO-8859-1")
    male_names = pd.read_csv(filepath_or_buffer="http://www.nytud.mta.hu/oszt/nyelvmuvelo/utonevek/osszesffi.txt",
                             delimiter="\n", encoding="ISO-8859-1")
    females = female_names[female_names.columns[0]].str.lower().apply(unidecode)
    males = male_names[male_names.columns[0]].str.lower().apply(unidecode)
    males = males.append(females)
    return males


def read_countries():
    # TODO unidecode because of Aland
    # TODO republic of ... etc removal
    countries = pd.read_csv(
        'https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.csv',
        usecols=['name', 'alpha-2', 'alpha-3'])
    countries['name'] = countries['name'].replace(to_replace=r'[ ]\(.*?\)', value="", regex=True)
    countries = countries.stack().str.lower()
    return countries


def read_diseases():
    diseases = pd.read_csv("data/local/21.02_disease_list.csv", usecols=["disease_full_name"])
    diseases_series = diseases[diseases.columns[0]].str.lower()
    return diseases_series


def read_hungarian_diseases():
    hungarian_diseases = pd.read_csv('data/local/diseases_hungarian.csv')
    return hungarian_diseases


class WorkData:
    def __init__(self, df: pd.DataFrame, sensitive_column: str, k: int, ldiv: int = None, p: float = None,
                 column_names: tuple = None, categorical: set = None, feature_columns=None):
        self.df = df
        self.sensitive_column = sensitive_column
        self.k = k
        self.ldiv = ldiv
        self.p = p
        if column_names is None:
            self.column_names = set(df.columns)
        else:
            self.column_names = column_names
        # TODO itt is ellenorizni a None erteket
        self.categorical = categorical
        if feature_columns is None:
            self.feature_columns = list(self.column_names)
            self.feature_columns.remove(sensitive_column)
        else:
            self.feature_columns = feature_columns

    def __str__(self):
        return ("Column names: {}\nCategorical columns: {}\nSensitive column: {}\nFeature columns: {}\nK: {}\nL: {}\nP: {}\n"
                .format(self.column_names, self.categorical, self.sensitive_column, self.feature_columns, self.k, self.ldiv, self.p)
                )
