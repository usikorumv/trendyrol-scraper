import os
import json
import requests
import asyncio

from time import time

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

    def get_products(self, ):
        pass

    # Add session paramether
    def get_categories(self, link):
        response = requests.get(self.aggregations_api + link)

        data = json.loads(response.text)

        aggregations = data["result"]["aggregations"]

        category_aggregation = next(
            item for item in aggregations if item["group"] == "CATEGORY"
        )
        categories = category_aggregation["values"]

        return categories

    # Convert to asynchromous
    # get_all_categories(self, need_parent)
    def get_all_categories(self):
        all_categories = self.categories.copy()

        i = 0
        while i < len(all_categories):
            categories = self.get_categories(all_categories[i]["link"])

            if len(categories) > 1:
                all_categories += [
                    {
                        "name": category["text"],
                        "slug": category["beautifiedName"],
                        "link": category["url"],
                        "parent": all_categories[i]["link"],
                    }
                    for category in categories
                ]
            i += 1

        return all_categories

    def get_categories_tree(self):
        all_categories = self.get_all_categories()

        categories_tree = DictionaryUtils.generate_tree(
            all_categories, "parent", "link"
        )

        return categories_tree


def main():
    scraper= TrendyolScraper()

    start_time = time()
    print(scraper.get_categories_tree())
    print(time() - start_time)


main()
