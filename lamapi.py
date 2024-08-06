"""LamAPI Wrapper File"""

import os
import requests


class FormatException(Exception):
    """Invalid Format Exception"""

    def __str__(self) -> str:
        return "Invalid Format"


class URL:
    """URLs Builder Class"""

    def __init__(self, base_url, response_format="json"):
        self.format = response_format

        self.base_url = base_url

        # lookup
        self.lookup = "lookup/entity-retrieval"

        # entity
        self.entities_labels = "entity/labels"
        self.entities_objects = "entity/objects"
        self.entities_predicates = "entity/predicates"
        self.entities_types = "entity/types"
        self.entities_literals = "entity/literals"

        # classify
        self._literal_recognizer = "classify/literal-recognizer"

        # sti
        self._column_analysis = "sti/column-analysis"

    def lookup_url(self):
        """Return Lookup URL"""
        return self.base_url + self.lookup

    def entities_labels_url(self):
        """Return Labels URL"""
        return self.base_url + self.entities_labels

    def column_analysis_url(self):
        """Return Column Analysis URL"""
        return self.base_url + self._column_analysis

    def predicates_url(self):
        """Return predicates URL"""
        return self.base_url + self.entities_predicates

    def types_url(self):
        """Return types URL"""
        return self.base_url + self.entities_types


class LamAPI():
    """LamAPI Wrapper Class"""

    def __init__(self, response_format="json", kg="wikidata") -> None:
        self.format = response_format
        base_url = os.getenv('LAMAPI_ROOT')
        self._url = URL(base_url, response_format=response_format)
        self.client_key = os.getenv('LAMAPI_TOKEN')
        self.kg = kg
        self.headers = {
            'accept': 'application/json'
        }

    def _exec_post(self, params, json_data, url, kg):
        response = requests.post(url,
                                 params=params,
                                 headers=self.headers,
                                 json=json_data,
                                 timeout=15)
        result = response.json()
        if kg in result:
            result = result[kg]
        return result

    def __to_format(self, response):
        if self.format == "json":
            result = response.json()
            for kg in ["wikidata", "dbpedia", "crunchbase"]:
                if kg in result:
                    result = result[kg]
                    break
            return result
        else:
            raise FormatException

    def __submit_get(self, url, params):
        return self.__to_format(requests.get(url, headers=self.headers, params=params, timeout=15))

    def __submit_post(self, url, params, headers, json):
        return self.__to_format(requests.post(url,
                                              headers=headers,
                                              params=params,
                                              json=json,
                                              timeout=15))

    def column_analysis(self, columns):
        """LamAPI Column Analysis Method"""
        json_data = {
            'json': columns
        }
        params = {
            'token': self.client_key
        }
        result = self.__submit_post(
            self._url.column_analysis_url(), params, self.headers, json_data)
        return result

    def labels(self, entitites, lang="en"):
        """LamAPI Labels Method"""
        params = {
            'token': self.client_key,
            'kg': self.kg,
            'lang': lang
        }
        json_data = {
            'json': entitites
        }
        result = self.__submit_post(
            self._url.entities_labels_url(), params, self.headers, json_data)
        return result

    def lookup(self, string, ngrams=False, fuzzy=False, types=None, limit=10):
        """LamAPI Lookup Method"""
        params = {
            'token': os.environ.get('LAMAPI_TOKEN'),
            'name': string,
            'ngrams': ngrams,
            'fuzzy': fuzzy,
            'types': types,
            'kg': self.kg,
            'limit': limit
        }
        result = self.__submit_get(self._url.lookup_url(), params)
        if len(result) > 1:
            result = {"wikidata": result}
        return result

    def types(self, entities):
        """LamAPI types"""
        params = {
            'token': self.client_key,
            'kg': self.kg,
        }
        json_data = {
            'json': entities
        }
        result = self.__submit_post(
            self._url.types_url(), params, self.headers, json_data)
        return result

    def predicates(self, entities):
        """LamAPI predicates"""
        params = {
            'token': self.client_key,
            'kg': self.kg,
        }
        json_data = {
            'json': entities
        }
        result = self.__submit_post(
            self._url.predicates_url(), params, self.headers, json_data)
        return result

    def test(self) -> str:
        return "test"
