# Python anonymizer

## Tartalom
* [A projekt célja](#a-projekt-célja)
* [Technologiák](#technologiák)
* [A felhasznált adatok](#a-felhasznált-adatok)
* [A program működése](#a-program-működése)
* [A jelenleg felismert személyes adatok](#a-jelenleg-felismert-személyes-adatok)
* [Pszeudonimizációs technikák](#pszeudonimizációs-technikák)
* [Anonimizációs technikák](#anonimizációs-technikák)


## A projekt célja

A projekt célja egy olyan alkalmazás létrehozása, amely egy adathalmazban képes személyes adatok felismerésére, 
majd ezt követően azok anonimizálására és pszeudonimizálására.


## Technológiák

A projekt Python 3.8 használatával készült. A függőségek a requirements.txt-ben találhatóak meg.


## A felhasznált adatok

* A projektben felhasznált adatok a data mappában találhatóak meg. A tesztelésre használt ds2.csv és a test.csv
általam generáltak, tehát valós adatokat NEM tartalmaznak.
* A data/local mappában található diseases_hungarian.csv forrása a https://koronavirus.gov.hu/elhunytak
* A data/local mappában található 21.02_disease_list.csv forrása a https://www.targetvalidation.org/downloads/data


## A program működése

Az adatokat felismerő függvények a detection.py modulban találhatók meg. Ha a program személyes adatot ismer fel, akkor a __labels.csv__ fileba menti el
annak az oszlopnak a nevét ahol a találat történt, és a megtalált adat jellegétől függően címkéket rendel hozzá. A fileba írás azért történik, hogy a korábbi elemzések
eredménye később is felhasználható legyen. A pszeudonimizálást végző függvények a __pseudonymisation.py__ modulban, az anonimizálást végzők pedig az __anonymisation.py__ modulban szerepelnek.
A __datamanager.py__ modulban találhatók az adathalmazokkal való munka megkönnyítésére szolgáló függvények. Az __analysis.py__ modul információt szolgáltat az adathalmaz értékeinek egyediségéről.
A programhoz tartozik egy datacrawler package, amellyel weboldalakon szereplő adatok gyűjthetők (jelenleg ez csak magyar betegségnevekre terjed ki).

A __main.py__ modulban található __auto_anon_and_pseud__ függvény automatikusan elvégzi a feladatokat. Az anonimizált eredmény a __data/output/outputtest.csv__ fileba íródik.

## A jelenleg felismert személyes adatok
* magyar rendszám
* angol betegségnevek
* magyar betegségnevek
* magyar adószám
* magyar TAJ szám
* magyar személyi szám
* magyar utónév
* magyar telefonszám
* MAC cím
* IP cím
* email cím
* országkódok, valamint angol nyelvű országnevek
* emberi életkor


# Pszeudonimizációs technikák
* szám intervallumba sorolása
* országnévből régió készítése
* email cím három részre bontása és külön-külön hashelése
* szöveg számra történő cseréje


# Anonimizációs technikák

K-anonimitás, L-diverzitás, T-közeliség. Az implementáció https://github.com/Nuclearstar/K-Anonymity megoldásán alapul.




