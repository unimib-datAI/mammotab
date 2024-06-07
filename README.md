# Create Dataset

## Download wikidumps
E.g. from [here](https://dumps.wikimedia.org/enwiki/20220520/). We suggest to download the dumps on multiple bz2 streams as it will be easy to process all the pages in parallel with reduced memory requirements (e.g. `enwiki-20220520-pages-articles-multistream1.xml-p1p41242.bz2`).
Once downloaded you should see something similar:
```
> ls enwiki-*
enwiki-20220520-pages-articles-multistream10.xml-p4045403p5399366.bz2
enwiki-20220520-pages-articles-multistream11.xml-p5399367p6899366.bz2
enwiki-20220520-pages-articles-multistream11.xml-p6899367p7054859.bz2
enwiki-20220520-pages-articles-multistream12.xml-p7054860p8554859.bz2
enwiki-20220520-pages-articles-multistream12.xml-p8554860p9172788.bz2
```

## Install requirements
Create a virtualenv (see [docs.python.org/3/tutorial/venv.html](https://docs.python.org/3/tutorial/venv.html)), activate it and install the requirements:
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
We used Python 3.8.10 and an Ubuntu 20 LTS server. All the scripts are supposed to be run from inside a virtualenv with the requirements installed.

## Process the dumps
To process a single dump run:
```
python mammotab_v3.py [DUMP_FILE]
```
or as an alternative process the dumps in parallel setting `NPROC` in `parallel_v2.sh` and then running it:
```
bash parallel_v2.sh
```
Once finished (it requires several hours even if executed in parallel) you should see a folder named `wiki_tables` containing, for each dump, several files named `diz_[wiki_id].jzon.gz` containing the information extracted from the dump for each wikipedia page, that contains at least one table.

## Filter the dump
This step removes meaningless columns/rows (e.g. all cells are the empty string).
To process a single dump run:
```
python mammotab_filter.py wiki_tables [enwiki...bz2] wiki_tables_filtered
```
or run
```
bash parallel_filter.sh # set NPROC in the file as it fits your needs
```
to process multiple dumps in parallel.
Once finished you should see a folder named `wiki_tables_filtered`.

## Enrich the dump with wikidata ids
This scripts requires some pickle files to work (see section [Auxiliary files](#auxiliary-files)).
This scripts gets the wikidata entities corresponding to wikipedia links and add columns types and it detects which mentions are NIL.
Modify the environment variables according to your LAMAPI instance, then run
```
# modify according to your lamapi instance
export LAMAPI_ROOT=http://example.lamapi.address:port/
export LAMAPI_TOKEN=lamapi_token_secret
#

python mammotab_wikidata.py wiki_tables_filtered [dump] wiki_tables_enriched
```
or in parallel
```
# modify according to your lamapi instance
export LAMAPI_ROOT=http://example.lamapi.address:port/
export LAMAPI_TOKEN=lamapi_token_secret
#

bash parallel_wikidata.sh # edit NPROC
```
Once finished you should see a folder namede wiki_tables_enriched.

## Create semtab dataset
To create the dataset for semtab (with tables, targets, and gt) run
```
python mammotab_semtab.py wiki_tables_enriched mammotab_dataset_semtab
```
Once finished the folder `mammotab_dataset_semtab` should contain the dataset.

# Auxiliary files

## Wikidata classes ontology
Required to sort the types from generic to specific:
1. Download and filter subclass relationships from a wikidata dump, e.g.:
```
curl 'https://zenodo.org/record/6643443/files/wikidata-20220521-truthy.nt.bz2?download=1' | bzcat | awk '$2 == "<http://www.wikidata.org/prop/direct/P279>" {print $0}'| gzip -c > ontology_all.gz
```
where `P279` is "subclass of".
2. Run
```
python prepare_ontology.py
```
Once finished you should have two pickle files:
```
ontology_complete.pickle # dictionary of superclasses: superclasses[wikidata_class]
depth.pickle # dictionary of depth (max depth from a top level wikidata class): depth[wikidata_class]
```

## Wikipedia titles
To detect which mentions are NIL we obtain all the titles/links actually present in wikipedia (if a title/link is not present the mention is NIL).
For each dump run:
```
python mamotab_entity_titles.py [dump]
```
or parallelize it with e.g.
```
NPROC=4
ls enwiki-20220520*.bz2 | \
    xargs -I {} -n 1 -P $NPROC bash -c 'python mamotab_entity_titles.py {}'
```
It should create a folder `wiki_entities_titles` and then run
```
python merge_title_dicts.py wiki_entities_titles
```
to merge all inside a single pickle file (`all_titles.pickle`)
