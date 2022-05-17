import math
import ujson
import asyncio
import aiohttp
import requests_ip_rotator

from time import time

# TODO: MAKE FULL ASYNCHRONOMOUS get_all_categories []
# TODO: write2file PARAMETER FOR SEVERAL FUCTIONS
# TODO: DRY AND REFACTOR

class DictionaryUtils:
    @staticmethod
    def get_recursively(search_dict: dict(), to_find):
        fields_found = []

        for key, value in search_dict.items():
            if key == to_find:
                fields_found.append(value)

            elif isinstance(value, dict):
                results = DictionaryUtils.get_recursively(value, to_find)
                for result in results:
                    fields_found.append(result)

            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        more_results = DictionaryUtils.get_recursively(item, to_find)
                        for another_result in more_results:
                            fields_found.append(another_result)

        return fields_found

    @staticmethod
    def get_dict_by_key_value(lst, key, value):
        return next(item for item in lst if item[key] == value)

    @staticmethod
    def get_unique_list_from_dicts(lst):
        return [dict(t) for t in {tuple(d.items()) for d in lst}]

    @staticmethod
    def generate_tree(data, parent, parent_key):
        levels = {}

        for n in data:
            levels.setdefault(n.get(parent, None), []).append(n)

        def build_tree(parent_id=None):
            nodes = [dict(n) for n in levels.get(parent_id, [])]
            for n in nodes:
                children = build_tree(n[parent_key])
                if children:
                    n["children"] = children
            return nodes

        return build_tree()

        # new_data = data.copy()

        # for i in range(len(new_data) - 1, -1, -1):
        #     data[i]["children"] = [
        #         child for child in new_data if child[parent] == new_data[i][parent_key]
        #     ]

        #     for child in new_data[i]["children"]:
        #         new_data.remove(child)

        # return new_data


headers = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
}

# class IPRotator:
    


