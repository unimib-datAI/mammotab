# Create Dataset

## 1. Download wikidumps

E.g. from [here](https://dumps.wikimedia.org/enwiki/). We suggest to download the dumps on multiple bz2 streams as it will be easy to process all the pages in parallel with reduced memory requirements (e.g. `enwiki-20220520-pages-articles-multistream1.xml-p1p41242.bz2`).
Once downloaded you should see something similar to this output:

```
> ls enwiki-*
enwiki-20220520-pages-articles-multistream10.xml-p4045403p5399366.bz2
enwiki-20220520-pages-articles-multistream11.xml-p5399367p6899366.bz2
enwiki-20220520-pages-articles-multistream11.xml-p6899367p7054859.bz2
enwiki-20220520-pages-articles-multistream12.xml-p7054860p8554859.bz2
enwiki-20220520-pages-articles-multistream12.xml-p8554860p9172788.bz2
```

## 2. Install requirements

Create a virtualenv (see [docs.python.org/3/tutorial/venv.html](https://docs.python.org/3/tutorial/venv.html)), activate it and install the requirements:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
touch .env
```

We used Python 3.10.12 and an Ubuntu 20 LTS server. All the scripts are supposed to be run from inside a virtualenv with the requirements installed.

The .env file should contain at least the following variables:

```bash
ADDACRONIMS=True
ADDALIASES=True
ADDTYPOS=True
APPROXIMATENUMBERS=True
```

The current user home folder should be writable, otherwise downloading of nltk data will fail and you need to manually provide the data. Check `utilities/column_classifier.py` for details.

## 3. Process the dumps

To process a single dump run:

```bash
python mammotab_v3.py [DUMP_FILE]
```

or as an alternative process the dumps in parallel setting `NPROC` in `parallel_v2.sh` and then running it:

```bash
bash parallel_v2.sh
```

Note that there is a constant `ENABLE_EXTERNAL_CONTEXT` which allows to keep the WikiPedia external context coming from the dumps, it defaults to false due to the large size of the data which it generates.

Once finished (it requires several hours even if executed in parallel) you should see a folder named `wiki_tables` containing, for each dump, several files named `diz_[wiki_id].jzon.gz` containing the information extracted from the dump for each wikipedia page, that contains at least one table.

The output of this first phase is a json file for each dump containing some statistics like this:

```json
{
  "tot_pages": 25507,
  "tot_tab": 3215,
  "tot_linked_tab": 2582,
  "keep_tab": 1415,
  "keep_rows": 30923,
  "keep_cols": 8898
}
```

And many json dictionaries containing the tables, similar to the following example:

<details>
    <summary>Example</summary>

    ```json
    {
        "wiki_id": "20460918", "title": "I'm a Celebrity...Get Me Out of Here! (British TV series) series 4", "tables": {"CW2LAZVR": {"caption": "None", "header": [["Celebrity", "Famous for", "Status"]], "cells": [["Celebrity", "", "Famous for", "", "Status", ""], ["'''[[Joe Pasquale]]'''", "Joe_Pasquale", "'''Comedian'''", "", "'''Winner'''<br><small>'''on 6 December 2004'''</small>", ""], ["[[Paul Burrell]]", "Paul_Burrell", "[[British Royal Household|Royal Household]] servant", "", "Runner-up<br/><small>on 6 December 2004</small>", ""], ["[[Fran Cosgrave]]", "Fran_Cosgrave", "Celebrity nightclub manager", "", "Eliminated 7th<br/><small>on 6 December 2004</small>", ""], ["[[Janet Street-Porter]]", "Janet_Street-Porter", "Broadcaster & journalist", "", "Eliminated 6th<br/><small>on 5 December 2004</small>", ""], ["[[Sophie Anderton]]", "Sophie_Anderton", "Model", "", "Eliminated 5th<br/><small>on 3 December 2004</small>", ""], ["[[Antonio Fargas]]", "Antonio_Fargas", "''[[Starsky & Hutch]]'' actor", "", "Eliminated 4th<br/><small>on 2 December 2004</small>", ""], ["[[Sheila Ferguson]]", "Sheila_Ferguson", "[[The Three Degrees]] singer", "", "Eliminated 3rd<br/><small>on 1 December 2004</small>", ""], ["[[Vic Reeves]]", "Vic_Reeves", "[[Vic and Bob]] comedian", "", "Eliminated 2nd<br/><small>on 30 November 2004</small>", ""], ["[[Nancy Sorrell]]", "Nancy_Sorrell", "Model & wife of [[Vic Reeves]]", "", "Eliminated 1st<br/><small>on 29 November 2004</small>", ""], ["[[Natalie Appleton]]", "Natalie_Appleton", "Former [[All Saints (group)|All Saints]] singer", "", "Withdrew<br/><small>on 29 November 2004</small>", ""], ["[[Brian Harvey (singer)|Brian Harvey]]", "Brian_Harvey_(singer)", "Former [[East 17]] lead singer", "", "Withdrew<br/><small>on 26 November 2004</small>", ""]], "link": [["", "", ""], ["Joe_Pasquale", "", ""], ["Paul_Burrell", "", ""], ["Fran_Cosgrave", "", ""], ["Janet_Street-Porter", "", ""], ["Sophie_Anderton", "", ""], ["Antonio_Fargas", "", ""], ["Sheila_Ferguson", "", ""], ["Vic_Reeves", "", ""], ["Nancy_Sorrell", "", ""], ["Natalie_Appleton", "", ""], ["Brian_Harvey_(singer)", "", ""]], "text": [["Celebrity", "Famous for", "Status"], ["Joe Pasquale", "Comedian", "Winner   on 6 December 2004"], ["Paul Burrell", "Royal Household servant", "Runner-up   on 6 December 2004"], ["Fran Cosgrave", "Celebrity nightclub manager", "Eliminated 7th   on 6 December 2004"], ["Janet Street-Porter", "Broadcaster & journalist", "Eliminated 6th   on 5 December 2004"], ["Sophie Anderton", "Model", "Eliminated 5th   on 3 December 2004"], ["Antonio Fargas", "Starsky & Hutch actor", "Eliminated 4th   on 2 December 2004"], ["Sheila Ferguson", "The Three Degrees singer", "Eliminated 3rd   on 1 December 2004"], ["Vic Reeves", "Vic and Bob comedian", "Eliminated 2nd   on 30 November 2004"], ["Nancy Sorrell", "Model & wife of Vic Reeves", "Eliminated 1st   on 29 November 2004"], ["Natalie Appleton", "Former All Saints singer", "Withdrew   on 29 November 2004"], ["Brian Harvey", "Former East 17 lead singer", "Withdrew   on 26 November 2004"]], "target_col": [0]}, "KFDLBZPH": {"caption": "None", "header": [["Celebrity", "Number of Stars Earned", "Percentage"]], "cells": [["Celebrity", "", "Number of Stars Earned", "", "Percentage", ""], ["[[Antonio Fargas]]", "Antonio_Fargas", "{{Rating|8|17}}", "", "47%", ""], ["[[Brian Harvey (singer)|Brian Harvey]]", "Brian_Harvey_(singer)", "{{Rating|2|10}}", "", "20%", ""], ["[[Fran Cosgrave]]", "Fran_Cosgrave", "{{Rating|18|29}}", "", "62%", ""], ["[[Janet Street Porter]]", "Janet_Street_Porter", "{{Rating|12|19}}", "", "63%", ""], ["[[Joe Pasquale]]", "Joe_Pasquale", "{{Rating|15|22}}", "", "68%", ""], ["[[Nancy Sorrell]]", "Nancy_Sorrell", "{{n/a}}", "", "{{n/a}}", ""], ["[[Natalie Appleton]]", "Natalie_Appleton", "{{Rating|15|41}}", "", "37%", ""], ["[[Paul Burrell]]", "Paul_Burrell", "{{Rating|18|24}}", "", "75%", ""], ["[[Sheila Ferguson]]", "Sheila_Ferguson", "{{Rating|6|9}}", "", "67%", ""], ["[[Sophie Anderton]]", "Sophie_Anderton", "{{Rating|8|15}}", "", "53%", ""], ["[[Vic Reeves]]", "Vic_Reeves", "{{n/a}}", "", "{{n/a}}", ""]], "link": [["", "", ""], ["Antonio_Fargas", "", ""], ["Brian_Harvey_(singer)", "", ""], ["Fran_Cosgrave", "", ""], ["Janet_Street_Porter", "", ""], ["Joe_Pasquale", "", ""], ["Nancy_Sorrell", "", ""], ["Natalie_Appleton", "", ""], ["Paul_Burrell", "", ""], ["Sheila_Ferguson", "", ""], ["Sophie_Anderton", "", ""], ["Vic_Reeves", "", ""]], "text": [["Celebrity", "Number of Stars Earned", "Percentage"], ["Antonio Fargas", "", "47%"], ["Brian Harvey", "", "20%"], ["Fran Cosgrave", "", "62%"], ["Janet Street Porter", "", "63%"], ["Joe Pasquale", "", "68%"], ["Nancy Sorrell", "", ""], ["Natalie Appleton", "", "37%"], ["Paul Burrell", "", "75%"], ["Sheila Ferguson", "", "67%"], ["Sophie Anderton", "", "53%"], ["Vic Reeves", "", ""]], "target_col": [0]}}}
    ```

</details>

## 4. Filter the dump

This step removes meaningless columns/rows (e.g. all cells are the empty string).
To process a single dump run:

```bash
python mammotab_filter.py wiki_tables [enwiki...bz2] wiki_tables_filtered
```

or run

```bash
bash parallel_filter.sh # set NPROC in the file as it fits your needs
```

to process multiple dumps in parallel.
Once finished you should see a folder named `wiki_tables_filtered`.

## 5. Wikipedia titles

To detect which mentions are NIL we obtain all the titles/links actually present in wikipedia (if a title/link is not present the mention is NIL).
For each dump run:

```
python mammotab_entity_titles.py [dump]
```

or parallelize it with e.g.

```bash
NPROC=4
ls enwiki-20220520*.bz2 | \
    xargs -I {} -n 1 -P $NPROC bash -c 'python mamotab_entity_titles.py {}'
```

It should create a folder `wiki_entities_titles` and then run

```bash
python merge_title_dicts.py wiki_entities_titles
```

to merge all inside a single pickle file (`all_titles.pickle`)

## 6. Enrich the dump with wikidata ids

This scripts requires some pickle files to work (see section [Auxiliary files](#auxiliary-files)).
This scripts gets the wikidata entities corresponding to wikipedia links and add columns types and it detects which mentions are NIL.

[LamAPI](https://bitbucket.org/disco_unimib/lamapi) is used to easily access Wikidata and DBpedia data.

Modify the environment variables according to your LAMAPI instance

```
# modify according to your lamapi instance
export LAMAPI_ROOT=http://example.lamapi.address:port/
export LAMAPI_TOKEN=lamapi_token_secret
```

then run:

```bash
python mammotab_wikidata.py wiki_tables_filtered [dump] wiki_tables_enriched
```

or in parallel

```bash
bash parallel_wikidata.sh # edit NPROC
```

Once finished you should see a folder named `wiki_tables_enriched` containing json dictionaries and json files for each dump containing some stats like for example:

```json
{
  "tot_cells": 153918,
  "tot_linked_cell": 34681,
  "entities_found": 27475,
  "entities_not_found": 7206,
  "types_found": 27003,
  "types_not_found": 7678,
  "filtered_types": 28,
  "found_perfect_types": 763,
  "tot_cols": 2924
}
```

The following examples allow to further understand how LamAPI helps the creation of the dataset.

For example when an array like this is passed to LamAPI ("entities_list")

```json
['Great_Arm_River', 'Watt_Mountain', "'Snaz", '1983–84_United_States_network_television_schedule', 'Brands_Hatch',...]
```

A sorted list of Q-Ids is returned (entities_diz)

```json
{"'Snaz": 'Q1937538', '...First_Do_No_Harm': 'Q1545282', '0-4-2': 'Q2806492', '0-4-4T': 'Q3077673', '0-6-0': 'Q2922269', '1._FC_Haßfurt': 'Q162241', '1._FC_Köln': 'Q104770', '1._FC_Köln_II': 'Q15972883', '1._FC_Normannia_Gmünd': 'Q162349', ...}
```

This dictionary is stored in `entities_dictionaries/entities_diz_<dumpname>.json`.

While when an array of types is sent (types_list):

```json
['Q327143', 'Q865720', 'Q3305593', 'Q1000028', ... ]
```

Which in human readable lables correspondes to:

```json
['Jean Rabasse', 'Borussia Dortmund II', 'Anxo Quintana', 'The Money-Maker Recipe', ... ]
```

The result is like this (types_diz):

```json
{'Q100': ['Q1549591', 'Q21518270', 'Q1093829', 'Q62049'], 'Q1000028': ['Q5398426', 'Q1366112'], 'Q1000341': ['Q515'],...}
```

Which can be read as:

```json
{
  "Boston": [
    "big city",
    "state or insular area capital of the United States",
    "city in the United States",
    "county seat"
  ],
  "The Money-Maker Recipe": ["television series", "drama television series"],
  "Ilo": ["city"]
}
```

## 7. Create semtab dataset

To create the dataset for semtab (with tables, targets, and gt) run

```bash
python mammotab_semtab.py wiki_tables_enriched mammotab_dataset_semtab
```

Once finished the folder `mammotab_dataset_semtab` will contain the dataset and the file `mammostats_semtab.json` will contain the statistics. For example:

```json
{
  "n_tables": 1226,
  "cells": 151895,
  "rows": 26597,
  "cols": 6872,
  "links": 34357,
  "mentions": 34287,
  "nils": 7097,
  "types": 26721,
  "col_types": 2867,
  "col_types_perfect": 761,
  "all_entities": 14370
}
```

# Auxiliary files

## Wikidata classes ontology

Required to sort the types from generic to specific:

1. Download and filter subclass relationships from a wikidata dump, e.g.:

```bash
sudo apt install bzip2   #or equivament for non debian based systems

wget <dump url>
bzcat latest-all.nt.bz2 | awk '$2 == "<http://www.wikidata.org/prop/direct/P279>" {print $0}'| gzip -c > ontology_all.gz
```

where `P279` is "subclass of".

2. Run

```bash
cd utilities
python prepare_ontology.py
```

Once finished you should have two pickle files:

1. `ontology_complete.pickle` #dictionary of superclasses: superclasses[wikidata_class]

2. `depth.pickle` #dictionary of depth (max depth from a top level wikidata class) : depth[wikidata_class]

Move them to the main folder to proceed.

```bash
mv *.pickle ..
cd ..
```

## Most common types (generic types)

In order to define if a given type is generic or specific we most common types across wikidata are identified.

The following bash command allows to have a list of the "Instance Of" wikidata property.

```bash
bzcat latest-all.nt.bz2 |
awk '$2 == "<http://www.wikidata.org/prop/direct/P31>"
{print $0}'| gzip -c > InstanceOf.gz
```

By then running the following script

```bash
python types_counter.py
```

A json file called `most_common.json` is created which contains an ordered dictionary for wikidata types frequency.

The threashold to distinguish between generic and specific types was empirically set to consider the first 5000 types as generic (currently types having <=250 entity instances).
