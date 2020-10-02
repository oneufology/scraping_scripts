import json
import pathlib
import scrapy
from scrapy.crawler import CrawlerProcess


NAME = 'turkey'
TOKEN = 'Bearer ZTJmMzYwMDE3YjJkYjk3NDMzZGZjZjhjMzM0MjE3MjIzMGMwYjVmOGQzZmM2NmI2YjExMjlhZjA0N2YzZGU5YQ'
_dir = pathlib.Path().absolute()


class TurkeyPhysyciansSpider(scrapy.Spider):
    def __init__(self, name, token):
        self.name = name
        self.headers = {"authorization": token}

    base_url = "https://www.xxxxxx.com%s"
    start_urls = ['https://www.xxxxxx.com/uzmanlik-alanlari']
    category_keyword = "ayrintili"
    api_doctor_url = base_url % "/api/v3/doctors/%s"
    ONLINE_CONSULT = "online"

    def parse(self, response):
        categories = response.xpath(f"//a[contains(@href, '{self.category_keyword}/')]")
        yield from response.follow_all(categories, callback=self.parse_category)

    def parse_category(self, response):
        cityes = response.css("ul.list-unstyled li.col-sm-6 a")
        yield from response.follow_all(cityes, callback=self.parse_city)

    def parse_city(self, response):
        doctor_items = response.xpath("//div[@id='search-content']/div/ul/li/div[@class='factors']/following-sibling::div[@class='panel panel-default']")
        for item in doctor_items:
            _id = item.css("::attr(data-result-id)").get()
            url = self.api_doctor_url % _id
            yield scrapy.Request(url, headers=self.headers, callback=self.parse_doctor)

        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse_city)

    def parse_doctor(self, response):
        data = json.loads(response.text)
        doctor = {
            'fullname': data.get('full_name'),
            'titles': data.get('prefix'),
            'firstname': data.get('name'),
            'lastname': data.get('surname'),
            'affiliations': [],
            'emails': [],
            'specialties': [],
            'externalId': [],
            'id': data.get('id'),
            'url': data.get('url'),
        }
        doctor['titles'] = doctor['titles'].strip('. ') if doctor['titles'] else ''
        url = self.api_doctor_url % doctor['id'] + '/specializations'
        yield scrapy.Request(
            url,
            headers=self.headers,
            meta={'doctor': doctor},
            callback=self.get_specializations
        )

    def get_specializations(self, response):
        data = json.loads(response.text)
        doctor = response.meta.get('doctor')
        for item in data['_items']:
            spec = item.get('name')
            if spec:
                doctor['specialties'].append(spec.capitalize())
        url = self.api_doctor_url % doctor['id'] + '/addresses'
        yield scrapy.Request(
            url,
            headers=self.headers,
            meta={'doctor': doctor},
            callback=self.get_addresses
        )

    def get_addresses(self, response):
        data = json.loads(response.text)
        doctor = response.meta.get('doctor')
        for item in data['_items']:
            affiliation = item.get('name')
            if self.ONLINE_CONSULT not in affiliation.lower():
                geo = "%s, %s, %s, %s" % (
                    item.get('street'),
                    item.get('city_name'),
                    item.get('province'),
                    item.get('post_code'),
                )
                doctor['affiliations'].append({
                        'affiliation': affiliation,
                        'geo': geo
                     })
        yield doctor


if __name__ == '__main__':
    process = CrawlerProcess({
        'FEED_FORMAT': 'jsonlines',
        'FEED_URI': f'{_dir}/{NAME}.jsonlines',
    })
    process.crawl(TurkeyPhysiciansSpider, NAME, TOKEN)
    process.start()
    