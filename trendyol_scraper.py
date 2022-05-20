import math

import os.path
from os import path
from os import mkdir

import ujson, asyncio, aiohttp

from time import time

# TODO: MAKE FULL ASYNCHRONOMOUS get_all_categories []
# TODO: write2file PARAMETER FOR SEVERAL FUCTIONS
# TODO: DRY AND REFACTOR
# TODO: CREATE FILE INCLUDE AUTO FOLDER CREATION IF IT IS IN PATH
# TODO: OPTIMIZE 1


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


class MyUtils:
    @staticmethod
    def create_file(path, info):
        with open(path, "w", encoding="utf-8") as f:
            f.write(info)

    @staticmethod
    def create_folder(name):
        if path.exists(name):
            return
        mkdir(name)


headers = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
}


class TrendyolScraper:
    site_url = "https://www.trendyol.com"
    img_url = "https://cdn.dsmcdn.com"

    aggregations_api = (
        "https://public.trendyol.com/discovery-web-searchgw-service/v2/api/aggregations"
    )

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
    all_products = []

    def get_products_api(self, link, page=0):
        url = (
            "https://public.trendyol.com/discovery-web-searchgw-service/v2/api/infinite-scroll"
            + link
        )
        if page != 0:
            return url + f"?pi={page}"
        return url

    def get_products_group_api(self, id):
        return f"https://public.trendyol.com/discovery-web-websfxproductgroups-santral/api/v1/product-groups/{id}"

    def get_product_api(self, id):
        return f"https://public.trendyol.com/discovery-web-productgw-service/api/productDetail/{id}?linearVariants=true"

    def get_reccomendations_api(self, id, group):
        return f"https://public-mdc.trendyol.com/discovery-web-websfxproductrecommendation-santral/api/v1/product/{id}/{group}?size=20"

    # async def get_pagination_of_products_from_link(
    #     self, session: aiohttp.ClientSession, link
    # ):
    #     async with session.get(
    #         self.get_products_api(link, 1), headers=headers
    #     ) as response:
    #         print(self.get_products_api(link, 1))
    #         print(response)
    #         data = ujson.loads(await response.text())

    #         products_data = data["result"]

    #         total_pages = products_data["totalCount"]

    #         pagination = math.floor(total_pages / 23)

    #         return pagination + 1

    async def get_cross_products_id(self, id):
        async with session.get(
            self.get_reccomendations_api(id, "/cross"), headers=headers
        ) as response:
            try:
                data = ujson.loads(await response.text())

                products = data["result"]["content"]

                return [product["id"] for product in products]
            except:
                return []

    async def get_recommendation_products_id(self, id):
        async with session.get(
            self.get_reccomendations_api(id, "/recommendation"), headers=headers
        ) as response:
            try:
                data = ujson.loads(await response.text())

                products = data["result"]["content"]

                return [product["id"] for product in products]
            except:
                return []

    async def get_product_attributes(self, session, raw_product):
        async with session.get(
            self.get_products_group_api(raw_product["productGroupId"]), headers=headers
        ) as response:
            try:
                data = ujson.loads(await response.text())

                slicing_attributes = data["result"]["slicingAttributes"][0][
                    "attributes"
                ]

                attributes = []
                for slicing_attribute in slicing_attributes:
                    attribute = slicing_attribute["contents"][0]
                    attributes.append(
                        {
                            "id": attribute["id"],
                            "name": slicing_attribute["name"],
                            "slug": slicing_attribute["beautifiedName"],
                            "link": attribute["url"],
                        }
                    )

                return attributes
            except:
                return

    async def get_product_from_id(self, session, id):
        async with session.get(self.get_product_api(id), headers=headers) as response:
            data = ujson.loads(await response.text())

            product = data["result"]

            campaign = product["campaign"]
            brand = product["brand"]
            category = product["originalCategory"]
            brand = product["brand"]
            sizes = product["allVariants"]
            description = product["contentDescriptions"]

            return {
                "id": product["id"],
                "name": product["name"],
                "link": product["url"],
                "images": product["images"],
                "price": product["price"],
                "campaign": product["merchant"]["name"],
                "brand": {
                    "id": brand["id"],
                    "name": brand["name"],
                    "slug": brand["beautifiedName"],
                },
                "category": {
                    "id": category["id"],
                    "name": category["name"],
                    "slug": category["beautifiedName"],
                },
                "color": product["color"],  # REVIEW
                "showSize": product["variants"][0]["attributeValue"],  # REVIEW
                "sizes": [
                    {
                        "value": size["value"],
                        "inStock": size["inStock"],
                        "price": size["price"],
                        "currency": size["currency"],
                    }
                    for size in sizes
                ],
                "description": "\n".join(
                    [
                        description["description"]
                        for description in product["contentDescriptions"]
                    ]
                ),
                "reviews": "",
                "questions": "",
                "recommendations": await self.get_recommendation_products_id(id),
                "cross": await self.get_cross_products_id(id)
            }

    async def get_product_from_raw_data(self, session, raw_product: dict):
        # print(await self.get_product_from_id(session, raw_product["id"]))

        attributes = await self.get_product_attributes(session, raw_product)

        # Make async
        if attributes is not None:
            for attribute in attributes:
                colors = [
                    {
                        "name": attribute["name"],
                        "product": await self.get_product_from_id(
                            session, attribute["id"]
                        ),
                    }
                    for attribute in attributes
                ]

            product = DictionaryUtils.get_dict_by_key_value(
                [color["product"] for color in colors],
                "showSize",
                raw_product["winnerVariant"],
            )
            product["colors"] = colors

            return product
        else:
            return await self.get_product_from_id(session, raw_product["id"])

    async def get_all_products_from_link(self, session, link, page):
        async with session.get(
            self.get_products_api(link, page),
            headers=headers,
        ) as response:
            try:
                data = ujson.loads(await response.text())

                raw_products = data["result"]["products"]

                self.all_products += [
                    await self.get_product_from_raw_data(session, raw_product)
                    for raw_product in raw_products
                ]

                print(f"Link: {link}\nPage: {page}\n")

            except Exception as e:
                print(e)
                print(f"{page} failed")

    async def fetch_all_products(self):
        self.all_products = []

        # OPTIMIZE 1
        with open("output/categories.json", "r") as f:
            categories = ujson.loads(f.read())

        end_categories = []
        for category in categories:
            parent = True
            for compare in categories:
                if compare.get("parent", "") == "":
                    continue
                if category["slug"] == compare["slug"]:
                    continue
                if category["slug"] == compare["parent"]:
                    parent = True
                    break
                parent = False

            if not parent:
                end_categories.append(category)
        #

        async with aiohttp.ClientSession() as session:
            # pagination = await self.get_pagination_of_products_from_link(session, category["link"])
            tasks = [
                self.get_all_products_from_link(session, category["link"], page)
                for page in range(208 + 1)  # JUST FOR TEST
                for category in end_categories  # JUST FOR TEST
            ]

            await asyncio.gather(*tasks)

    def get_all_products(self, write2file=False):
        if not path.exists("output/categories.json"):
            self.get_all_categories(write2file=True)

        asyncio.run(self.fetch_all_products())

        # if write2file:
        #     MyUtils.create_folder("output")
        #     MyUtils.create_file("output/products.json", ujson.dumps(self.all_products))

        return self.all_products

    # # GET AGGREGATIONS
    # aggregations = []

    # async def get_aggregations(self, session, link):
    #     async with session.get(
    #         "https://public.trendyol.com/discovery-web-searchgw-service/v2/api/aggregations" + link, headers=headers
    #     ) as response:
    #         self.aggregations = []

    #         data = ujson.loads(await response.text())

    #         aggregations = data["result"]["aggregations"]

    #         self.aggregations = aggregations

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
                    "id": color["id"],
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

    def get_all_colors(self, write2file=False):
        asyncio.run(self.fetch_all_colors())

        if write2file:
            MyUtils.create_folder("output")
            MyUtils.create_file("output/colors.json", ujson.dumps(self.all_colors))

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

    def get_all_sizes(self, write2file=False):
        asyncio.run(self.fetch_all_sizes())

        if write2file:
            MyUtils.create_folder("output")
            MyUtils.create_file("output/sizes.json", ujson.dumps(self.all_sizes))

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
                    "id": brand["id"],
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

    def get_all_brands(self, write2file=False):
        asyncio.run(self.fetch_all_brands())

        if write2file:
            MyUtils.create_folder("output")
            MyUtils.create_file("output/brands.json", ujson.dumps(self.all_brands))

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
                pass
                # print(self.aggregations_api + link)
                # print(response.ok)
                # print(e)

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
                                "id": category["id"],
                                "name": category["text"],
                                "slug": category["beautifiedName"],
                                "link": category["url"],
                                "count": category["count"],
                                "parent": all_categories[i]["slug"],
                            }
                            for category in categories
                        ]
                except Exception as e:
                    pass
                    # print(e)

                i += 1

        self.all_categories += all_categories

    async def fetch_all_categories(self):
        tasks = [self.get_categories(category) for category in self.categories]

        await asyncio.gather(*tasks)

    def get_all_categories(self, write2file=False):
        asyncio.run(self.fetch_all_categories())

        if write2file:
            MyUtils.create_folder("output")
            MyUtils.create_file(
                "output/categories.json", ujson.dumps(self.all_categories)
            )

        return self.all_categories


def main():
    scraper = TrendyolScraper()

    start_time = time()

    scraper.get_all_products(write2file=True)

    print(time() - start_time)


if __name__ == "__main__":
    main()
