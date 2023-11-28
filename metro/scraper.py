import logging
import collections
import csv

import requests
import bs4

# Жеаемый путь сохранения csv файла
path = '/Users/daniil/PycharmProjects/scraper_test/metro/result.csv'


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('metro')

ParseResult = collections.namedtuple(
    'ParseResult',
    (
        'id_product',
        'name',
        'url',
        'reg_price',
        'sale_prise'
    ),
)

HEADERS = (
    'ID',
    'Название',
    'Ссылка',
    'Скидка',
    'Цена',
)


class Client:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/119.0.0.0 Safari/537.36',
            'Accept-Language': 'ru',
        }
        self.result = []

    def load_page(self, page: int = None):
        params = {

        }
        if page and page > 1:
            params['page'] = page
        url = 'https://online.metro-cc.ru/category/sladosti-chipsy-sneki/konfety-podarochnye-nabory'
        res = self.session.get(url, params=params)
        res.raise_for_status()

        return res.text

    def pagination_limit(self):
        text = self.load_page()
        soup = bs4.BeautifulSoup(text, 'lxml')
        container = soup.select('a.v-pagination__item.catalog-paginate__item')
        last = int(container[-1].text) + 1
        if not container:
            return 1

        return last

    def get_limit(self):
        limit = self.pagination_limit()
        logger.info(f'Всего страниц:{limit}')
        for i in range(1, limit + 1):
            self.parse_page(page=i)

    def parse_page(self, page: int = None):
        text = self.load_page(page=page)
        soup = bs4.BeautifulSoup(text, 'lxml')
        container = soup.select('div.catalog-2-level-product-card.product-card.'
                                'subcategory-or-type__products-item.with-rating.with-prices-drop')
        for block in container:
            self.parse_block(block=block)

    def parse_block(self, block):
        id_sweet = block.get('data-sku')

        name_block = block.select_one('span.product-card-name__text')
        if not name_block:
            logger.error('no name_block')
        name = name_block.getText().strip()
        if not name:
            logger.error('no name')

        url_block = block.select_one('a.product-card-photo__link.reset-link')
        if not url_block:
            logger.error('no url_block')
            return
        url = url_block.get('href')
        if not url:
            logger.error('no href')
            return
        url = 'https://online.metro-cc.ru' + url

        old_price_block = block.select_one('div.product-unit-prices__old-wrapper')
        old_price = old_price_block.select_one('span.product-price__sum-rubles')
        if old_price:
            old_price = old_price.text.strip()

        new_price_block = block.select_one('div.product-unit-prices__actual-wrapper')
        new_price = new_price_block.select_one('span.product-price__sum-rubles')
        if new_price:
            new_price = new_price.text.strip()

        self.result.append(ParseResult(
            id_product=id_sweet,
            name=name,
            url=url,
            reg_price=new_price,
            sale_prise=old_price,
        ))

        logger.debug('%s, %s, %s, %s, %s', id_sweet, name, url, old_price, new_price)
        logger.debug('-' * 100)

    def save_res(self):
        with open(path, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(HEADERS)
            for item in self.result:
                writer.writerow(item)

    def run(self):
        self.pagination_limit()
        self.get_limit()
        self.save_res()
        logger.info(f'Получили {len(self.result)} наименований')


if __name__ == '__main__':
    parser = Client()
    parser.run()
