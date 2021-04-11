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
    df.to_csv(path_or_buf='data/' + name, index=False)
