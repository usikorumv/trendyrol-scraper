import re
import requests, json, os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
from deep_translator import GoogleTranslator

headers = {}


class ChromeDriverProvider:
    def _get_driver(self):
        # service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()

        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        # driver = webdriver.Chrome(service=service, options=options)
        driver = webdriver.Chrome(executable_path="./chromedriver.exe", options=options)

        return driver


class JsonHelper:
    def find_value_from_json(self, key: str, json_repr: str):
        """
        Finds dictionary value by key in json file
        including in list or dictionary which is inserted or not
        inserted
        """
        results = []

        def _decode_dict(a_dict):
            try:
                results.append(a_dict[key])
            except KeyError:
                pass
            return a_dict

        json.loads(json_repr, object_hook=_decode_dict)  # Return value ignored.
        return results


class TranslatorHelper:
    def get_translator(self, lang):
        return GoogleTranslator(source="tr", target=lang)


class TredyrolScraper(ChromeDriverProvider, JsonHelper, TranslatorHelper):
    url = "https://www.trendyol.com/"
    img_url = "https://cdn.dsmcdn.com/"

    # def __init__(self):
    #     self.driver = self._get_driver()

    def get_product_info_from_link_with_options(
        self, link, price_multiplier=1, language_to_translate="en"
    ):
        response = requests.get(link)

        product = self._get_product_info_from_page(response.text)

        product["price"] *= price_multiplier

        translator = self.get_translator(language_to_translate)

        return {
            "img": product["img"],
            "name": translator.translate(product["name"]),
            "price": product["price"],
            "colors": [
                {
                    "img": color["img"],
                    "link": color["link"],
                    "name": translator.translate(color["name"]),
                }
                for color in product["colors"]
            ],
            "sizes": product["sizes"],
            "detailes": [
                translator.translate(detail) for detail in product["detailes"]
            ],
            "species": [
                {
                    "name": translator.translate(specie["name"]),
                    "property": translator.translate(specie["property"]),
                }
                for specie in product["species"]
            ],
            "feedbacks": [
                {
                    "user": feedback["user"],
                    "comment": translator.translate(feedback["comment"]),
                    "rate": feedback["rate"],
                    "likes": feedback["likes"],
                }
                for feedback in product["feedbacks"]
            ],
            "questions_and_answers": [
                {
                    "user": question_and_answer["user"],
                    "question": translator.translate(question_and_answer["question"]),
                    "answer": translator.translate(question_and_answer["answer"]),
                }
                for question_and_answer in product["questions_and_answers"]
            ],
            "seller": product["seller"],
            "similar_products": [
                {
                    "img": similar["img"],
                    "company": similar["company"],
                    "name": translator.translate(similar["name"]),
                    "price": similar["price"],
                    "link": similar["link"],
                }
                for similar in product["similar_products"]
            ],
            "cross_products": [
                {
                    "img": cross["img"],
                    "company": cross["company"],
                    "name": translator.translate(cross["name"]),
                    "price": cross["price"],
                    "link": cross["link"],
                }
                for cross in product["cross_products"]
            ],
        }

    def get_product_info_from_link(self, link):
        # self.driver.get(link)
        # page = self.driver.page_source

        # return self._get_product_info_from_page(page)

        response = requests.get(link)

        return self._get_product_info_from_page(response.text)

    def _get_product_info_from_page(self, page):
        soup = BeautifulSoup(page, "lxml")

        product = self._get_product_info_from_scripts(
            soup.find_all("script", {"type": "application/javascript"})
        )
        product_json = json.dumps(product)

        # with open("test.json", "w") as f:
        #     f.write(product_json)

        product_id = product["id"]
        product_group_id = product["productGroupId"]
        merchant_id = re.search(r"merchantId=(.*)", product["url"]).group(1)

        try:
            name = soup.find("h1", {"class": "pr-new-br"}).find("span").text.strip()
        except:
            name = ""

        try:
            seller = soup.find("a", {"class": "merchant-text"}).text.strip()
        except:
            seller = ""

        try:
            price = product["price"]["sellingPrice"]["value"]
        except:
            price = ""

        try:
            img = (
                soup.find("div", {"class": "base-product-image"}).find("img").get("src")
            )
        except:
            img = self.url + "Content/images/defaultThumb.jpg"

        try:
            colors = self._get_colors_of_product(product_group_id)
        except:
            colors = []

        try:
            sizes = [size["value"] for size in product["allVariants"]]
        except:
            sizes = []

        try:
            detailes_container = soup.find("ul", {"class": "detail-desc-list"})
            detailes = [detail.text for detail in detailes_container.find_all("li")]
        except:
            detailes = []

        try:
            species_container = soup.find("ul", {"class": "detail-attr-container"})
            species = [
                {
                    "name": specie.find("span").text,
                    "property": specie.find("b").text,
                }
                for specie in species_container.find_all("li")
            ]
        except:
            species = {}

        try:
            feedbacks = self._get_feedbacks_of_product(product_id, 0)
        except:
            feedbacks = []

        try:
            similar_products = self._get_similar_products(page)
        except:
            similar_products = []

        try:
            cross_products = self._get_cross_products(product_id)
        except:
            cross_products = []

        try:
            question_and_answers = self._get_questions_and_answers_of_product(
                product_id, merchant_id
            )
        except:
            question_and_answers = []

        return {
            "img": img,
            "name": name,
            "price": price,
            "colors": colors,
            "sizes": sizes,
            "detailes": detailes,
            "species": species,
            "feedbacks": feedbacks,
            "questions_and_answers": question_and_answers,
            "seller": seller,
            "similar_products": similar_products,
            "cross_products": cross_products,
        }

    def _get_similar_products(self, page):
        soup = BeautifulSoup(page, "lxml")

        products_container = soup.find("aside", {"class": "productDetail-Similar"})

        return [
            {
                "img": product.find("img", {"class": "pd-img"}).get("src"),
                "company": product.find("span", {"class": "pr-rc-br"}).text,
                "name": product.find("span", {"class": "pr-rc-nm"}).text,
                "link": self.url + product.find("a").get("href")[1:],
            }
            for product in products_container.find_all("div", {"class": "pr-rc-w"})
        ]

    def _get_cross_products(self, product_id, page=0):
        response = requests.get(
            f"https://public-mdc.trendyol.com/discovery-web-websfxproductrecommendation-santral/api/v1/product/{product_id}/cross?page={page}"
        )

        products = self.find_value_from_json("content", response.text)[0]

        return [
            {
                "img": self.img_url + product["images"][0][1:],
                "company": product["brand"]["name"],
                "name": product["name"],
                "price": product["price"]["sellingPrice"]["value"],
                "link": self.url + product["url"][1:],
            }
            for product in products
        ]

    def _get_colors_of_product(self, product_group_id):
        response = requests.get(
            f"https://public.trendyol.com/discovery-web-websfxproductgroups-santral/api/v1/product-groups/{product_group_id}"
        )

        colors = self.find_value_from_json("contents", response.text)

        return [
            {
                "img": self.img_url + color[0]["imageUrl"][1:],
                "link": self.url + color[0]["url"][1:],
                "name": color[0]["name"],
            }
            for color in colors
        ]

    def _get_feedbacks_of_product(self, product_id, page=0):
        response = requests.get(
            f"https://public-mdc.trendyol.com/discovery-web-socialgw-service/api/review/{product_id}?order=5&page={page}"
        )

        product_reviews = self.find_value_from_json("productReviews", response.text)[0]

        return [
            {
                "user": product_review["userFullName"],
                "comment": product_review["comment"],
                "rate": product_review["rate"],
                "likes": product_review["reviewLikeCount"],
            }
            for product_review in product_reviews["content"]
        ]

    def _get_questions_and_answers_of_product(self, product_id, merchant_id):
        response = requests.get(
            f"https://public-mdc.trendyol.com/discovery-web-socialgw-service/api/questions/answered/{merchant_id}/{product_id}"
        )

        questions_and_answers = self.find_value_from_json("content", response.text)[0]

        return [
            {
                "user": question_and_answer["userName"],
                "question": question_and_answer["text"],
                "answer": question_and_answer["answer"]["text"],
            }
            for question_and_answer in questions_and_answers
        ]

    def _get_product_info_from_scripts(self, scripts):
        for script in scripts:
            if "window.__PRODUCT_DETAIL_APP_INITIAL_STATE__" in script.text:
                data = json.loads(re.search(r"({.*});", script.text.strip()).group(1))

                return data["product"]

        return {}

    def get_products_from_link(self, link):
        response = requests.get(link)

        return self._get_products_from_page(response.text)

    def _get_products_from_page(self, page):
        soup = BeautifulSoup(page, "lxml")

        products_container = soup.find("div", {"class": "prdct-cntnr-wrppr"})

        return {
            product.find("span", {"class": "prdct-desc-cntnr-ttl"}).text
            + " "
            + product.find("span", {"class": "prdct-desc-cntnr-name"}).text: {
                "img": product.find("img", {"class": "p-card-img"}).get("src"),
                "company": product.find("span", {"class": "prdct-desc-cntnr-ttl"}).text,
                "name": product.find("span", {"class": "prdct-desc-cntnr-name"}).text,
                "link": self.url + product.find("a").get("href")[1:],
            }
            for product in products_container.find_all(
                "div", {"class": "p-card-chldrn-cntnr"}
            )
        }

    def _get_search_link_of_product(self, product, page=1):
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
        self.driver.get(self.url)

        Select(self.driver.find_element(By.TAG_NAME, "select")).select_by_value("TR")
        self.driver.find_element(By.TAG_NAME, "button").click()

        soup = BeautifulSoup(self.driver.page_source, "lxml")

        categ_ul = soup.find("ul", {"class": "main-nav"})

        return [
            {
                "name": category.text,
                "link": self.url + category.get("href")[1:],
            }
            for category in categ_ul.find_all("a", {"class": "category-header"})
        ]


