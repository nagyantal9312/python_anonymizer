# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class KoronavirusItem(scrapy.Item):
    # define the fields for your item here like:

    # sorszam = scrapy.Field()
    # nem = scrapy.Field()
    # kor = scrapy.Field()
    alapbetegsegek = scrapy.Field()

    pass
