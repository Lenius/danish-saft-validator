import datetime
import hashlib
from typing import Union, List, Tuple, Dict, Optional

import pandas as pd

from dataclasses import dataclass

from lxml.etree import _Element, _ElementTree

from modules.conventions.date_handler import date_time_handler
from modules.conventions.file_system import FileSystem
from modules.conventions.read_write import Read
from modules.conventions.text_lang import Language, Texts

date_format = "%Y-%m-%d %H:%M:%S"


def audit_trail_translated(lang: Language):
    return Read.excel_dict(path=FileSystem.audit_trail,
                           sheet_name_='Sheet1',
                           key='audit_trail',
                           val=lang.value)


class Check:
    def __init__(self, lang):
        self.xml_read = Texts.xml_read[lang]
        self.naming_check = Texts.naming_check[lang]
        self.structure_check = Texts.structure_check[lang]
        self.certificate_check = Texts.certificate_check[lang]
        self.signature_check = Texts.signature_check[lang]
        self.value_check = Texts.value_check[lang]


class Report:
    def __init__(self, lang):
        self.ok_prefix = 'OK_'
        self.nok_prefix = 'NOK_'
        self.flag_prefix = 'FLAG_'
        self.checked = Texts.checked[lang]


class DeleteXML:
    def __init__(self, lang):
        self.ja = Texts.yes[lang]
        self.nej = Texts.no[lang]

    def __iter__(self):
        for variable in [self.ja, self.nej]:
            yield variable


class SheetNames:
    def __init__(self, lang):
        self.check = Texts.check[lang]
        self.master_data = Texts.master_data[lang]


@dataclass
class MasterData:
    company_id: Union[str, None]
    company_name: Union[str, None]
    software_company: Union[str, None]
    software_desc: Union[str, None]
    software_version: Union[str, None]
    created_at: Union[datetime.datetime, None]
    modified_at: Union[datetime.datetime, None]
    last_access: Union[datetime.datetime, None]

    def res(self, lang):
        return {'CVR': self.company_id,
                Texts.company_name[lang]: self.company_name,
                Texts.software_company_name[lang]: self.software_company,
                Texts.software_description[lang]: self.software_desc,
                Texts.software_version[lang]: self.software_version,
                Texts.file_generated[lang]: self.created_at.strftime(date_format),
                Texts.file_modified[lang]: self.modified_at.strftime(date_format),
                Texts.file_last_access[lang]: self.last_access.strftime(date_format)}


@dataclass
class Signature:
    prev_signature: Union[str, None]
    nr: Union[str, None]
    trans_id: Union[str, None]
    trans_type: Union[str, None]
    trans_date: Union[str, None]
    trans_time: Union[str, None]
    emp_id: Union[str, None]
    trans_amnt_in: Union[str, None]
    trans_amnt_ex: Union[str, None]
    register_id: Union[str, None]
    company_ident: Union[str, None]

    @property
    def full_message(self):
        return f"{self.prev_signature};" \
               f"{self.nr};" \
               f"{self.trans_id};" \
               f"{self.trans_type};" \
               f"{self.trans_date};" \
               f"{self.trans_time};" \
               f"{self.emp_id};" \
               f"{self.trans_amnt_in};" \
               f"{self.trans_amnt_ex};" \
               f"{self.register_id};" \
               f"{self.company_ident}"

    @property
    def full_message_hh_mm_ss(self):
        new_trans_date = date_time_handler.convert_to_date(self.trans_date)
        new_trans_time = date_time_handler.convert_to_time(self.trans_time,
                                                           new_trans_date)
        if new_trans_time:
            return f"{self.prev_signature};" \
                   f"{self.nr};" \
                   f"{self.trans_id};" \
                   f"{self.trans_type};" \
                   f"{new_trans_date};" \
                   f"{new_trans_time.strftime(format='%H:%M:%S')};" \
                   f"{self.emp_id};" \
                   f"{self.trans_amnt_in};" \
                   f"{self.trans_amnt_ex};" \
                   f"{self.register_id};" \
                   f"{self.company_ident}"
        return self.full_message

    @property
    def full_message_encoded(self):
        return self.full_message.encode('utf-8')

    @property
    def full_message_sha512(self):
        return hashlib.sha512(bytes(self.full_message, 'utf-8')).digest()

    @property
    def full_message_encoded_hh_mm_ss(self):
        return self.full_message_hh_mm_ss.encode('utf-8')

    @property
    def full_message_sha512_hh_mm_ss(self):
        return hashlib.sha512(bytes(self.full_message_hh_mm_ss, 'utf-8')).digest()

    def __repr__(self):
        return f"{self.full_message}"

    @property
    def full_message_sha512_hex(self):
        return hashlib.sha512(bytes(self.full_message, 'utf-8')).hexdigest()


