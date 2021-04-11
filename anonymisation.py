import pandas as pd


def get_spans(df, partition, categorical, scale=None):
    """
    A DataFrame minden oszlopára vonatkozóan visszaad egy értéket. Folytonos értékeket tartalmazó oszlop esetén a
    paraméterben kapott sorokban szereplő legnagyobb és legkisebb értékek különbségét, kategorikus értékeket tartalmazó
    oszlop esetén pedig a paraméterben kapott sorokban szereplő egyedi értékek számát.
    :param df: a DataFrame
    :param partition: a DataFrame sorai
    :param categorical: a DataFrame kategorikus oszlopai
    :param scale: ha meg van adva, akkor ezzel elosztódnak az egyébként kapott értékek
    :return: szótár, ami az oszlopokhoz kiszámított értékeket tartalmazza
    """
    spans = {}
    for column in df.columns:
        if column in categorical:
            span = len(df[column][partition].unique())
        else:
            span = df[column][partition].max() - df[column][partition].min()
        if scale is not None:
            span = span / scale[column]
        spans[column] = span
    return spans


def split(df, partition, categorical, column):
    """
    A kapott partíciót két részre vágja a vizsgált oszlopban szereplő értékek szerint. Ha a vizsgált oszlop folytonos
    értékeket tartalmaz, akkor a medián alattiak egy csoportba, a mediánnál nagyobb vagy egyenlő értékek pedig egy másik
    csoportba kerülnek. Ha a vizsgált oszlop kategorikus értékeket tartalmaz, akkor sorrend szerint vág.
    :param df: a DataFrame
    :param partition: a DataFrame sorai
    :param categorical: a DataFrame kategorikus oszlopai
    :param column: a vizsgált oszlop
    :return: a részekre vágott partíció
    """
    dfp = df[column][partition]
    if column in categorical:
        values = dfp.unique()
        lv = set(values[:len(values) // 2])
        rv = set(values[len(values) // 2:])
        return dfp.index[dfp.isin(lv)], dfp.index[dfp.isin(rv)]
    else:
        median = dfp.median()
        dfl = dfp.index[dfp < median]
        dfr = dfp.index[dfp >= median]
        return dfl, dfr


def is_k_anonymous(df, partition, sensitive_column, k=3):
    """
    Megmondja, hogy teljesül-e a k-anonimitás az adott partícióra.
    :param df: a DataFrame
    :param partition: a DataFrame egy partíciója
    :param sensitive_column: a DataFrame szenzitív oszlopa
    :param k: a k szám
    :return: True ha a partícióban legalább  k darab elem van, False ha kevesebb
    """
    if len(partition) < k:
        return False
    return True


def is_l_diverse(df, partition, sensitive_column, l=5):
    """
    Megmondja, hogy teljesül-e az l-diverzitás.
    :param df: a DataFrame
    :param partition: a DataFrame partíciója
    :param sensitive_column: a DataFrame szenzitív oszlopa
    :param l: az egyedi értékek száma
    :return: True, ha legalább l darab egyedi érték van a szenzitív oszlopban a partíción belül, False ha kevesebb van
    belőle
    """
    return diversity(df, partition, sensitive_column) >= l


def is_t_close(df, partition, sensitive_column, categorical, global_freqs, p=0.2):
    """
    Megmondja, hogy teljesül-e a t-közeliség.
    :param df: a DataFrame
    :param partition: a DataFrame egy partíciója
    :param sensitive_column: a DataFrame egy szenzitív oszlopa
    :param categorical: a DataFrame kategorikus oszlopai
    :param global_freqs: az eredeti DataFrame értékeinek eloszlása
    :param p: a szám, amire nézve viszonyítunk
    :return: True ha partícióban szereplő legnagyobb eloszlás érték legfeljebb akkora, mint a p szám, False ha nagyobb
    nála
    """
    if sensitive_column not in categorical:
        raise ValueError("This method only works for categorical values")
    # t-közeli, ha az adott partícióban szereplő legnagyobb eloszlási érték <= mint a paraméteres érték
    # hiszen minél nagyobb egy érték eloszlása annál inkább kiemelkedik a tömegből
    return t_closeness(df, partition, sensitive_column, global_freqs) <= p


def partition_dataset(df, feature_columns, sensitive_column, categorical, scale, is_valid):
    """
    Partíciókra vágja a DataFramet.
    :param df: a DataFrame
    :param feature_columns: a DataFrame megváltoztatandó oszlopai
    :param sensitive_column: a DataFrame nem megváltoztatandó oszlopa
    :param categorical: a DataFrame kategorikus oszlopai
    :param scale: az get_spans() függvény számára átadott paraméter
    :param is_valid: validációs függvény, pl. k-anonimitás, l-diverzitás, t-közeliség
    :return: a partícionált DataFrame
    """
    finished_partitions = []
    partitions = [df.index]
    while partitions:
        partition = partitions.pop(0)
        spans = get_spans(df[feature_columns], partition, categorical, scale)
        for column, span in sorted(spans.items(), key=lambda x: -x[1]):
            lp, rp = split(df, partition, categorical, column)
            if not is_valid(df, lp, sensitive_column) or not is_valid(df, rp, sensitive_column):
                continue
            partitions.extend((lp, rp))
            break
        else:
            finished_partitions.append(partition)
    return finished_partitions


def build_anonymized_dataset(df, partitions, feature_columns, categorical, max_partitions=None):
    """
    Létrehozza az anonimizált DataFramet.
    :param df: a DataFrame
    :param partitions: a partícionált DataFrame
    :param feature_columns: a DataFrame megváltoztatandó oszlopai
    :param categorical: a DataFrame kategorikus oszlopai
    :param max_partitions: ha meg van adva, akkor maximum ennyi részre osztható a DataFrame
    :return: az anonimizált DataFrame
    """
    anonymized_df = pd.DataFrame(columns=df.columns)
    for i, partition in enumerate(partitions):
        if max_partitions is not None and i > max_partitions:
            break

        df_part = df.loc[partition]
        # a d szótár tartalmazza a kulcs-érték párokat, ami alapján az átírás történik
        d = {c: i for i, c in enumerate(feature_columns)}

        # folytonos oszlop esetén az értékek átlagára íródik át a partíció összes értéke az oszlopban, kategorikus
        # oszlop esetén pedig a partíció adott oszlopában szereplő értékek egymástól a ',' karakterrel elválasztott
        # felsorolására
        for j in feature_columns:
            if j in categorical:
                d[df_part[j].name] = '|'.join(map(str, df_part[j].unique()))
            else:
                datatype = type(d[df_part[j].name])
                d[df_part[j].name] = datatype(df_part[j].mean())

        for key, value in d.items():
            df_part[key] = value
        anonymized_df = anonymized_df.append(df_part)
    return anonymized_df


def diversity(df, partition, column):
    """
    Visszaadja hogy a DataFrame adott oszlopában a DataFrame egy partíciójára nézve hány darab egyedi érték található.
    :param df: a DataFrame
    :param partition: a DataFrame egy partíciója
    :param column: a DataFrame egy oszlopa
    :return: az egyedi értékek száma
    """
    return len(df[column][partition].unique())


def get_global_freqs(df, sensitive_column):
    """
    A DataFrame szenzitív oszlopában szereplő egyedi értékek eloszlását adja vissza.
    :param df: a DataFrame
    :param sensitive_column: a DataFrame
    :return: az egyedi értékek és a hozzájuk tartozó eloszlás
    """
    global_freqs = {}
    total_count = float(len(df))
    group_counts = df.groupby(sensitive_column)[sensitive_column].agg('count')
    for value, count in group_counts.to_dict().items():
        p = count / total_count
        global_freqs[value] = p
    return global_freqs


def t_closeness(df, partition, column, global_freqs):
    """
    A partícióban szereplő értékek eloszlása közül visszaadja a legnagyobbat.
    :param df: a DataFrame
    :param partition: a DataFrame egy partíciója
    :param column: a DataFrame egy oszlopa
    :param global_freqs: az eredeti DataFrameben szereplő értékek eloszlása
    :return: a legnagyobb eloszlás érték
    """
    total_count = float(len(partition))
    d_max = None
    group_counts = df.loc[partition].groupby(column)[column].agg('count')
    for value, count in group_counts.to_dict().items():
        p = count / total_count
        d = abs(p - global_freqs[value])
        if d_max is None or d > d_max:
            d_max = d
    return d_max
