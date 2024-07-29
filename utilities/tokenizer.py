#     wink-tokenizer
#     Multilingual tokenizer that automatically tags each token with its type.
#
#     Copyright (C) 2017-19  GRAYPE Systems Private Limited
#
#     This file is part of “wink-tokenizer”.
#
#     Permission is hereby granted, free of charge, to any person obtaining a
#     copy of this software and associated documentation files (the "Software"),
#     to deal in the Software without restriction, including without limitation
#     the rights to use, copy, modify, merge, publish, distribute, sublicense,
#     and/or sell copies of the Software, and to permit persons to whom the
#     Software is furnished to do so, subject to the following conditions:
#
#     The above copyright notice and this permission notice shall be included
#     in all copies or substantial portions of the Software.
#
#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#     OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#     FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#     THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#     LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#     FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#     DEALINGS IN THE SOFTWARE.
import re,os,json
from enum import Enum
from collections import Counter

class TokenTagEnum(Enum):
    WORD = "word"
    NUMBER = "number"
    QUOTED_PHRASE = "quoted_phrase"
    URL = "url"
    EMAIL = "email"
    MENTION = "mention"
    HASHTAG = "hash_tag"
    EMOJI = "emoji"
    TIME = "time"
    ORDINAL = "ordinal"
    CURRENCY = "currency"
    PUNCTUATION = "punctuation"
    SYMBOL = "symbol"
    ALIEN = "alien"


class Token:
    def __init__(self, value: str, tag: TokenTagEnum):
        self.value = value
        self.tag = tag

    def __str__(self):
        return f"{self.value}[{self.tag.value}]"

    def __repr__(self):
        return str(self)


