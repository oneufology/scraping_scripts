import json
import scrapy
from scrapy.crawler import CrawlerProcess


class TestSpider(scrapy.Spider):
    name = "test"
    base_url = "https://www.xxxxxxxx.it"
    start_urls = ['https://www.xxxxxxxx.it/categorie']
    api_doctor_url = "https://www.xxxxxxxx.it/api/v3/doctors/%s"
    ONLINE_CONSULT = 'consulenza online'
    headers = {
        'authorization': 'Bearer NzdjNDA5ZGU5ZmZhNDA3M2IwMmNiYzdhZjdlOTgzNjMzZjNjYmRhMGQxZGNlNjlmMWRhNDlhZjQwNjRkNjg5ZA'
    }

    def parse(self, response):
        categories = response.xpath("//a[contains(@href, 'categorie/')]")
        yield from response.follow_all(categories, callback=self.parse_category)

    def parse_category(self, response):
        doctor_items = response.xpath("//div[@id='search-content']/div/ul/li/div[@class='factors']/following-sibling::div[@class='panel panel-default']")
        for item in doctor_items:
            _id = item.css("::attr(data-result-id)").get()
            url = self.api_doctor_url % _id
            yield scrapy.Request(url, headers=self.headers, callback=self.parse_doctor)

        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse_category)

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
            '_id': data.get('id'),
        }
        doctor['titles'] = doctor['titles'].strip('. ') if doctor['titles'] else ''
        url = self.api_doctor_url % doctor['_id'] + '/specializations'
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
        url = self.api_doctor_url % doctor['_id'] + '/addresses'
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
        del doctor['_id']
        yield doctor


if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(TestSpider)
    process.start()
