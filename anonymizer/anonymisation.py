import pandas as pd
from datamanager import WorkData


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


def is_k_anonymous(workdata: WorkData, partition):
    """
    Megmondja, hogy teljesül-e a k-anonimitás az adott partícióra.
    :param workdata: a WorkData példány
    :param partition: a DataFrame egy partíciója
    :return: True ha a partícióban legalább  k darab elem van, False ha kevesebb
    """
    if len(partition) < workdata.k:
        return False
    return True


def is_l_diverse(workdata, partition):
    """
    Megmondja, hogy teljesül-e az l-diverzitás.
    :param workdata: a WorkData példány
    :param partition: a DataFrame partíciója
    :return: True, ha legalább l darab egyedi érték van a szenzitív oszlopban a partíción belül, False ha kevesebb van
    """
    return diversity(workdata.df, partition, workdata.sensitive_column) >= workdata.ldiv


def is_t_close(workdata, partition, global_freqs):
    """
    Megmondja, hogy teljesül-e a t-közeliség.
    :param workdata: a WorkData példány
    :param partition: a DataFrame egy partíciója
    :param global_freqs: az eredeti DataFrame értékeinek eloszlása
    :return: True ha partícióban szereplő legnagyobb eloszlás érték legfeljebb akkora, mint a p szám, False ha nagyobb
    """
    if workdata.sensitive_column not in workdata.categorical:
        raise ValueError("This method only works for categorical values")
    # t-közeli, ha az adott partícióban szereplő legnagyobb eloszlási érték <= mint a paraméteres érték
    # hiszen minél nagyobb egy érték eloszlása annál inkább kiemelkedik a tömegből
    return t_closeness(workdata.df, partition, workdata.sensitive_column, global_freqs) <= workdata.p


def partition_dataset(workdata, scale, is_valid):
    """
    Partíciókra vágja a DataFramet.
    :param workdata: a WorkData példány
    :param scale: a get_spans() függvény számára átadott paraméter
    :param is_valid: validációs függvény, pl. k-anonimitás, l-diverzitás, t-közeliség
    :return: a partícionált DataFrame
    """
    finished_partitions = []
    partitions = [workdata.df.index]
    while partitions:
        partition = partitions.pop(0)
        spans = get_spans(workdata.df[workdata.feature_columns], partition, workdata.categorical, scale)
        for column, span in sorted(spans.items(), key=lambda x: -x[1]):
            lp, rp = split(workdata.df, partition, workdata.categorical, column)
            if not is_valid(workdata, lp) or not is_valid(workdata, rp):
                continue
            partitions.extend((lp, rp))
            break
        else:
            finished_partitions.append(partition)
    return finished_partitions


def build_anonymized_dataset(workdata, partitions, max_partitions=None):
    """
    Létrehozza az anonimizált DataFramet.
    :param workdata: a WorkData példány
    :param partitions: a már partícionált DataFrame
    :param max_partitions: ha meg van adva, akkor maximum ennyi részre osztható a DataFrame
    :return:
    """
    anonymized_df = pd.DataFrame(columns=workdata.df.columns)
    for i, partition in enumerate(partitions):
        if max_partitions is not None and i > max_partitions:
            break

        df_part = workdata.df.loc[partition]
        # a d szótár tartalmazza a kulcs-érték párokat, ami alapján az átírás történik
        d = {c: i for i, c in enumerate(workdata.feature_columns)}

        # folytonos oszlop esetén az értékek átlagára íródik át a partíció összes értéke az oszlopban, kategorikus
        # oszlop esetén pedig a partíció adott oszlopában szereplő értékek egymástól a '|' karakterrel elválasztott
        # felsorolására
        for j in workdata.feature_columns:
            if j in workdata.categorical:
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


def anonymise_dataset(workdata: WorkData, func: str):

    full_spans = get_spans(workdata.df, workdata.df.index, workdata.categorical)

    if func == 'k':
        finished_partitions = partition_dataset(workdata, full_spans, (lambda *args: is_k_anonymous(*args)))
        df = build_anonymized_dataset(workdata, finished_partitions)

    elif func == 'l':
        finished_l_diverse_partitions = partition_dataset(workdata, full_spans, (
            lambda *args: is_k_anonymous(*args) and is_l_diverse(*args)
            )
        )
        df = build_anonymized_dataset(workdata, finished_l_diverse_partitions)

    elif func == 't':
        freqs = get_global_freqs(workdata.df, workdata.sensitive_column)
        finished_t_close_partitions = partition_dataset(
            workdata, full_spans, lambda *args: is_k_anonymous(*args) and is_t_close(*args, freqs)
        )
        df = build_anonymized_dataset(workdata, finished_t_close_partitions)

    return df
