from time import sleep
import json

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options


class GermanySpider(Chrome):
    url = 'https://www.xxxxxxx.de/arztsuche/staedte/'
    city_urls = []
    options = Options()
    options.add_argument("--start-maximized")

    def __init__(self):
        super().__init__(options=self.options)

    def start(self):
        self.get(self.url)
        self.pass_iframe()
        self.get_city_urls()
        for doctor in self.parse_city():
            self.dump_to_jslines(doctor)
        print('End')

    def pass_iframe(self):
        sleep(4)
        is_iframe = self.find_elements_by_xpath("//iframe[contains(@id, 'sp_message_iframe')]")
        if is_iframe:
            self.switch_to.frame(is_iframe[0])
            self.find_element_by_css_selector("button[title='Einverstanden']").click()
            sleep(0.2)
            self.switch_to.default_content()

    def get_city_urls(self):
        print('Collecting city urls...')
        sleep(2)
        cities = self.find_elements_by_css_selector(".left-innen ul li a[href]")
        self.city_urls = [(c.get_attribute("href"), c.text) for c in cities]

    def parse_city(self):
        for city in self.city_urls:
            url, city_name = city
            print(f"Parsing {city_name}...")
            self.get(url)
            sleep(2)

            while True:
                more = self.execute_script('''return document.querySelector("a[href*='?page=']");''')
                if more is None:
                    break
                self.execute_script('''document.querySelector("a[href*='?page=']").click();''')
                sleep(2)

            items = self.find_elements_by_xpath("//ol[@id='result-list']/li")
            for i in items:
                fullname = i.find_element_by_xpath("./div[2]/div[1]/div[1]/div[2]/div[2]/div[1]").text
                if fullname.lower().startswith('mvz'):
                    continue
                titles = ''
                if '.' in fullname:
                    titles, fullname = fullname.rsplit('.', 1)
                    fullname = fullname.strip()
                specialties = i.find_element_by_xpath("./div[2]/div[1]/div[1]/div[2]/div[2]/div[2]/div[1]").text
                specialties = [s.strip() for s in specialties.split(',')]
                location = i.find_element_by_xpath("./div[2]/div[1]/div[1]/div[2]/div[2]/div[2]/div[2]")
                is_affil = location.find_elements_by_xpath("./a")
                affil = is_affil[0].text.strip() if is_affil else ''
                geo = location.text.replace(affil, '').replace('\n', ' ').strip()
                url = i.find_element_by_css_selector("a").get_attribute("href")
                _id = url.strip('/').rsplit('/', 1)[-1]

                yield {
                    'id': _id,
                    'url': url,
                    'fullname': fullname,
                    'titles': titles,
                    'firstname': '',
                    'lastname': '',
                    'affiliations': [
                        {
                            'affiliation': affil,
                            'geo': geo
                        }
                    ],
                    'emails': [],
                    'specialties': specialties,
                    'externalId': [],
                }
            print(city_name)

    @staticmethod
    def dump_to_jslines(doctor):
        with open('test_result.jsonlines', 'a') as f:
            json.dump(doctor, f)
            f.write('\n')
            print('Ok')


if __name__ == '__main__':
    germany = GermanySpider()
    germany.start()

