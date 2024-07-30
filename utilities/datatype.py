from enum import Enum


class DataTypeEnum(Enum):
    NONE = ""
    EMPTY = "empty"
    GEOCOORD = "geo_coordinates"
    HEXCOLOR = "hex_color"
    NUMERIC = "numeric"
    IP = "ip"
    CREDITCARD = "credit_card"
    IMAGE = "image"
    URL = "url"
    EMAIL = "email"
    ISBN = "isbn"
    ISO8601 = "iso8601"
    BOOLEAN = "boolean"
    DATE = "date"
    DESCRIPTION = "description"
    CURRENCY = "currency"
    IATA = "iata"
    ADDRESS = "address"
    ID = "id"
    NOANNOTATION = "no_annotation"

    @staticmethod
    def get_datatype_info(data_type):
        xml_string = {
            "label": "xsd:string",
            "uri": "http://www.w3.org/2001/XMLSchema#string"
        }
        xml_float = {
            "label": "xsd:float",
            "uri": "http://www.w3.org/2001/XMLSchema#float"
        }
        xml_integer = {
            "label": "xsd:integer",
            "uri": "http://www.w3.org/2001/XMLSchema#integer"
        }
        xml_double = {
            "label": "xsd:double",
            "uri": "http://www.w3.org/2001/XMLSchema#double"
        }
        xml_date = {
            "label": "xsd:date",
            "uri": "http://www.w3.org/2001/XMLSchema#date"
        }
        xml_boolean = {
            "label": "xsd:boolean",
            "uri": "http://www.w3.org/2001/XMLSchema#boolean"
        }
        xml_any_uri = {
            "label": "xsd:anyURI",
            "uri": "http://www.w3.org/2001/XMLSchema#anyURI"
        }

        datatype_map = {
            DataTypeEnum.GEOCOORD: xml_string,
            DataTypeEnum.ADDRESS: xml_string,
            DataTypeEnum.HEXCOLOR: xml_string,
            DataTypeEnum.URL: xml_any_uri,
            DataTypeEnum.NUMERIC: [
                xml_float,
                xml_integer,
                xml_double,
            ],
            DataTypeEnum.IMAGE: xml_string,
            DataTypeEnum.CREDITCARD: xml_string,
            DataTypeEnum.EMAIL: xml_string,
            DataTypeEnum.IP: xml_string,
            DataTypeEnum.ISBN: xml_string,
            DataTypeEnum.ISO8601: xml_string,
            DataTypeEnum.BOOLEAN: xml_boolean,
            DataTypeEnum.DATE: xml_date,
            DataTypeEnum.ID: xml_string,
            DataTypeEnum.CURRENCY: xml_string,
            DataTypeEnum.DESCRIPTION: xml_string,
            DataTypeEnum.IATA: xml_string,
        }

        return datatype_map.get(data_type, xml_string)

    @staticmethod
    def get_datatype_uri(data_type):
        all_datatype = [
            {
                "label": "xsd:string",
                "uri": "http://www.w3.org/2001/XMLSchema#string"
            },
            {
                "label": "xsd:float",
                "uri": "http://www.w3.org/2001/XMLSchema#float"
            },
            {
                "label": "xsd:integer",
                "uri": "http://www.w3.org/2001/XMLSchema#integer"
            },
            {
                "label": "xsd:double",
                "uri": "http://www.w3.org/2001/XMLSchema#double"
            },
            {
                "label": "xsd:date",
                "uri": "http://www.w3.org/2001/XMLSchema#date"
            },
            {
                "label": "xsd:boolean",
                "uri": "http://www.w3.org/2001/XMLSchema#boolean"
            },
            {
                "label": "xsd:anyURI",
                "uri": "http://www.w3.org/2001/XMLSchema#anyURI"
            }
        ]

        for current_type in all_datatype:
            if current_type['label'] == data_type:
                return current_type
