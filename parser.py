# pylint: disable=E0202
import requests
import chromedriver_binary
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from selenium import webdriver
from decimal import Decimal
import json
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


company_website = 'https://www.wellton-towers.ru/flats/?limit=500&mode=table&offset=0'


def get_html(url):

    error = 0
    while error < 11:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("window-size=1400,2100")
        chrome_options.add_argument('--disable-gpu')
        browser = webdriver.Chrome(options=chrome_options)
        browser.get(url)
        try:
            target = browser.find_element_by_class_name("footer__links-item")
            error == 12
            actions = ActionChains(browser)
            actions.move_to_element(target)
            actions.perform()
            html = browser.page_source

            return html
        except AttributeError:
            error += 1
            if error == 10:
                print("Не получается получить javascript")
            else:
                print('Network Error')
            return False


def finding_link_for_each_flat(html):
    list_with_half_of_the_link = []
    soup = BeautifulSoup(html, 'html.parser')

    find_class_tag = soup.find('div', attrs={
                               'class': 'flat-list-table__list js-flat-list-table-container active'})

    find_href = find_class_tag.findAll('a', href=True)
    for i in find_href:
        first_children = i['href']
        list_with_half_of_the_link.append(first_children)

    return list_with_half_of_the_link


def get_full_list_of_flats_url():
    first_part = 'https://www.wellton-towers.ru'
    url_list = []
    for i in (finding_link_for_each_flat(get_html(company_website))):
        url_list.append(first_part+i)
    return url_list


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


def price(soup):
    building = soup.find(
        'a', class_='realty-sidebar__back-button').next_sibling.next_sibling.next_sibling.next_sibling.text
    building_number_text = building.split()[1]  # корпус

    floor = soup.findAll('a', class_='realty-sidebar__back-button')
    floor_text = floor[2].text.split()[0]  # этаж

    area = soup.findAll('div', class_='flat-detail__info-value')
    area_text = area[1].text.replace(',', '.')  # площадь

    rooms_text = area[0].text  # комнаты

    discount_percent = soup.find('div', class_='flat-detail__price-discount')
    if discount_percent == None:
        discount_percent_text = None
    else:
        discount_percent_text = Decimal(discount_percent.text.split()[
            2][:-1])  # процент скидки

    price_before_discount = soup.find('div', class_='flat-detail__price-old')
    if price_before_discount == None:
        price_before_discount_text = None
    else:
        price_before_discount_text = ''.join(price_before_discount.text.split())[
            :-1]  # старая цена без отделки и скидки

    price_with_discount = soup.find('div', class_='flat-detail__price-val')
    if price_with_discount == None:
        price_with_discount_text = None
    else:
        price_with_discount_text = Decimal(''.join(price_with_discount.text.split())[
            :-1])  # новая цена без отделки со скидкой

    room_number = soup.find(
        'div', class_='flat-detail__number').text.split()[1]  # номер кваритры на этаже

    picture_url = (soup.find('div', class_='flat-detail__plan-3d dont-print'))
    if picture_url == None:
        full_picture_url_text = None
    else:
        try:
            picture_url = str(picture_url)
            picture_url_text = picture_url.split()[5]
            full_picture_url_text = 'https://www.wellton-towers.ru/' + \
                picture_url_text  # картинка
        except IndexError:
            full_picture_url_text = None

    base_price = soup.find('div', class_='flat-detail__price')
    if price_before_discount_text == None:
        price_before_discount_text = ''.join(base_price.text.split())[
            :-1]  # цена если скидки нет

    item = dict(
        complex='WELLTON TOWERS',
        type='flat',
        phase=None,
        building=building_number_text,
        section=None,
        price_base=Decimal(price_before_discount_text),
        price_finished=None,
        price_sale=price_with_discount_text,
        price_finished_sale=None,
        area=Decimal(area_text),
        living_area=None,
        number=None,
        number_on_site=room_number,
        rooms=int(rooms_text),
        floor=int(floor_text),
        in_sale=1,
        sale_status='Забронировать',
        finished=0,
        ceil=None,
        article=None,
        finishing_name=None,
        furniture=None,
        furniture_price=None,
        plan=full_picture_url_text,
        feature=None,
        view=None,
        euro_planning=None,
        sale=None,
        discount_percent=discount_percent_text,
        discount=None
    )

    return item


def show_all():
    list_of_dicts = []
    for flats in get_full_list_of_flats_url():
        html = requests.get(flats, verify=False).text
        soup = BeautifulSoup(html, 'html.parser')
        list_of_dicts.append(price(soup))
        out = json.dumps(list_of_dicts, cls=DecimalEncoder, indent=1,
                         sort_keys=False, ensure_ascii=False).encode('utf8').decode()
    print(out)


if __name__ == "__main__":
    show_all()
