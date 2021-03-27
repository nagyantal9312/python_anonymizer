import re
import pandas as pd
from unidecode import unidecode

tax_regex = re.compile(r'^8[\d]{9}$')
taj_regex = re.compile(r'^[\d]{9}$')
personal_number_regex = re.compile(r'^[1-8]([\d]{2})(0[1-9]|1[0-2])(0[1-9]|[1-2][\d]|[3][0-1])[\d]{4}$')
mac_regex = re.compile(r'^(([0-9A-Fa-f]{2}[-:. ]){5}[0-9A-Fa-f]{2})|(([0-9A-Fa-f]{4}[:. ]){2}[0-9A-Fa-f]{4})$')

# magyar rendszamokat felismero regex, a tema szempontjabol kevesbe jelentosek kikommentezhetok
licence_plate_regex = re.compile(
    r'^([a-z]{3}[- ]?[0-9]{3}'  # atlag rendszam: 3betu 3szam
    r'|[m][- ]?[0-9]{6}'  # mezogazdasagi: m betu es 6 szam
    r'|[a-z]{4}[- ]?[0-9][- ]?[0-9]'  # egyedi rendszam 4betu 2szam
    r'|[a-z]{5}[- ]?[0-9]'  # egyedi rendszam 5betu 1szam
    r'|[s][- ]?[a-z]{3}[- ]?[0-9]{3}'  # mopedautok
    r'|[s][p][- ]?[0-9]{2}[- ]?[0-9]{2}'  # versenyautok
    r'|[o][t][- ]?[0-9]{2}[- ]?[0-9]{2}'  # old timer, veteran jarmuvek
    r'|[epvz][- ]?[0-9]{5}'  # ideiglenes, proba, vamugyintezes alatt allo (be / ki)
    r'|[c][- ]?[cx][- ]?[0-9]{2}[- ]?[0-9]{2}'  # kulfoldi allampolgarok Mo-n uzemeltetett jarmuvei 2009.04.01 elott
    r'|[x][- ]?[abc][- ]?[0-9]{2}[- ]?[0-9]{2})$'  # berautok 2004.07.01 elott
    # r'|[c][d][- ]?[0-9]{3}[- ]?[0-9]{3}'  # diplomaciai testuletek hivatalos jarmuvei 2017.05.01 utan
    # r'|[c][k][- ]?[0-9]{2}[- ]?[0-9]{2}'  # konzuli testuletek diplomaciai mentesseget nem elvezo tagjainak jarmuvei
    # r'|[d][t][- ]?[0-9]{2}[- ]?[0-9]{2}' # diplomaciai testuletek hivatalos jarmuvei 2017.05.01 elott
    # r'|[h][c][- ]?[0-9]{2}[- ]?[0-9]{2}' # tiszteletbeli konzul, 2004.07.01 elott
    # r'|[c][d][- ]?[0-9]{2}[- ]?[0-9]{2}' # diplomaciai testuletek jarmuveinek az orszag vegleges elhagyasaval jaro hazaszallitasara hasznalt jarmuvei 2017.05.01 elott
    # r'|[h][abefiklmnprstvx][- ]?[0-9]{2}[- ]?[0-9]{2}' # honvedseg jarmuvei
    # r'|[m][a][- ]?[0-9]{2}[- ]?[0-9]{2}' # mentoszolgalat
    # r'|[r][a-z][- ]?[0-9]{2}[- ]?[0-9]{2}' # rendorseg
    # r'|[r]{2}[- ]?[0459][0-9][- ]?[0-9]{2}' # buntetesvegrehajtas
)


def is_disease(param: str) -> bool:
    """
    A paraméterben kapott string tartalmaz e betegség nevet.
    :param param: az ellenőrzendő string
    :return: True: ha tartalmaz, False: egyébként
    """
    diseases = pd.read_csv("data/21.02_disease_list.csv", usecols=["disease_full_name"])

    param = param.lower()
    for i in diseases.iloc[:, 0].values:
        if i.lower() in param:
            return True

    return False


