import re
import secrets
import string
import pandas as pd


def partition_email(email, local_part, domain_part, tld_part):
    """Egy email címet három részre oszt fel, a @ jel és a tld végződés előtt álló pont mentén."""
    email = email.lower()
    m = re.search(r'(.+)@(.+)\.(.+)', email)
    if m:
        groups = m.groups()
        local_part.update({groups[0]: ''})
        domain_part.update({groups[1]: ''})
        tld_part.update({groups[2]: ''})
        return str(groups)
    else:
        return None


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
    m = re.search(r"'(.+)', '(.+)', '(.+)'", text)
    if m:
        groups = m.groups()
        reconstructed = str(local_part.get(groups[0])) + "@" + str(domain_part.get(groups[1])) + "." + str(tld_part.get(
            groups[2]))
        return reconstructed
    else:
        return None


#TODO: megcsinálni, hogy nan, és a kicserélt nan értékekre is illeszkedjen
def email_multi_pseudonymise(p_df, column):
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
    p_df[column] = p_df[column].apply(lambda x: partition_email(x, local_part, domain_part, tld_part))

    # a pszeudonimizált szövegváltozatok generálása
    generate_secret_text(pseudo_local, local_part, 10)  # 10 hosszú szöveg generálása
    generate_secret_text(pseudo_domain, domain_part, 5)  # 5 hosszú szöveg generálása
    generate_secret_text(pseudo_tld, tld_part, 4)  # 4 hosszú szöveg generálása a tld

    # a szótár kulcsokhoz a halmazbeli értékek hozzárendelése
    add_value_to_dict(local_part, pseudo_local)
    add_value_to_dict(domain_part, pseudo_domain)
    add_value_to_dict(tld_part, pseudo_tld)

    # az eredeti email címek átírása a szótár alapján a pszeudonimizált változatra
    p_df[column] = p_df[column].apply(lambda x: reconstruct_email(x, local_part, domain_part, tld_part))


def text_to_number(df, column):
    """A paraméterként kapott DataFrame paraméterben kapott oszlopában szereplő értékeket cseréli ki számokra,
    az inkrementálás módszerét használva. Az egymással megegyező adatoknak a pszeudonimizált számértéke is
    megegyezik. """
    df[column] = pd.factorize(df[column])[0]


def number_to_interval(distance, column, df):
    """A paraméterben kapott DataFrame paraméterben kapott oszlopában található számokat sorolja be egy
    intervallumba. Az intervallum távolságot a distance paraméter tartalamzza. Pozitív számokra működik."""

    maximum = df[column].max()  # az oszlopban szereplő legnagyobb érték

    # a címkék létrehozása, 0-tól a maximum értékig, megadott távolsággal
    labels = ["{0} - {1}".format(i, i + distance - 1) for i in range(0, maximum, distance)]
    # oszlop átírása a címkéknek megfelelően
    df[column] = pd.cut(df[column], range(0, maximum + distance, distance), right=False, labels=labels)
    df[column] = df[column].astype("category")  # kategorikus adatttípusra állítja az oszlopot
