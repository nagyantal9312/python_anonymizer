import pandas as pd
from anonymizer import anonymisation, pseudonymisation, datamanager, detection
from datamanager import WorkData

column_names = tuple()
sensitive_column = ''
categorical = set()

P = 0.2
L = 2
K = 3
func = 'l'

column_names = (
    'nev', 'kor', 'email', 'telefonszam', 'bankszamla', 'rendszam', 'idopont', 'koord1', 'koord2'
)
sensitive_column = 'nev'
df = pd.read_csv('data/test.csv', index_col=False, header=None, names=column_names)
categorical = {'nev',
               'email',
               'telefonszam',
               'bankszamla',
               'rendszam',
               'idopont'
               }


testclass = WorkData(df, sensitive_column, K, L, P, categorical=categorical)


# datamanager.replace_nan_values(df, categorical) # ezt azelott kell megcsinalni, mielott a kategoriakat hozzarendelem a tablazathoz, mert kesobb nem fogja engedni a modositast


def auto_anon_and_pseud(workdata: WorkData, func: str):

    labels_csv = detection.find_and_label(workdata.df, datamanager.read_labels_file())
    workdata.feature_columns = list(labels_csv['name'].unique())

    if workdata.sensitive_column in workdata.feature_columns:
        workdata.feature_columns.remove(workdata.sensitive_column)

    pseudonymisation.auto_pseudonymise_by_label(workdata, labels_csv)

    for name in workdata.categorical:
        workdata.df[name] = workdata.df[name].astype('category')

    workdata.df = anonymisation.anonymise_dataset(workdata, func)
    pseudonymisation.auto_pseudonymise_id_data(workdata, labels_csv)

    workdata.df.to_csv(path_or_buf='data/output/outputtest.csv', index=False)
    return workdata.df


if __name__ == "__main__":
    print("Welcome to Python Anonymizer")
    print(testclass)
    test = auto_anon_and_pseud(testclass, func)
    print("Called anonymisation function: {}".format(func))