class TrendyolScraper:
    site_url = "https://www.trendyol.com"
    img_url = "https://cdn.dsmcdn.com"

    aggregations_api = (
        "https://public.trendyol.com/discovery-web-searchgw-service/v2/api/aggregations"
    )

    products_api = "https://public.trendyol.com/discovery-web-searchgw-service/v2/api/infinite-scroll"

    categories = [
        {
            "name": "Kadın Giyim",
            "slug": "kadın-giyim",
            "link": "/kadin-giyim-x-g1-c82",
        },
        {
            "name": "Erkek Giyim",
            "slug": "erkek-giyim",
            "link": "/erkek-giyim-x-g2-c82",
        },
        {
            "name": "Çocuk Giyim",
            "slug": "cocuk-giyim",
            "link": "/cocuk-giyim-x-g3-c82",
        },
    ]
    #

    # GET PRODUCTS
    count = 0
    all_products = []

    def get_products_api(self, link, page):
        return self.products_api + link + f"?pi={page}"

    async def get_pagination_of_products_from_link(self, session: aiohttp.ClientSession, link):
        async with session.get(
            self.get_products_api(link, 1), headers=headers
        ) as response:
            print(self.get_products_api(link, 1))
            print(response)
            data = ujson.loads(await response.text())

            products_data = data["result"]

            total_pages = products_data["totalCount"]

            pagination = math.floor(total_pages / 23)

            return pagination + 1

    async def get_all_products_from_link(self, session, link, page):
        async with session.get(
            self.get_products_api(link, page),
            headers=headers,
        ) as response:
            try:
                data = ujson.loads(await response.text())

                products = data["result"]["products"]

                self.all_products += [
                    product
                    # {
                    #     "name": product["name"],
                    #     "": ,
                    # }
                    for product in products
                ]

                print(page)

                self.count += 1
            except:
                print(f"{page} failed")
                

    async def fetch_all_products(self):
        self.all_products = []

        async with aiohttp.ClientSession() as session:
            # pagination = await self.get_pagination_of_products_from_link(session, category["link"])
            tasks = [
                self.get_all_products_from_link(session, self.categories[0]["link"], page)
                # self.get_all_products_from_link(session, category["link"], page)
                for page in range(1, 1000)
                # # for page in range(1, pagination):
                # for category in self.categories
            ]

            await asyncio.gather(*tasks)

    def get_all_products(self):
        asyncio.run(self.fetch_all_products())

        print(f"{self.count} is done")

        return self.all_products

    # GET AGGREGATIONS
    aggregations = []

    async def get_aggregations(self, session, link):
        async with session.get(
            self.aggregations_api + link, headers=headers
        ) as response:
            self.aggregations = []

            data = ujson.loads(await response.text())

            aggregations = data["result"]["aggregations"]

            self.aggregations = aggregations

    # GET COLORS
    all_colors = []

    async def get_colors_from_link(self, session, link):
        async with session.get(
            self.aggregations_api + link, headers=headers
        ) as response:
            data = ujson.loads(await response.text())

            aggregations = data["result"]["aggregations"]

            colors_aggregation = next(
                item for item in aggregations if item["group"] == "ATTRIBUTE"
            )
            colors = colors_aggregation["values"]

            self.all_colors += [
                {
                    "name": color["text"],
                    "slug": color["beautifiedName"],
                }
                for color in colors
            ]

    async def fetch_all_colors(self):
        tasks = []

        async with aiohttp.ClientSession() as session:
            for category in self.categories:
                tasks.append(self.get_colors_from_link(session, category["link"]))

            await asyncio.gather(*tasks)

    def get_all_colors(self):
        asyncio.run(self.fetch_all_colors())

        return DictionaryUtils.get_unique_list_from_dicts(self.all_colors)

    # GET SIZES
    all_sizes = []

    async def get_sizes_from_link(self, session, link):
        async with session.get(
            self.aggregations_api + link, headers=headers
        ) as response:
            data = ujson.loads(await response.text())

            aggregations = data["result"]["aggregations"]

            sizes_aggregation = next(
                item for item in aggregations if item["group"] == "VARIANT"
            )
            sizes = sizes_aggregation["values"]

            self.all_sizes += [
                {
                    "name": size["text"],
                    "slug": size["beautifiedName"],
                }
                for size in sizes
            ]

    async def fetch_all_sizes(self):
        tasks = []

        async with aiohttp.ClientSession() as session:
            for category in self.categories:
                tasks.append(self.get_sizes_from_link(session, category["link"]))

            await asyncio.gather(*tasks)

    def get_all_sizes(self):
        asyncio.run(self.fetch_all_sizes())

        print(self.count)

        return DictionaryUtils.get_unique_list_from_dicts(self.all_sizes)

    # GET BRANDS
    all_brands = []

    async def get_brands_from_link(self, session, link):
        async with session.get(
            self.aggregations_api + link, headers=headers
        ) as response:
            data = ujson.loads(await response.text())

            aggregations = data["result"]["aggregations"]

            brands_aggregation = next(
                item for item in aggregations if item["group"] == "BRAND"
            )
            brands = brands_aggregation["values"]

            self.all_brands += [
                {
                    "name": brand["text"],
                    "slug": brand["beautifiedName"],
                }
                for brand in brands
            ]

    async def fetch_all_brands(self):
        tasks = []

        async with aiohttp.ClientSession() as session:
            for category in self.categories:
                tasks.append(self.get_brands_from_link(session, category["link"]))

            await asyncio.gather(*tasks)

    def get_all_brands(self):
        asyncio.run(self.fetch_all_brands())

        return DictionaryUtils.get_unique_list_from_dicts(self.all_brands)

    # GET CATEGORIES
    all_categories = []

    async def get_categories_from_link(self, session, link):
        async with session.get(
            self.aggregations_api + link, headers=headers
        ) as response:
            try:
                data = ujson.loads(await response.text())

                aggregations = data["result"]["aggregations"]

                category_aggregation = DictionaryUtils.get_dict_by_key_value(
                    aggregations, "group", "CATEGORY"
                )
                categories = category_aggregation["values"]

                return categories

            except Exception as e:
                print(self.aggregations_api + link)
                print(response.ok)
                print(e)

    async def get_categories(self, category, write2file=False):
        all_categories = [category]

        async with aiohttp.ClientSession() as session:
            i = 0
            while i < len(all_categories):
                categories = await self.get_categories_from_link(
                    session, all_categories[i]["link"]
                )

                try:
                    if len(categories) > 1:
                        print()

                        for category in categories:
                            print(category["text"])

                        all_categories += [
                            {
                                "name": category["text"],
                                "slug": category["beautifiedName"],
                                "link": category["url"],
                                "parent": all_categories[i]["slug"],
                            }
                            for category in categories
                        ]
                except Exception as e:
                    print(categories)
                    print(e)

                    # tries = 0

                    # while tries > 0:
                    #     tries -= 1
                    #     await asyncio.sleep(15)
                    #     # make continue for outter while

                i += 1

        self.all_categories += all_categories

    async def fetch_all_categories(self):
        tasks = []

        for category in self.categories:
            tasks.append(self.get_categories(category))

        await asyncio.gather(*tasks)

    def get_all_categories(self=False):
        asyncio.run(self.fetch_all_categories())

        return self.all_categories


def main():
    scraper = TrendyolScraper()

    start_time = time()

    # scraper.get_all_products()

    # with open("products.json", "w", encoding="utf-8") as f:
    #     ujson.dump(scraper.get_all_products(), f)

    with open("categories.json", "w", encoding="utf-8") as f:
        ujson.dump(scraper.get_all_categories(), f)

    # with open("sizes.json", "w", encoding="utf-8") as f:
    #     ujson.dump(scraper.get_all_sizes(), f)

    # with open("brands.json", "w", encoding="utf-8") as f:
    #     ujson.dump(scraper.get_all_brands(), f)

    # with open("colors.json", "w", encoding="utf-8") as f:
    #     ujson.dump(scraper.get_all_colors(), f)

    print(time() - start_time)


if __name__ == "__main__":
    main()