class Status:
    def __init__(self, lang):
        self.ok = Texts.ok[lang]
        self.error = Texts.error[lang]


class Employee:
    def __init__(self, id: str, date: str, first_name: str, sur_name: str, role_type: str, role_type_desc: str,
                 element: _Element):
        """
        Initialize an Employee instance.

        :param id: The employee's ID.
        :param date: The date of the employee's record.
        :param first_name: The employee's first name.
        :param sur_name: The employee's surname.
        :param role_type: The role type of the employee.
        :param role_type_desc: A description of the employee's role.
        :param element_: The associated XML element (from lxml.etree).
        """
        self.id = id
        self.date = date
        # self.datetime = date_time_handler.convert_to_datetime(self.date, "00:00:00")
        # self.datetime_min = date_time_handler.truncate_seconds(self.datetime)
        self.first_name = first_name
        self.sur_name = sur_name
        self.full_name = f"{first_name} {sur_name}"
        self.role_type = role_type
        self.role_type_desc = role_type_desc
        self.employee_type_element = element

    def __repr__(self) -> str:
        """
        Provide a string representation of the Employee instance.

        :return: A string representing the Employee instance.
        """
        return (f"Employee(id={self.id!r}, first_name={self.first_name!r}, "
                f"sur_name={self.sur_name!r}, role_type={self.role_type!r}, "
                f"role_type_desc={self.role_type_desc!r})")


class EmployeeCollection:
    def __init__(self):
        """
        Initialize an EmployeeCollection instance to manage a collection of Employee objects.
        """
        self.employees: Dict[str, Employee] = {}

    def add_employee(self, employee: Employee):
        """
        Add an Employee instance to the collection.

        :param employee: The Employee instance to add.
        """
        self.employees[employee.id] = employee

    def __getitem__(self, employee_id: str) -> Optional[Employee]:
        """
        Retrieve an Employee instance by its ID.

        :param employee_id: The ID of the Employee to retrieve.
        :return: The Employee instance with the given ID, or None if not found.
        """
        return self.employees.get(employee_id)

    def __repr__(self) -> str:
        """
        Provide a string representation of the EmployeeCollection instance.

        :return: A string representing the EmployeeCollection instance.
        """
        return f"EmployeeCollection(employees={list(self.employees.values())})"



class Article:
    def __init__(self, id: str, desc: str, group_id: str, date: str, element: _Element):
        self.id = id
        self.desc = desc
        self.group_id = group_id
        self.date = date
        self.article_type_element = element

    def __getitem__(self, item):
        return self.id[item]

    def __repr__(self) -> str:
        """
        Provide a string representation of the Basics instance.

        :return: A string representing the Basics instance.
        """
        return (f"Articles(id={self.id!r}, group_id={self.group_id!r}, desc={self.desc!r}, "
                f"date={self.date!r})")



class ArticleCollection:
    def __init__(self):
        self.articles: Dict[str, Article] = {}

    def add_article(self, article: Article):
        """
        Add an Article instance to the collection.

        :param article: The Article instance to add.
        """
        self.articles[article.id] = article

    def __getitem__(self, article_id: str) -> Optional[Article]:
        """
        Retrieve an Article instance by its id.

        :param article_id: The id of the Article to retrieve.
        :return: The Article instance with the given id, or None if not found.
        """
        return self.articles.get(article_id)

    def __repr__(self) -> str:
        """
        Provide a string representation of the ArticleCollection instance.

        :return: A string representing the ArticleCollection instance.
        """
        return f"ArticleCollection(articles={list(self.articles.values())})"




@dataclass
class SchemaChild:
    name: str
    optional: bool


