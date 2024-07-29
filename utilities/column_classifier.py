import collections
import re
import string

from nltk.corpus import stopwords


def remove_punctuations(s, punctuation=string.punctuation):
    """
    Remove punctuations characters
    :param s:
    :return:
    """
    return s.translate(str.maketrans("", "", punctuation))


def remove_extra_spaces(s):
    """
    Remove unnecessary spaces
    :param s:
    :return:
    """
    return " ".join(s.split())


def remove_stopwords(tokens):
    """
    Remove english stopwords
    :param tokens:
    :return:
    """
    stops = set(stopwords.words("english"))
    return [word for word in tokens if word not in stops]


def retain_alpha_nums(s):
    """
    Remove all non alpha-numeric characters
    :param s:
    :return:
    """
    return re.sub(r'[^a-zA-Z0-9]', ' ', s)


# bag of words
def bow(tokens):
    """
    Make bag of words table
    :param tokens:
    :return:
    """
    return dict(collections.Counter(re.findall(r'\w+', " ".join(tokens))))


def uc(values: list) -> float:
    """
        Fraction of cells with unique content
    """

    if len(values) == 0:
        return 0.0

    unique_values = set(values)
    return len(unique_values) / len(values)


def aw(values: list) -> float:
    """
        Average number of words in each cell
    """
    if len(values) == 0:
        return 0.0

    cleaned = remove_punctuations(" ".join(values))
    cleaned = remove_extra_spaces(cleaned)

    # This is ok only for english corpus
    words =remove_stopwords(cleaned.split(' '))
    number_of_words = len(words)

    return number_of_words / len(values)
    

def emc(values: list) -> float:
    """
        Fraction of empty cells
    """

    if len(values) == 0:
        return 0.0

    empty_cells_count = sum([
        1
        for v in values
        if len(v.strip()) == 0
    ])

    return empty_cells_count / len(values)


def df(col_idx: int, first_ne_idx: int) -> float:
    """
        Distance from the first NE-column
    """
    return abs(float(col_idx - first_ne_idx))

class ColumnClassifier:
    def __init__(self, cols_data, cols_type):
        self._cols_data = cols_data

        # 0: {NONE: 4, ID: 1, DATE: 5,...}
        self._cols_type = cols_type

    def get_columns_tags(self):
        tags = {}
        for col_name, col in self._cols_type.items():
            lit_type = self._get_lit_type(self._cols_data[col_name], col)

            if lit_type is not None:
                tags[col_name] = {
                    "tags": {
                        "col_type": "LIT",
                        "lit_type": lit_type
                    }
                }
            else:
                tags[col_name] = {
                    "tags": {
                        "col_type": "NE",
                    }
                }

        return tags

    def _accumulate_freqs(self, col, pred):
        return sum([
            freq
            for col_type, freq in col.items()
            if pred(col_type)
        ])

    def _get_lit_type(self, col, col_freqs):
        rows_count = sum([ freq for freq in col_freqs.values() ])
        lit_count = self._accumulate_freqs(
            col_freqs,
            lambda col_type: col_type != "STRING"
        )
        max_type = max(col_freqs, key=col_freqs.get)

        lit_type = None
        if lit_count > 0.60 * rows_count:
            lit_type = max_type
        elif aw(col) > 6:
            lit_type = "STRING"

        return lit_type

class ColumnClassifierTargets(ColumnClassifier):
    def __init__(self, cols_data, cols, targets):
        super().__init__(cols_data, cols)
        
        self._targets = targets # Specific table targets

    def get_columns_tags(self):
        tags = {}
        for col_idx, item in enumerate(self._cols_type.items()):
            col_name, col = item
            lit_type = self._get_lit_type(self._cols_data[col_name], col)

            if col_idx not in self._targets:
                if lit_type is None:
                    lit_type == "STRING"

                tags[col_name] = {
                    "tags": {
                        "col_type": "LIT",
                        "lit_type": lit_type
                    }
                }
            else:
                tags[col_name] = {
                    "tags": {
                        "col_type": "NE",
                    }
                }

        return tags