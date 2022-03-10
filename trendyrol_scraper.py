import requests, json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

headers = {}


class ChromeDriverProvider:
    def _get_driver(self):
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)

        return driver


class TredyrolScraper(ChromeDriverProvider):
    url = "https://www.trendyol.com/"

    def get_product_info_from_link(self, link):
        response = requests.get(link)

        return self.get_product_info_from_page(response.text)

    def get_product_info_from_page(self, page):
        soup = BeautifulSoup(page, "lxml")

        name = soup.find("h1", {"class": "pr-new-br"}).find("span").text
        seller = soup.find("a", {"class": "merchant-text"})
        price = float(
            soup.find("span", {"class": "prc-slg"}).text.replace(",", ".").split()[0]
        )

        colors_container = soup.find("div", {"class": "styles-module_slider__o0fqa"})
        colors = [
            {
                "name": color.get("title"),
                "image": color.find("image").get("src"),
                "link": self.url + color.get("href"),
            }
            for color in colors_container.find_all("a", {"class": "slc-img"})
        ]

        sizes_container = soup.find("div", {"class": "variants"})
        print(sizes_container)
        sizes = [
            size.text for size in sizes_container.find_all("div", {"class": "sp-itm"})
        ]

        return {
            "name": name,
            "seller": seller,
            "price": price,
            "colors": colors,
            "sizes": sizes,
        }

    def get_products_from_link(self, link):
        response = requests.get(link)

        return self.get_products_from_page(response.text)

    def get_products_from_page(self, page):
        soup = BeautifulSoup(page, "lxml")

        products_container = soup.find("div", {"class": "prdct-cntnr-wrppr"})

        return {
            product.find("span", {"class": "prdct-desc-cntnr-ttl"}).text
            + " "
            + product.find("span", {"class": "prdct-desc-cntnr-name"}).text: {
                "company": product.find("span", {"class": "prdct-desc-cntnr-ttl"}).text,
                "name": product.find("span", {"class": "prdct-desc-cntnr-name"}).text,
                "link": self.url + product.find("a").get("href")[1:],
            }
            for product in products_container.find_all(
                "div", {"class": "p-card-chldrn-cntnr"}
            )
        }

    def get_search_link_of_product(self, product, page=1):
        name = "%20".join(product.split())
        trendyrol_search_link = (
            f"https://www.trendyol.com/sr?q={name}&qt={name}&st={name}&os=1"
        )

        return trendyrol_search_link + f"&pi={page}"

    def get_subcategories(self, category_url):
        response = requests.get(url=category_url)
        soup = BeautifulSoup(response.text, "lxml")

        subcateg_container = soup.find("div", {"class": "styles-module_slider__o0fqa"})

        return [
            {
                "name": subcategory.find("span").text,
                "link": subcategory.get("href"),
            }
            for subcategory in subcateg_container.find_all("a", {"class": "item"})
        ]

    def get_categories(self):
        driver = self._get_driver()

        driver.get(self.url)
        Select(driver.find_element(By.TAG_NAME, "select")).select_by_value("TR")
        driver.find_element(By.TAG_NAME, "button").click()

        soup = BeautifulSoup(driver.page_source, "lxml")

        driver.close()

        categ_ul = soup.find("ul", {"class": "main-nav"})

        return [
            {
                "name": category.text,
                "link": self.url + category.get("href")[1:],
            }
            for category in categ_ul.find_all("a", {"class": "category-header"})
        ]


line = lambda num_of_lines=15: print("-" * num_of_lines)


class TrendyrolService(TredyrolScraper):
    actions = [
        "Next Page",
        "Select Product",
        "Search",
        "Quit",
    ]

    def search_for_product(self):
        page = 1
        products = {}
        last_product_name = ""

        while True:
            print()
            product_name = (
                last_product_name
                if last_product_name != ""
                else input("Product to find: ")
            )
            link = super().get_search_link_of_product(product_name, page)
            new_products = super().get_products_from_link(link)
            products.update(new_products)

            print(f"[+] Page {page}")
            print("[+] URL: " + link)

            line()
            for name, product in new_products.items():
                print(name)
            line()

            while True:
                print()
                print("Available actions:")
                for i, e in enumerate(self.actions):
                    print(f"{i + 1}. {e}")
                action = int(input("Option: "))
                if action > 0 and action <= len(self.actions):
                    print(self.actions[action - 1])
                    break
                else:
                    print(f"We don`t have '{action}' option")

            if action == 1:
                last_product_name = product_name
                page += 1
                continue

            if action == 2:
                print()
                while True:
                    selected_product = input("Product to see: ")
                    if selected_product in products.keys():
                        print(products[selected_product])
                        link = products[selected_product]["link"]
                        for key, val in super().get_product_info_from_link(link):
                            print(f"{key}: {val}")
                        break
                    else:
                        print("This product not in the page")
                        break

            if action == 3:
                products.clear()
                last_product_name = ""
                page = 1
                continue

            if action == 4:
                break


def main():
    service = TrendyrolService()

    service.search_for_product()

    # service.get_product_info_from_link(
    #     "https://www.trendyol.com/trendyolmilla/kahverengi-kemerli-dugme-kapamali-su-itici-ozellikli-uzun-trenckot-twoss20tr0012-p-43123490?boutiqueId=599739&merchantId=968"
    # )


if __name__ == "__main__":
    main()