class Tokenizer:
    json_string = None
    with open(os.path.join(os.path.dirname(__file__), "contractions.json"), "r") as file:
        json_string = file.read()

    contractions = json.loads(json_string)  

    rgx_quoted_phrase = r"\"[^\"]*\""
    rgx_url = r"(?i)(?:https?:\/\/)(?:[\da-z\.-]+)\.(?:[a-z\.]{2,6})(?:[\/\w\.\-\?#=]*)*\/?"
    rgx_email = r"(?i)[-!#$%&'*+\/=?^\w{|}~](?:\.?[-!#$%&'*+\/=?^\w`{|}~])*@[a-z0-9](?:-?\.?[a-z0-9])*(?:\.[a-z](?:-?[a-z0-9])*)+"
    rgx_mention = r"@\w+"
    rgx_hash_tag_l1 = r"(?i)#[a-z][a-z0-9]*"
    rgx_hash_tag_dv = r"(?i)#[\u0900-\u0963\u0970-\u097F][\u0900-\u0963\u0970-\u097F\u0966-\u096F0-9]*"
    rgx_emoji = r"[\uD800-\uDBFF][\uDC00-\uDFFF]|[\u2600-\u26FF]|[\u2700-\u27BF]"
    rgx_time = r"(?i)(?:\d|[01]\d|2[0-3]):?(?:[0-5][0-9])?\s?(?:[ap]\.?m\.?|hours|hrs)"
    rgx_ordinal_l1 = r"1\dth|[04-9]th|1st|2nd|3rd|[02-9]1st|[02-9]2nd|[02-9]3rd|[02-9][04-9]th|\d+\d[04-9]th|\d+\d1st|\d+\d2nd|\d+\d3rd"
    rgx_currency = r"[₿₽₹₨$£¥€₩]"
    rgx_punctuation = r"[’'‘’`“”\"\[\]\(\){}…,\.!;\?\-:\u0964\u0965]"
    rgx_symbol = r"[\u0950~@#%\^\+=\*\|\/<>&]"
    rgx_word_l1 = r"(?i)[a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF][a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF']*"
    rgx_word_dv = r"(?i)[\u0900-\u094F\u0951-\u0963\u0970-\u097F]+"
    rgx_number_l1 = r"\d+\/\d+|\d(?:[\.,-\/]?\d)*(?:\.\d+)?"
    rgx_number_dv = r"[\u0966-\u096F]+\/[\u0966-\u096F]+|[\u0966-\u096F](?:[\.,-\/]?[\u0966-\u096F])*(?:\.[\u0966-\u096F]+)?"
    rgx_pos_singular = r"(?i)([a-z]+)('s)$"
    rgx_pos_plural = r"(?i)([a-z]+s)(')$"

    def __init__(self):
        self.regexes = [
            (Tokenizer.rgx_quoted_phrase, TokenTagEnum.QUOTED_PHRASE),
            (Tokenizer.rgx_url, TokenTagEnum.URL),
            (Tokenizer.rgx_email, TokenTagEnum.EMAIL),
            (Tokenizer.rgx_mention, TokenTagEnum.MENTION),
            (Tokenizer.rgx_hash_tag_l1, TokenTagEnum.HASHTAG),
            (Tokenizer.rgx_hash_tag_dv, TokenTagEnum.HASHTAG),
            (Tokenizer.rgx_emoji, TokenTagEnum.EMOJI),
            (Tokenizer.rgx_time, TokenTagEnum.TIME),
            (Tokenizer.rgx_ordinal_l1, TokenTagEnum.ORDINAL),
            (Tokenizer.rgx_number_l1, TokenTagEnum.NUMBER),
            (Tokenizer.rgx_number_dv, TokenTagEnum.NUMBER),
            (Tokenizer.rgx_currency, TokenTagEnum.CURRENCY),
            (Tokenizer.rgx_word_l1, TokenTagEnum.WORD),
            (Tokenizer.rgx_word_dv, TokenTagEnum.WORD),
            (Tokenizer.rgx_punctuation, TokenTagEnum.PUNCTUATION),
            (Tokenizer.rgx_symbol, TokenTagEnum.SYMBOL),
        ]

    def GetType(self, text):
        tokens = self.tokenize(text)
        return self._most_frequent_tag(tokens)

    def tokenize(self, text):
        return self._tokenize_recursive(text, self.regexes)
    
    def _most_frequent_tag(self,tokens):
        tags = [token.tag for token in tokens]
        tag_counts = Counter(tags)
        most_common_tag = tag_counts.most_common(1)[0][0]
    
        return TokenTagEnum[most_common_tag]

    def _tokenize_recursive(self, text, regexes):
        sentence = text.strip()
        final_tokens = []

        if len(regexes) <= 0:
            # No regex left, split on spaces and tag every token as **alien**
            for tkn in re.split(r"\s+", text):
                final_tokens.append(Token(tkn.strip(), TokenTagEnum.ALIEN))

            return final_tokens

        rgx = regexes[0]
        tokens = self._tokenize_text_unit(sentence, rgx)

        for token in tokens:
            if isinstance(token, str):
                final_tokens.extend(self._tokenize_recursive(token, regexes[1:]))
            else:
                final_tokens.append(token)

        return final_tokens

    def _tokenize_text_unit(self, text, regex):
        matches = list(re.findall(regex[0], text))
        balance = list(re.split(regex[0], text))
        tokens = []
        tag = regex[1]

        k = 0
        for i in range(0, len(balance)):
            t = balance[i].strip()
            if len(t) > 0:
                tokens.append(t)

            if k < len(matches):
                if tag == TokenTagEnum.WORD:
                    # Possible contraction
                    aword = matches[k]
                    if aword.find("'") >= 0:
                        tokens = self._manage_contraction(aword, tokens)
                    else:
                        # No contractions
                        tokens.append(Token(aword, tag))
                else:
                    tokens.append(Token(matches[k], tag))

            k += 1

        return tokens

    def _manage_contraction(self, word, tokens):
        ct = Tokenizer.contractions.get(word, None)

        if ct is None:
            # Possessive of singular and plural forms
            matches = re.match(Tokenizer.rgx_pos_singular, word)
            if matches is not None:
                tokens.append(Token(matches[1], TokenTagEnum.WORD))
                tokens.append(Token(matches[2], TokenTagEnum.WORD))
            else:
                matches = re.match(Tokenizer.rgx_pos_plural, word)
                if matches is not None:
                    tokens.append(Token(matches[1], TokenTagEnum.WORD))
                    tokens.append(Token(matches[2], TokenTagEnum.WORD))
                else:
                    tokens.append(Token(word[0:word.find("'")], TokenTagEnum.WORD))
                    tokens.append(Token("'", TokenTagEnum.PUNCTUATION))
                    tokens.append(Token(word[word.find("'")+1:], TokenTagEnum.WORD))
        else:
            # Lookup
            tokens.append(Token(ct[0], TokenTagEnum.WORD))
            tokens.append(Token(ct[1], TokenTagEnum.WORD))
            if len(ct) == 3:
                tokens.append(Token(ct[2], TokenTagEnum.WORD))

        return tokens