line = lambda num_of_lines=15: print("-" * num_of_lines)
clearConsole = lambda: os.sys("cls" if os.name in ("nt", "dos") else "clear")


class TrendyrolService(TredyrolScraper):
    def search_for_product(self):
        global page, current_product_name, products, first_time, finished

        page = 1
        current_product_name = ""
        products = {}
        first_time, finished = True, False

        def display_variants_of_products(name):
            link = self._get_search_link_of_product(name, page)
            new_products = self.get_products_from_link(link)
            products.update(new_products)

            print(f"[+] Page {page}")
            print("[+] URL: " + link)

            line()
            for name, _ in new_products.items():
                print(name)
            line()

        def search_product():
            global page, current_product_name

            products.clear()
            page = 1

            try:
                current_product_name = input("Product to find: ")

                display_variants_of_products(current_product_name)
            except Exception as e:
                print(f"[Error] {e}")

            # current_product_name = input("Product to find: ")

            # display_variants_of_products(current_product_name)

        def next_page():
            global products, page, current_product_name

            page += 1

            try:
                display_variants_of_products(current_product_name)
            except Exception as e:
                print(f"[Error] {e}")

        def select_product():
            while True:
                selected_product = input("Product to see: ")

                if selected_product in products.keys():
                    link = products[selected_product]["link"]

                    print(f"[URL] {link}")

                    try:
                        for key, val in self.get_product_info_from_link_with_options(
                            link=link, price_multiplier=2, language_to_translate="en"
                        ).items():
                            print()
                            print(f"{key}: {val}")
                    except Exception as e:
                        print(e)

                    # for key, val in self.get_product_info_from_link(link).items():
                    #     print()
                    #     print(f"{key}: {val}")

                    break
                else:
                    print("This product not in the page")
                    break

        def quit():
            global finished
            finished = True

        actions = [
            {
                "name": "Search Product",
                "function": search_product,
            },
            {
                "name": "Next Page",
                "function": next_page,
            },
            {
                "name": "Select Product",
                "function": select_product,
            },
            {
                "name": "Quit",
                "function": quit,
            },
        ]

        while not finished:
            if first_time:
                search_product()
                first_time = False

            while True:
                print()
                print("Available actions:")
                for i, action in enumerate(actions):
                    print(f"{i + 1}. {action['name']}")
                try:
                    option = int(input("Option: "))
                    actions[option - 1]["function"]()
                    break
                except Exception as e:
                    print(f"We don`t have '{option}' option")

                # option = int(input("Option: "))
                # actions[option - 1]["function"]()
                # break

            print()

            input("[Press enter to continue]")


def main():
    service = TrendyrolService()

    service.search_for_product()

    # for key, value in service.get_product_info_from_link(
    #     "https://www.trendyol.com/altinyildiz-classics/erkek-siyah-slim-fit-dar-kesim-5-cep-chino-pantolon-p-174674661?boutiqueId=597286&merchantId=347"
    # ).items():
    #     print(f"{key}: {value}")


if __name__ == "__main__":
    main()