class ElementInfo:
    def __init__(self, name: str, element_type: str, children: Dict[str, SchemaChild],
                 immediate_children: Dict[str, SchemaChild],
                 optional: bool):
        self.name = name
        self.type = element_type
        self.children = children
        self.immediate_children = immediate_children
        self.optional = optional
        self.is_parent: bool = True if self.type is None else False
        self.parents: List[str] = []

    def __repr__(self) -> str:
        """
        Provide a string representation of the ElementInfo instance.

        :return: A string representing the ElementInfo instance.
        """
        return (f"ElementInfo(name={self.name!r}, type={self.type!r}, "
                f"immediate_children={self.immediate_children!r}, optional={self.optional!r})")


class SchemaCollection:
    def __init__(self, schema: _ElementTree):
        self.elements: Dict[str, ElementInfo] = {}
        self.__element_parents: Dict[str, List[str]] = {}
        self.__build_schema_collection(schema)
        self.__generate_all_parents()

    def __build_schema_collection(self, schema: _ElementTree):
        for element in schema.findall(".//{http://www.w3.org/2001/XMLSchema}element"):
            if 'name' in element.attrib:
                element_name = element.attrib['name']
                element_type = element.attrib.get('type', None)
                element_optional = True if element.attrib.get('minOccurs', None) is not None else False
                children = self.__get_all_children_xsd(element)
                immediate_children = self.__get_all_immediate_children(element)

                element_info = ElementInfo(name=element_name, element_type=element_type,
                                           children=children, immediate_children=immediate_children,
                                           optional=element_optional)
                self.add_element(element_info)

    def __generate_all_parents(self):
        for element_name, element in self.elements.items():
            all_parents = []
            for parents_, elements_ in self.elements.items():
                if element_name in [x.name for x in elements_.immediate_children.values()]:
                    all_parents.append(parents_)
            element.parents = all_parents

    @staticmethod
    def __get_all_children_xsd(xsd_element: _Element) -> Dict[str, SchemaChild]:
        children = {}
        for child in xsd_element.findall(".//{http://www.w3.org/2001/XMLSchema}element"):
            if 'name' in child.attrib:
                child_name = child.attrib['name']
                children[child_name] = (SchemaChild(child_name,
                                                    True if child.attrib.get('minOccurs', None) is not None else False))
                # self.__element_parents[child.attrib['name']] = xsd_element.attrib['name']
        return children

    @staticmethod
    def __get_all_immediate_children(xsd_element: _Element) -> Dict[str, SchemaChild]:
        immediate_children = {}
        sequence = xsd_element.findall(".//{http://www.w3.org/2001/XMLSchema}sequence")
        if sequence and len(sequence) > 0:
            current_sequence = sequence[0]
            for child in current_sequence.getchildren():
                if 'name' in child.attrib:
                    child_name = child.attrib['name']
                    immediate_children[child_name] = (SchemaChild(child_name,
                                                                  True if child.attrib.get('minOccurs',
                                                                                           None) is not None else False))
        return immediate_children

    def add_element(self, element: ElementInfo):
        """
        Add an ElementInfo instance to the collection.

        :param element: The ElementInfo instance to add.
        """
        self.elements[element.name] = element

    def __getitem__(self, element_name: str) -> Optional[ElementInfo]:
        """
        Retrieve an ElementInfo instance by its name.

        :param element_name: The name of the ElementInfo to retrieve.
        :return: The ElementInfo instance with the given name, or None if not found.
        """
        return self.elements.get(element_name)

    def __repr__(self) -> str:
        """
        Provide a string representation of the SchemaCollection instance.

        :return: A string representing the SchemaCollection instance.
        """
        return f"SchemaCollection(elements={list(self.elements.values())})"


class Basics:
    __basic_type_list_for_predefined_basics = {'10', '11', '12', '13'}

    def __init__(self, type: str, id: str, desc: str, predefined_id: str, element: _Element):
        self.type = type
        self.id = id
        self.desc = desc
        self.predefined_id = predefined_id
        self.basic_type_element = element
        self.predefined_basic = type

    @property
    def mandatory_if_available_predefined_basic_id(self) -> Tuple[str, bool]:
        val = True
        if self.type in self.__basic_type_list_for_predefined_basics:
            if self.predefined_id is None:
                val = False
        return 'predefinedBasicID', val

    def __repr__(self) -> str:
        """
        Provide a string representation of the Basics instance.

        :return: A string representing the Basics instance.
        """
        return (f"Basics(type={self.type!r}, id={self.id!r}, desc={self.desc!r}, "
                f"predefined_id={self.predefined_id!r})")



