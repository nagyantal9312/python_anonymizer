import pandas as pd


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


def write_dataset_to_file(df, name):
    df.to_csv(path_or_buf='data/output/' + name, index=False)


def read_labels_file():
    return pd.read_csv('data/local/labels.csv', index_col=None, dtype={'identifier': 'boolean'})


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
