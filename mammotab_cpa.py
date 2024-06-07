import os
import csv
import gzip
from gzip import BadGzipFile
import json
from tqdm import tqdm
from lamapi import LamAPI
from collections import Counter

lamapi = LamAPI()
cache = {}


def extract_relations(entities):
    """Find relations"""
    cpa_annotations = {}
    for entity_row in entities:
        for index, cell_annotation in enumerate(entity_row):
            for index_2, cell_annotation_2 in enumerate(entity_row):
                if index < index_2 and index != index_2 and cell_annotation != '' and cell_annotation != '':
                    if f"{cell_annotation}_{cell_annotation_2}" not in cache:
                        result = lamapi.predicates(
                            [[cell_annotation, cell_annotation_2]])
                        if result:
                            if "message" not in result:
                                cache[f"{cell_annotation}_{cell_annotation_2}"] = result[f"{cell_annotation} {cell_annotation_2}"]
                                if f"{index}_{index_2}" not in cpa_annotations:
                                    cpa_annotations[f"{index}_{index_2}"] = result[f"{cell_annotation} {cell_annotation_2}"]
                                else:
                                    cpa_annotations[f"{index}_{index_2}"].extend(
                                        result[f"{cell_annotation} {cell_annotation_2}"])
                    else:
                        if f"{index}_{index_2}" not in cpa_annotations:
                            cpa_annotations[f"{index}_{index_2}"] = cache[f"{cell_annotation}_{cell_annotation_2}"]
                        else:
                            cpa_annotations[f"{index}_{index_2}"].extend(
                                cache[f"{cell_annotation}_{cell_annotation_2}"])

    final_cpa_dict = {}
    for key, value in cpa_annotations.items():
        current_cpa = Counter(value).most_common()[0][0]
        final_cpa_dict[key] = current_cpa

    return final_cpa_dict


cpa = []
for folder in tqdm(os.listdir("./wiki_tables_enriched/")):
    for table in os.listdir(f"./wiki_tables_enriched/{folder}/"):
        with gzip.open(f"./wiki_tables_enriched/{folder}/{table}", 'rb') as file:
            try:
                text = file.read()
            except BadGzipFile as e:
                continue
            my_json = text.decode('utf8')
            data = json.loads(my_json)
            for table in data["tables"].keys():
                entities = [
                    row_gt for row_gt in data["tables"][table]["entity"]]
                cpa_result = extract_relations(entities)
                for key, value in cpa_result.items():
                    col_1, col_2 = key.split("_")
                    cpa.append([table, col_1, col_2, value])

    with open('cpa_gt.csv', 'w', newline='', encoding='utf8') as file:
        writer = csv.writer(file)
        writer.writerows(cpa)
