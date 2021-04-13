import scrapy
from ..items import KoronavirusItem


class KoronavirusSpider(scrapy.Spider):

    name = "koronavirus"

    def start_requests(self):
        start_urls = [
            "https://koronavirus.gov.hu/elhunytak"
        ]
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        items = KoronavirusItem()

        for row in response.css('tbody').xpath('//tr'):
            # sorszam = row.xpath('td[1]//text()').extract_first()
            # nem = row.xpath('td[2]//text()').extract_first()
            # kor = row.xpath('td[3]//text()').extract_first()
            alapbetegsegek = row.xpath('td[4]//text()').extract_first()

            # items['sorszam'] = sorszam
            # items['nem'] = nem
            # items['kor'] = kor
            items['alapbetegsegek'] = alapbetegsegek

            yield items

        next_page = response.css('li.next a::attr(href)').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)



