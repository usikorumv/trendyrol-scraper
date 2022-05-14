import ujson
import asyncio
import aiohttp

from time import time

# TODO: CREATE get_aggregations(link) function
# TODO: MAKE FULL ASYNCHRONOMOUS get_all_categories
# TODO: write2file PARAMETER FOR SEVERAL FUCTIONS
# TODO: DRY
# TODO: get_all_products()


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
        return next(item for item in aggregations if item[key] == value)

    # @staticmethod
    # def delete_recursively(dict_: dict, condition=lambda x: x is None):
    #     for key, value in dict_.copy().items():
    #         if isinstance(value, dict):
    #             results = DictionaryUtils.delete_recursively(value, condition)
    #             for k, v in results.items():
    #                 if condition(v):
    #                     del results[k]

    #         elif isinstance(value, list):
    #             for item in value:
    #                 if isinstance(item, dict):
    #                     more_results = DictionaryUtils.delete_recursively(item, condition)
    #                     for k, v in more_results.items():
    #                         if condition(v):
    #                             del more_results[k]
    #     return dict_

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


class TrendyolScraper:
    site_url = "https://www.trendyol.com"
    img_url = "https://cdn.dsmcdn.com"

    aggregations_api = f"https://public.trendyol.com/discovery-web-searchgw-service/v2/api/aggregations"

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

    # def get_all_products_from_link(self, link):
    #     pass

    # def get_all_products(self):
    #     pass

    aggregations = []

    async def get_aggregations(self, session, link):
        async with session.get(self.aggregations_api + link) as response:
            data = ujson.loads(await response.text())

            aggregations = data["result"]["aggregations"]

            self.aggregations = aggregations

    # GET COLORS
    all_colors = set()

    async def get_colors_from_link(self, session, link):
        async with session.get(self.aggregations_api + link) as response:
            data = ujson.loads(await response.text())

            try:
                aggregations = data["result"]["aggregations"]

                colors_aggregation = next(
                    item for item in aggregations if item["group"] == "ATTRIBUTE"
                )
                colors = colors_aggregation["values"]

                for color in colors:
                    self.all_colors.add(
                        tuple(
                            {
                                "name": color["text"],
                                "slug": color["beautifiedName"],
                                "link": color["url"],
                            }.items()
                        )
                    )
            except Exception as e:
                with open("error.json", "w") as f:
                    f.write(ujson.dumps(data))

                print(e)

    async def fetch_all_colors(self):
        tasks = []

        async with aiohttp.ClientSession() as session:
            for category in self.categories:
                tasks.append(self.get_colors_from_link(session, category["link"]))

            await asyncio.gather(*tasks)

    def get_all_colors(self):
        asyncio.run(self.fetch_all_colors())

        return [dict(tup) for tup in self.all_colors]

    # GET SIZES
    all_sizes = set()

    async def get_sizes_from_link(self, session, link):
        async with session.get(self.aggregations_api + link) as response:
            data = ujson.loads(await response.text())

            try:
                aggregations = data["result"]["aggregations"]

                sizes_aggregation = next(
                    item for item in aggregations if item["group"] == "VARIANT"
                )
                sizes = sizes_aggregation["values"]

                for size in sizes:
                    self.all_sizes.add(
                        tuple(
                            {
                                "name": size["text"],
                                "slug": size["beautifiedName"],
                                "link": size["url"],
                            }.items()
                        )
                    )
            except Exception as e:
                with open("error.json", "w") as f:
                    f.write(ujson.dumps(data))

                print(e)

    async def fetch_all_sizes(self):
        tasks = []

        async with aiohttp.ClientSession() as session:
            for category in self.categories:
                tasks.append(self.get_sizes_from_link(session, category["link"]))

            await asyncio.gather(*tasks)

    def get_all_sizes(self):
        asyncio.run(self.fetch_all_sizes())

        return [dict(tup) for tup in self.all_sizes]

    # GET BRANDS
    all_brands = set()

    async def get_brands_from_link(self, session, link):
        async with session.get(self.aggregations_api + link) as response:
            data = ujson.loads(await response.text())

            try:
                aggregations = data["result"]["aggregations"]

                brands_aggregation = next(
                    item for item in aggregations if item["group"] == "BRAND"
                )
                brands = brands_aggregation["values"]

                for brand in brands:
                    self.all_brands.add(
                        tuple(
                            {
                                "name": brand["text"],
                                "slug": brand["beautifiedName"],
                                "link": brand["url"],
                            }.items()
                        )
                    )
            except Exception as e:
                with open("error.json", "w") as f:
                    f.write(ujson.dumps(data))

                print(e)

    async def fetch_all_brands(self):
        tasks = []

        async with aiohttp.ClientSession() as session:
            for category in self.categories:
                tasks.append(self.get_brands_from_link(session, category["link"]))

            await asyncio.gather(*tasks)

    def get_all_brands(self):
        asyncio.run(self.fetch_all_brands())

        return [dict(tup) for tup in self.all_brands]

    # GET CATEGORIES
    all_categories = []

    async def get_categories_from_link(self, session, link):
        async with session.get(self.aggregations_api + link) as response:
            data = ujson.loads(await response.text())

            try:
                aggregations = data["result"]["aggregations"]

                category_aggregation = next(
                    item for item in aggregations if item["group"] == "CATEGORY"
                )
                categories = category_aggregation["values"]

                return categories

            except Exception as e:
                with open("error.json", "w") as f:
                    f.write(ujson.dumps(data))

                print(e)

    async def get_categories(self, category, write2file=False):
        all_categories = [category]

        async with aiohttp.ClientSession() as session:
            i = 0
            while i < len(all_categories):
                categories = await self.get_categories_from_link(
                    session, all_categories[i]["link"]
                )

                print(categories)

                if len(categories) > 1:
                    all_categories += [
                        {
                            "name": category["text"],
                            "slug": category["beautifiedName"],
                            "link": category["url"],
                            "parent": all_categories[i]["slug"],
                        }
                        for category in categories
                    ]
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

    def get_categories_tree(self, write2file=False):
        all_categories = self.get_all_categories()

        categories_tree = DictionaryUtils.generate_tree(
            all_categories, "parent", "slug"
        )

        return categories_tree


def main():
    scraper = TrendyolScraper()

    start_time = time()
    print(scraper.get_all_colors())
    print(time() - start_time)


if __name__ == "__main__":
    main()