@dataclass
class Validation:
    """
        check (str): The type of check e.g. structure
        check_obj (Check): Mandatory the check object
        status (str): The status
        technical_error_type: 'Teknisk fejlbeskrivelse' in the NOK file.
        error_xml_element: Name of the xml element, if applicable.
        error_row: The row number in the dataset where the error occurred, if applicable.
        complete_error_message: ONLY FOR DEBUGGING - A complete error message describing the error in detail.
        audit_trail: The audit trail, if applicable.
        special_error_message: If the error message needs to be dynamic.
    """
    check: str
    status: str
    check_obj: Check
    technical_error_type: Union[str, None] = None
    error_xml_element: Union[str, None] = None
    error_row: Union[int, None] = None
    complete_error_message: Union[str, None] = None
    audit_trail: Union[str, None] = None
    special_error_message: Union[List, None] = None

    @classmethod
    def read_from_pd_series(cls, pd_series):
        pd_series = pd_series.where(pd.notna(pd_series), None)
        data = pd_series.to_dict()
        lang = Language.dk
        cls_ = cls(check=data['Tjek'],
                   check_obj=Check(lang),
                   status=data['Status'],
                   technical_error_type=data['Teknisk fejlbeskrivelse'],
                   error_xml_element=data['Fejl XML element'],
                   error_row=int(data['Fejl række']) if pd.notna(data['Fejl række']) else None,
                   audit_trail=data['Fejl område'])
        return {Texts.check[lang]: cls_.check,
                Texts.status[lang]: cls_.status,
                Texts.error_row[lang]: cls_.error_row,
                Texts.error_area[lang]: cls_.audit_trail,
                Texts.error_xml_element[lang]: cls_.error_xml_element,
                Texts.technical_error_desc[lang]: cls_.technical_error_type,
                Texts.error_desc[lang]: data['Fejlbeskrivelse']}

    def __post_init__(self):
        self.__check_order = {self.check_obj.xml_read: 0,
                              self.check_obj.naming_check: 1,
                              self.check_obj.structure_check: 2,
                              self.check_obj.certificate_check: 3,
                              self.check_obj.signature_check: 4,
                              self.check_obj.value_check: 5}

    def __lt__(self, other):
        if self.__check_order[self.check] != self.__check_order[other.check]:
            return self.__check_order[self.check] < self.__check_order[other.check]
        else:
            return (self.error_row or float('inf')) < (other.error_row or float('inf'))

    def __eq__(self, other):
        return self.check == other.check and self.error_row == other.error_row

    def __error_message(self, error_messages_):
        message_ = error_messages_[self.technical_error_type] if self.technical_error_type is not None else None
        if self.special_error_message and message_:
            for idx, val_ in enumerate(self.special_error_message):
                if isinstance(val_, (int, float)):
                    message_ = message_.replace(f"[{idx + 1}]", f"{val_:,.2f}")
                else:
                    message_ = message_.replace(f"[{idx + 1}]", f"{val_}")
        return message_

    def res(self, error_messages_, lang):
        return {Texts.check[lang]: self.check,
                Texts.status[lang]: self.status,
                Texts.error_row[lang]: self.error_row,
                Texts.error_area[lang]: self.audit_trail,
                Texts.error_xml_element[lang]: self.error_xml_element,
                Texts.technical_error_desc[lang]: self.technical_error_type,
                Texts.error_desc[lang]: self.__error_message(error_messages_)}

    def __hash__(self):
        return hash((self.check, self.status, self.error_row, self.audit_trail, self.error_xml_element,
                     self.technical_error_type, str(self.special_error_message)))



def get_basic(all_basics: List[Basics], trans_type: str) -> Basics | None:
    for basic in all_basics:
        if basic.id == trans_type:
            return basic
    for basic in all_basics:
        if basic.desc == trans_type:
            # if can't find via basic.id, look in desc. If possible there then change id to desc.
            all_basics.append(Basics(type=basic.type,
                                     id=basic.desc,
                                     desc=basic.desc,
                                     predefined_id=basic.predefined_id,
                                     element=basic.basic_type_element
                                     ))
            return basic


def get_predefined_basic_id(basic: Basics):
    if basic and basic.predefined_id:
        return basic.predefined_id


def get_predefined_basic(basic: Basics):
    if basic and basic.predefined_basic:
        return basic.predefined_basic
