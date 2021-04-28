# Python anonymizer

## Table of Contents
* [The aim of this project](#the-aim-of-this-project)
* [Technologies](#technologies)
* [The data used](#the-data-used)
* [How this program works](#how-the-program-works)
* [The list of recognised personal data](#the-list-of-recognised-personal-data)
* [Pseudonymisation techniques](#pseudonymisation-techniques)
* [Anonymisation techniques](#anonymisation-techniques)


## The aim of this project

The aim of this project is to develop an application which is able to detect personal data, and after detection 
anonymises and pseudonymises them.


## Technologies

The project is written in Python 3.8. The dependencies can be found in requirements.txt.


## The data used

* The data used in this project can be found in the data folder. The ds2.csv and test.csv files are used for testing purposes,
they are generated, they DO NOT contain real data.
* The source of diseases_hungarian.csv in data/local folder is https://koronavirus.gov.hu/elhunytak
* The source of 21.02_disease_list.csv in data/local folder is https://www.targetvalidation.org/downloads/data


## How this program works

The personal data detection functions can be found in __detection.py__. If the program detects personal data in a column, it saves the column name to __labels.csv__, and labels it
based on the type of the data. Writing to a file is used in order to store the results for later use.
The __pseudonymisation.py__ module does the pseudonymisation and the __anonymisation.py__ module does the anonymisation.
The functions in __datamanager.py__ makes working with datasets easier. The __analysis.py__ module can provide information to the user about the uniqueness of data found
in the columns of the dataset.
The program includes a datacrawler package, which can be used for crawling data from different websites (currently it is only used for hungarian disease names).

The __auto_anon_and_pseud__ function found in __main.py__ automatizes the tasks. The result (anonymised dataset) is written into __data/output/outputtest.csv__ file.


## The list of recognised personal data
* hungarian licence plates
* english disease names
* hungarian disease names
* hungarian tax number
* hungarian TAJ number
* hungarian personal number
* hungarian first names
* hungarian phone number
* MAC address
* IP address
* email address
* country codes and country names in english
* human age


# Pseudonymisation techniques
* number to interval
* country name to region
* separating email address to three parts and hashing them
* text to number


# Anonymisation techniques

K-anonymity, L-diversity, T-closeness. The implementation is based on https://github.com/Nuclearstar/K-Anonymity.