def is_tax_number_hungarian(param: str) -> bool:
    """
    A paraméterben kapott string lehet e valós magyar adóazonosító. A magyar adóazonosító számokban az első számjegy a
    konstans 8, ami a magánszemély minőségre utal. A 2-6. számjegyek a személy születési időpontja és az 1867. január 1.
    között eltelt napok száma. A 7-9. számjegyek az azonos napon születettek megkülönböztetésére szolgáló
    véletlenszerűen képzett szám. A 10. számjegy az 1-9. számjegyek felhasználásával készített ellenőrző összeg: ezek
    értékeit meg kell szorozni azzal, ahányadik helyet foglalják el az azonosítón belül. A kapott szorzatok összegét el
    kell osztani 11-gyel, és az osztás maradéka lesz a 10. számjegy.
    :param param: az ellenőrzendő string
    :return: True: ha valós magyar adóazonosító szám, False: egyébként
    """
    if not re.match(tax_regex, param):
        return False
    numbers = [int(x) for x in param]
    sum = 0
    for i in range(len(numbers) - 1):
        sum += numbers[i] * (i + 1)

    if sum % 11 != numbers[9]:
        return False
    return True


def is_taj_number_hungarian(param) -> bool:
    """
    A paraméterben kapott string lehet e valós magyar TAJ szám. A TAJ szám 9 számjegyből áll,
    ebből az első 8 számjegyet sorban osztják ki, a 9. számjegy pedig ellenőrző összeg. Ez úgy képződik,
    hogy a páratlan sorszámú számejgyek értékeit hárommal, a páros sorszámúakat pedig héttel kell megszorozni. Az így
    kapott számokat össze kell adni, majd az összeget el kell osztani tízzel, és az osztás maradéka lesz 9.
    számjegy.
    :param param: az ellenőrzendő string
    :return: True: ha valós magyar TAJ szám, False: egyébként
    """
    if not re.match(taj_regex, param):
        return False
    numbers = [int(x) for x in param]
    sum = 0
    for i in range(len(numbers) - 1):
        if i % 2 == 0 or i == 0:
            sum += numbers[i] * 3
        else:
            sum += numbers[i] * 7
    if sum % 10 != numbers[8]:
        return False
    return True


def is_personal_number_hungarian(param) -> bool:
    """
    A paraméterben kapott string lehet e valós magyar személyi szám. A személyi szám első számjegye 1-8 közötti érték
    lehet. Utána ÉÉHHNN formátumban a születési dátum következik. Ezt három számjegy követi, ami az ugyanakkor
    születettek megkülönböztetésére szolgál. A 11. szám egy ellenőrző összeg, aminet két számítási módja van.
    Az 1996.12.31 előtt születettek esetén az első 10 számjegy értékeit meg kell szorozni azzal a számmal,
    ahányadik helyet elfoglalják a sorban. A kapott szorzatokat össze kell adni, majd az összeget el kell osztani
    11-gyel, és az osztás maradéka lesz a 11. számjegy. Az 1996.12.31 után születettek esetén annyi a változás, hogy meg
    van fordítva tehát az első számjegyet kell 10-zel szorozni ... a tizediket pedig 1-gyel.
    :param param: az ellenőrzendő szám string alakban
    :return: True: ha valós magyar személyi szám, False: egyébként
    """
    groups = re.search(personal_number_regex, param)
    if not groups:
        return False
    numbers = [int(x) for x in param]
    sum = 0
    if int(groups[1]) > 96:
        length = len(numbers)
        for i in range(length - 1):
            sum += numbers[i] * (length - 1)
            length -= 1
    else:
        for i in range(len(numbers) - 1):
            sum += numbers[i] * (i + 1)
    if sum % 11 != numbers[10]:
        return False
    return True


def is_hungarian_name(param: str) -> bool:
    """
    A paraméterben kapott string tartalmaz e magyar keresztnevet.
    :param param: az ellenőrzendő string
    :return: True: ha tartalmaz, False: egyébként
    """
    param = unidecode(param.lower())
    female_names = pd.read_csv(filepath_or_buffer="http://www.nytud.mta.hu/oszt/nyelvmuvelo/utonevek/osszesnoi.txt",
                               delimiter="\n", encoding="ISO-8859-1")

    for i in female_names.iloc[:, 0].values:
        if unidecode(i.lower()) in param:
            return True

    male_names = pd.read_csv(filepath_or_buffer="http://www.nytud.mta.hu/oszt/nyelvmuvelo/utonevek/osszesffi.txt",
                             delimiter="\n", encoding="ISO-8859-1")

    for i in male_names.iloc[:, 0].values:
        if unidecode(i.lower()) in param:
            return True

    return False


def is_licence_plate_hungarian(param) -> bool:
    return True if re.match(licence_plate_regex, param.lower()) else False


def is_mac_address(param: str) -> bool:
    """
    A paraméterben kapott string MAC cím e.
    :param param: az ellenőrzendő string
    :return: True: ha MAC cím, False: egyébként
    """
    return True if re.match(mac_regex, param) else False
