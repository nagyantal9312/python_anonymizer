import pandas as pd
import datamanager
import anonymisation
import pseudonymisation
import analysis



column_names = tuple()
sensitive_column = ''
categorical = set()


P = 0.2
L = 5
K = 4

column_names = (
    'nev', 'kor', 'email', 'telefonszam', 'bankszamla', 'rendszam', 'idopont', 'koord1', 'koord2'
)
sensitive_column = 'nev'
df = pd.read_csv('data/ds2.csv', index_col=False, header=None, names=column_names)
categorical = {'nev',
               'email',
               'telefonszam',
               'bankszamla',
               'rendszam',
               'idopont'
               }

datamanager.replace_nan_values(df, categorical) # ezt azelott kell megcsinalni, mielott a kategoriakat hozzarendelem a tablazathoz, mert kesobb nem fogja engedni a modositast


for name in categorical:
    df[name] = df[name].astype('category')

feature_columns = list(df.columns.values)
feature_columns.remove(sensitive_column)


# pseudonymisation.email_multi_pseudonymise(df, 'email')
# pseudonymisation.text_to_number(df, df['nev'].name)
# pseudonymisation.number_to_interval(10, df['kor'].name, df)

full_spans = anonymisation.get_spans(df, df.index, categorical)

finished_partitions = anonymisation.partition_dataset(df, feature_columns, sensitive_column, categorical, full_spans,
                                                      (lambda *args: anonymisation.is_k_anonymous(*args, k=K)))

dfn = anonymisation.build_anonymized_dataset(df, finished_partitions, feature_columns, categorical)

finished_l_diverse_partitions = anonymisation.partition_dataset\
    (df, feature_columns, sensitive_column, categorical, full_spans,
     (lambda *args: anonymisation.is_k_anonymous(*args, k=K) and anonymisation.is_l_diverse(*args, l=L)))

dfl = anonymisation.build_anonymized_dataset(df, finished_l_diverse_partitions, feature_columns, categorical)

gf = anonymisation.get_global_freqs(df, sensitive_column)

finished_t_close_partitions = anonymisation.partition_dataset\
    (df, feature_columns, sensitive_column, categorical, full_spans,
    lambda *args: anonymisation.is_k_anonymous(*args, k=K) and anonymisation.is_t_close(*args, categorical, gf, p=P))

dft = anonymisation.build_anonymized_dataset(df, finished_t_close_partitions, feature_columns, categorical)

combinations = analysis.combinations_unique_percentage(df, column_names)


