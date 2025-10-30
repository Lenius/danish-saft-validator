import getpass
import os
import time
from datetime import datetime
import re
from enum import Enum
from pathlib import Path
from typing import List, Union, Generator, Dict, Optional
from xml.etree.ElementTree import ElementTree

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from loguru import logger
from lxml import etree
from lxml.etree import _LogEntry, _Element, XMLSyntaxError

from modules.conventions.date_handler import date_time_handler
from modules.conventions.read_write import Write
from modules.create_config import create_config, get_language
from modules.conventions.error_handling import unexpected_error
from modules.conventions.variables import Validation, Status, Check, Report, \
    audit_trail_translated, SheetNames, MasterData, DeleteXML, Basics, Article, ArticleCollection, \
    SchemaCollection, EmployeeCollection, Employee
from modules.conventions.error_types import error_messages, XMLReadErrors, ArticleErrors, BasicErrors, EmployeeErrors
from modules.conventions.text_lang import Texts
from modules.conventions.file_system import FileSystem
from modules.conventions.variables_value_test import CashTrans, EventReport, Event, Metadata
from modules.validate_certificate import XMLCertificateValidator
from modules.validate_value_test import XMLValueTestValidator
from modules.validate_naming import XMLNamingValidator
from modules.validate_signature import XMLSignatureValidator
from modules.validate_structure import XMLStructureValidator, AddedDummies

if not FileSystem.config.exists():
    create_config()
lang = get_language()
username = getpass.getuser()

# Define custom log levels
logger.level("RED", no=38, color="<red>")
logger.level("YELLOW", no=39, color="<yellow>")
logger.level("WHITE", no=40, color="<white>")
logger.level("GREEN", no=41, color="<green>")


class XMLValidator:
    missing_child = 'Missing child element'
    xml_root_namespace = 'urn:StandardAuditFile-Taxation-CashRegister:DK'
    xml_root_find = f".//{{{xml_root_namespace}}}"
    __start_date: Union[datetime, None]
    __end_date: Union[datetime, None]
    xml_file: (Path, ElementTree)
    validation: List[Validation]
    __all_basics: List[Basics]
    __all_articles: Union[ArticleCollection, None]
    __all_employees: Union[EmployeeCollection, None]
    __metadata: Union[Metadata, None] = None
    __all_z_reports: Dict[str, List[EventReport]]
    __all_x_reports: Dict[str, List[EventReport]]
    __all_cash_trans: Dict[str, List[CashTrans]]
    __all_events: Dict[str, List[Event]]
    master_data: Union[MasterData, None]
    __line_mapping: Dict[_Element, tuple[int, bool]]
    naming_error: Union[bool, None]
    structure_error: Union[bool, None]
    certificate_error: Union[bool, None]
    signature_error: Union[bool, None]
    value_error: Union[bool, None]
    naming_validator: XMLNamingValidator
    structure_validator: XMLStructureValidator
    certificate_validator: XMLCertificateValidator
    signature_validator: XMLSignatureValidator
    value_test_validator: XMLValueTestValidator

    def __init__(self):
        self.session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.xsd_structure_in_xml = etree.parse(FileSystem.saf_t_xsd)
        self.xsd_structure = etree.XMLSchema(self.xsd_structure_in_xml)
        self.xsd_elements = self.xsd_structure_in_xml.findall(".//{http://www.w3.org/2001/XMLSchema}element")
        self.schema_dict = SchemaCollection(self.xsd_structure_in_xml)
        self.error_messages = error_messages(lang)
        self.__audit_trail_translated = audit_trail_translated(lang)
        self.__delete_xml = DeleteXML(lang)
        self.report = Report(lang)
        self.check = Check(lang)
        self.__sheet_names = SheetNames(lang)
        self.status = Status(lang)

    def __reset_all_class_variables(self):
        self.naming_validator = XMLNamingValidator(self)
        self.structure_validator = XMLStructureValidator(self)
        self.certificate_validator = XMLCertificateValidator(self)
        self.signature_validator = XMLSignatureValidator(self)
        self.value_test_validator = XMLValueTestValidator(self)
        self.__start_date: Union[datetime, None] = None
        self.__end_date: Union[datetime, None] = None
        self.xml_file: (Path, ElementTree) = ()
        self.validation: List[Validation] = []
        self.__all_basics: List[Basics] = []
        self.__all_articles: Union[ArticleCollection, None] = None
        self.__all_employees: Union[EmployeeCollection, None] = None
        self.__metadata: Union[Metadata, None] = None
        self.__all_z_reports: Dict[str, List[EventReport]] = {}
        self.__all_x_reports: Dict[str, List[EventReport]] = {}
        self.__all_event_reports: Dict[str, List[EventReport]] = {}
        self.__all_cash_trans: Dict[str, List[CashTrans]] = {}
        self.__all_events: Dict[str, List[Event]] = {}
        self.master_data: Union[MasterData, None] = None
        self.__line_mapping: Dict[_Element, tuple[int, bool]] = {}
        self.naming_error: Union[bool, None] = None
        self.structure_error: Union[bool, None] = None
        self.certificate_error: Union[bool, None] = None
        self.signature_error: Union[bool, None] = None
        self.value_error: Union[bool, None] = None

    def __read_xml(self, xml_path: str):
        """
        This private method reads an XML file, performs necessary validations,
        and prepares the data for further processing. It prompts the user for
        the path to the XML file, constructs an absolute path, and initializes
        various instance variables for handling the XML data.

        If the provided file is not of XML type or if the specified path does not
        exist, appropriate debug messages are logged. In case of an encoding error,
        it attempts to fix the issue.

        After successful parsing, it checks if the auditfile root needs adjustment
        and calls the appropriate method if necessary.
        """
        path = Path(xml_path)
        self.__reset_all_class_variables()

        encoding_error = False
        if path.suffix != '.xml':
            self.xml_file = (None, None)
            logger.debug(Texts.path_not_xml_file[lang])
        elif not path.exists():
            self.xml_file = (None, None)
            logger.debug(Texts.path_not_exist[lang])
        else:
            try:
                self.xml_file: (Path, etree) = (path, etree.parse(path))
            except XMLSyntaxError as e:
                self.xml_file = (path, None)
                if 'Input is not proper UTF-8' in e.msg:
                    """If encoding error, fix"""
                    encoding_error = self.__fix_encoding_error()
                elif 'Entity' in e.msg:
                    """XML reads & as entity, why replace with &amp;"""
                    with open(self.xml_file[0], "r") as infile:
                        data = infile.read()
                        data = data.replace('&', '&amp;')
                        self.xml_file = (self.xml_file[0], etree.ElementTree(etree.fromstring(data.encode("UTF-8"))))
                else:
                    raise XMLSyntaxError
            if self.xml_file[1]:
                """Checking if needs to fix auditfile root"""
                self.__fix_global_declaration(encoding_error=encoding_error)

    def __fix_encoding_error(self):
        """
        This private method addresses an encoding error when reading an XML file.
        It appends a Validation object to the validation list, indicating the error type.
        Then, it reads the XML file, encodes it in UTF-8, and replaces the original
        ElementTree with the corrected version.

        :return: True if the encoding error was successfully fixed, otherwise False.
        """
        self.log_validation_error_no_element(check_=self.check.xml_read,
                                             error_type=XMLReadErrors.encoding_error)
        with open(self.xml_file[0], "r") as infile:
            data = infile.read()
            self.xml_file = (self.xml_file[0], etree.ElementTree(etree.fromstring(data.encode("UTF-8"))))
            return True

    @staticmethod
    def extract_not_expected_element_name(error: _LogEntry):
        return error.message.split("'")[1]

    @staticmethod
    def extract_missing_element(error: _LogEntry) -> str | None:
        """
        Extract the missing element from the text.

        :return: The missing element as a string, or None if not found.
        """
        pattern = r"Expected is(?: one of)? \(\s*(.*?)\s*\)"
        matches = re.findall(pattern, error.message)
        if matches:
            elements = [element.strip() for element in matches[-1].split(',')]
            return elements[-1] if elements else None
        return None

    def extract_error_element_and_name(self, error: _LogEntry, expected_element_name: Optional[str] = None,
                                       added_dummies: Optional[AddedDummies] = None) -> tuple[_Element, str]:
        element_name = self.extract_not_expected_element_name(error)
        all_xml_tags = self.xml_file[1].findall(f".//{element_name}")
        if error.line == 0:
            xml_tags = [x for x in all_xml_tags if self.get_row_build(x)]
            if len(xml_tags) == 0:
                # takes parent element of added dummies - because Cython has turned that one's line to 0.
                all_added_dummies = [x[1] for x in added_dummies.all_added_elements]
                xml_tags = [x for x in all_xml_tags if x in all_added_dummies]
        else:
            xml_tags = [x for x in all_xml_tags if self.get_row_nr(x) == error.line]
        if xml_tags and len(xml_tags) > 1 and added_dummies:
            xml_tags = [x for x in xml_tags if
                        (self.extract_missing_element(error), x) not in added_dummies.all_added_elements]

        if self.missing_child not in error.message and expected_element_name and len(xml_tags) > 1:
            # Try to filter out replicated names by checking expected element names parent
            expected_element_name_ = self.extract_tag_from_tag(expected_element_name)
            list_of_parents = [f"{{{self.xml_root_namespace}}}{x}" for x in
                               self.schema_dict.elements[expected_element_name_].parents]
            xml_tags = [x for x in xml_tags if x.getparent().tag in list_of_parents]
        return xml_tags[0], element_name

    def extract_error_element(self, error: _LogEntry) -> _Element:
        return self.extract_error_element_and_name(error)[0]

    @staticmethod
    def __gen_parent_tree(xml_element: _Element) -> Generator[_Element, None, None]:
        """
        This static method generates a sequence of parent elements for a given XML element.

        :param xml_element: The XML element for which to generate parent elements.
        :yield: A generator yielding parent elements.
        """
        parent = xml_element.getparent()
        while parent is not None:
            yield parent
            parent = parent.getparent()

    def get_audit_trail(self, xml_element: _Element, get_translation: bool = True) -> str:
        """
        This private method retrieves the audit trail for a given XML element.

        :param xml_element: The XML element for which to retrieve the audit trail.
        :param get_translation: Whether to get the translated version of the audit trail.
        :return: The audit trail for the XML element as a string.
        """
        audit_trail = [self.extract_tag_from_element(parent) for parent in self.__gen_parent_tree(xml_element)]
        audit_trail.reverse()
        audit_trail = "/".join([x for x in audit_trail])
        if get_translation:
            if audit_trail in self.__audit_trail_translated.keys():
                return self.__audit_trail_translated[audit_trail]
            logger.debug(f"{Texts.missing_translation_audit_trail[lang]}{audit_trail}")
        return audit_trail

    def get_audit_trail_from_xml_error(self, error: _LogEntry) -> str:
        """
        This private method retrieves the audit trail from an XML error.

        :param error: The error object containing the error message.
        :return: The audit trail associated with the error as a string.
        """
        if 'validation root' not in error.message:
            error_element = self.extract_error_element(error)
            return self.get_audit_trail(xml_element=error_element)
        else:
            return self.__audit_trail_translated['auditfile']

    def __fix_global_declaration(self, encoding_error: bool = False):
        """
        This private method attempts to fix a global declaration error in the XML file.

        :param encoding_error: Flag indicating if an encoding error was encountered.
        """
        try:
            self.xsd_structure.assertValid(self.xml_file[1])
        except etree.DocumentInvalid:
            errors_ = [x for x in self.xsd_structure.error_log]
            if 'global declaration' in errors_[0].message:
                root = self.xml_file[1].getroot()
                with open(self.xml_file[0], "r", encoding='utf-8') as infile:
                    data = infile.read()
                    auditfile_ = [x for x in data.split("\n") if x.startswith('<auditfile')]
                    if auditfile_:
                        auditfile_ = auditfile_[0]
                    else:
                        auditfile_ = "<auditfile>"

                    if None not in root.nsmap and auditfile_ in data:
                        nsmap = """<auditfile xmlns="urn:StandardAuditFile-Taxation-CashRegister:DK">"""
                        data = data.replace(auditfile_, nsmap)
                    else:
                        nsmap = root.nsmap[None]
                        data = data.replace(nsmap, self.xml_root_namespace)
                if encoding_error:
                    self.xml_file = (self.xml_file[0], etree.ElementTree(etree.fromstring(data.encode("UTF-8"))))
                else:
                    self.xml_file = (self.xml_file[0], etree.ElementTree(etree.fromstring(data.encode())))
                self.validation.append(Validation(check=self.check.xml_read,
                                                  check_obj=self.check,
                                                  status=self.status.error,
                                                  technical_error_type=errors_[0].type_name,
                                                  error_xml_element=self.extract_not_expected_element_name(errors_[0]),
                                                  error_row=errors_[0].line,
                                                  complete_error_message=errors_[0].message,
                                                  audit_trail=self.get_audit_trail_from_xml_error(errors_[0])))

    def __validate_naming(self) -> bool:
        return self.naming_validator.validate()

    def __validate_structure(self) -> bool:
        return self.structure_validator.validate()

    def __validate_certificate(self) -> bool:
        return self.certificate_validator.validate()

    def __validate_signature(self) -> bool:
        return self.signature_validator.validate()

    def __validate_value_test(self) -> bool:
        return self.value_test_validator.validate()

    @staticmethod
    def extract_tag_from_element(element_: _Element):
        return element_.tag.split("}")[-1]

    @staticmethod
    def extract_tag_from_tag(tag_: str):
        return tag_.split("}")[-1]

    def __gen_all_basics(self):
        all_basics = []
        for basic in self.xml_file[1].findall(f"{self.xml_root_find}basic"):

            basics = {'basicType': None,
                      'basicID': None,
                      'predefinedBasicID': None,
                      'basicDesc': None
                      }
            try:
                for basic_child in basic.getchildren():
                    if isinstance(basic_child.tag, str):
                        basics[self.extract_tag_from_element(basic_child)] = basic_child.text
                all_basics.append(Basics(type=basics['basicType'],
                                         id=basics['basicID'],
                                         desc=basics['basicDesc'],
                                         predefined_id=basics['predefinedBasicID'],
                                         element=basic))
            except Exception as e:
                self.log_validation_error(self.check.structure_check, basic, BasicErrors.error_reading_basics)
        return all_basics

    def __gen_all_articles(self):
        art_id = 'artID'
        date_of_entry = 'dateOfEntry'
        art_group_id = 'artGroupID'
        art_desc = 'artDesc'
        all_articles = ArticleCollection()
        for article in self.xml_file[1].findall(f"{self.xml_root_find}article"):
            articles = {art_id: None,
                        date_of_entry: None,
                        art_group_id: None,
                        art_desc: None
                        }
            try:
                for article_child in article.getchildren():
                    articles[self.extract_tag_from_element(article_child)] = article_child.text
                all_articles.add_article(Article(id=articles[art_id],
                                                 desc=articles[art_desc],
                                                 group_id=articles[art_group_id],
                                                 date=articles[date_of_entry],
                                                 element=article))
            except Exception as e:
                self.log_validation_error(self.check.structure_check, article, ArticleErrors.error_reading_articles)
        return all_articles

    def __gen_all_employees(self):
        emp_id = 'empID'
        date_of_entry = 'dateOfEntry'
        first_name = 'firstName'
        sur_name = 'surName'
        role_type = 'roleType'
        role_type_desc = 'roleTypeDesc'
        all_employees = EmployeeCollection()
        for employee in self.xml_file[1].findall(f"{self.xml_root_find}employee"):
            employees = {emp_id: None,
                         date_of_entry: None,
                         first_name: None,
                         sur_name: None,
                         role_type: None,
                         role_type_desc: None
                         }
            try:
                for element_child in employee.getchildren():
                    if element_child.getchildren():
                        for element_child_child in element_child.getchildren():
                            employees[self.extract_tag_from_element(element_child_child)] = element_child_child.text
                    else:
                        employees[self.extract_tag_from_element(element_child)] = element_child.text
                all_employees.add_employee(Employee(id=employees[emp_id],
                                                    date=employees[date_of_entry],
                                                    first_name=employees[first_name],
                                                    sur_name=employees[sur_name],
                                                    role_type=employees[role_type],
                                                    role_type_desc=employees[role_type_desc],
                                                    element=employee))
            except Exception as e:
                self.log_validation_error(self.check.structure_check, employee, EmployeeErrors.error_reading_employees)
        return all_employees

    def __print_validation(self):
        """
        This private method prints the validation results to the debug log.
        """
        for validation in self.validation:
            logger.debug(validation.res(self.error_messages, lang))

    def __get_master_data(self) -> MasterData:
        """
        This private method retrieves master data from the XML file.

        :return: An instance of MasterData containing company information.
        """

        def __get_specific_xml_element(element_name: str, audit_trail_lookup: str):
            """
            Helper function to extract a specific XML element.

            :param element_name: The name of the XML element to retrieve.
            :param audit_trail_lookup: The audit trail to match for element retrieval.
            :return: The text content of the specified XML element, or an error message if not found.
            """
            try:
                elements = self.xml_file[1].findall(f"{self.xml_root_find}{element_name}")
                for element in elements:
                    audit_trail = self.get_audit_trail(element, get_translation=False)
                    if audit_trail_lookup == audit_trail:
                        return element.text
            except:
                pass
            return self.error_messages['MASTERDATA']

        os_data = os.stat(self.xml_file[0])
        return MasterData(
            company_id=__get_specific_xml_element(element_name="companyIdent", audit_trail_lookup="auditfile/company"),
            company_name=__get_specific_xml_element(element_name="companyName", audit_trail_lookup="auditfile/company"),
            software_company=__get_specific_xml_element(element_name="softwareCompanyName",
                                                        audit_trail_lookup="auditfile/header"),
            software_desc=__get_specific_xml_element(element_name="softwareDesc",
                                                     audit_trail_lookup="auditfile/header"),
            software_version=__get_specific_xml_element(element_name="softwareVersion",
                                                        audit_trail_lookup="auditfile/header"),
            created_at=datetime.fromtimestamp(os_data.st_ctime),
            modified_at=datetime.fromtimestamp(os_data.st_mtime),
            last_access=datetime.fromtimestamp(os_data.st_mtime))

    @staticmethod
    def remove_duplicates_and_sort_validation(validation_list: List[Validation]):
        return sorted(list(set(validation_list)))

    @property
    def base_folder_of_xml_file(self):
        if self.xml_file:
            return self.xml_file[0].parent.parent

    @property
    def xml_file_name(self):
        if self.xml_file:
            return self.xml_file[0].stem

    @property
    def prefix(self):
        if any([x.status == self.status.error for x in self.validation if x.check != self.check.value_check]):
            return self.report.nok_prefix
        elif any([x.status == self.status.error for x in self.validation if x.check == self.check.value_check]):
            return self.report.flag_prefix
        else:
            return self.report.ok_prefix



    def __write_report(self, print_errors: bool = False):
        """
        This private method generates and writes a validation report to an Excel file.

        :param print_errors: Flag indicating whether to print errors to the console.
        """
        prefix = self.prefix
        filename_ = f"{prefix}{self.xml_file_name}.xlsx"
        path = Path(f"{self.base_folder_of_xml_file}/{self.report.checked}/{filename_}")
        if not path.parent.exists():
            path.parent.mkdir()

        Write.excel_multiple_sheets(file_path=path, data={self.__sheet_names.master_data: [self.master_data.res(lang)],
                                                          self.__sheet_names.check: [x.res(self.error_messages, lang)
                                                                                     for x in self.validation]})
        if print_errors:
            self.__print_validation()
        if prefix == self.report.nok_prefix:
            logger.log("RED", f"{Texts.errors_found[lang]}{path.resolve()}")
        elif prefix == self.report.flag_prefix:
            logger.log("YELLOW", f"{Texts.flag_errors_found[lang]}{path.resolve()}")
        else:
            logger.log("GREEN", f"{Texts.no_errors_found[lang]}{path.resolve()}")

    @staticmethod
    def certificate(pem_format: str):
        """
        Static method to load a PEM formatted certificate and return an X.509 certificate object.

        :param pem_format: The PEM formatted certificate as a string.
        :return: An X.509 certificate object.
        """
        return x509.load_pem_x509_certificate(
            "".join([x.strip() for x in pem_format.split("\n")]).encode('utf-8'), default_backend())


    def __run_function(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e_:
            if self.xml_file[0] is not None:
                logger.debug(self.xml_file[0].resolve())
            unexpected_error(e_)
            return None

    def __check_if_no_errors(self):
        if not self.naming_error:
            self.validation.append(Validation(check=self.check.naming_check,
                                              check_obj=self.check,
                                              status=self.status.ok))
        if not self.structure_error:
            self.validation.append(Validation(check=self.check.structure_check,
                                              check_obj=self.check,
                                              status=self.status.ok))
        if not self.certificate_error:
            self.validation.append(Validation(check=self.check.certificate_check,
                                              check_obj=self.check,
                                              status=self.status.ok))
        if not self.signature_error:
            self.validation.append(Validation(check=self.check.signature_check,
                                              check_obj=self.check,
                                              status=self.status.ok))
        if not self.value_error:
            self.validation.append(Validation(check=self.check.value_check,
                                              check_obj=self.check,
                                              status=self.status.ok))

    def __delete_xml_file(self, delete_xml=None):
        if delete_xml is None:
            time.sleep(0.1)
            delete_or_not = input(Texts.report_was_written[lang]).lower()
            while delete_or_not not in [val for val in self.__delete_xml]:
                delete_or_not = input(Texts.report_was_written_delete[lang]).lower()
        else:
            delete_or_not = self.__delete_xml.ja if delete_xml else self.__delete_xml.nej

        if delete_or_not == self.__delete_xml.ja:
            self.xml_file[0].unlink()

    def __build_line_mapping(self):
        for elem in self.xml_file[1].iter():
            if elem.sourceline:
                self.__line_mapping[elem] = (elem.sourceline, False)

    def add_to_line_mapping(self, key, value):
        self.__line_mapping[key] = value

    def get_row_build(self, elem: _Element):
        return self.__line_mapping[elem][1]

    def get_row_nr(self, elem: _Element):
        row_ = self.__line_mapping[elem][0]
        if row_ == 0:
            return self.__line_mapping[elem.getparent()][0]
        return row_

    def __gen_all_event_reports(self):
        for cash_reg in self.xml_file[1].findall(f"{self.xml_root_find}cashregister"):
            reg_id = cash_reg.find(f"{self.xml_root_find}registerID").text
            EventReport.reset_class_variables()
            for event_report in cash_reg.findall(f"{self.xml_root_find}eventReport"):
                report_type = event_report.find(f"{self.xml_root_find}reportType")
                if report_type is not None:  # and report_type.text == report_type_:
                    event_report_obj = EventReport(event_report)

                    if reg_id in self.__all_z_reports and report_type.text == 'Z report':
                        self.__all_z_reports[reg_id].append(event_report_obj)
                    elif reg_id in self.__all_x_reports and report_type.text == 'X report':
                        self.__all_x_reports[reg_id].append(event_report_obj)
                    else:
                        if report_type.text == 'Z report':
                            self.__all_z_reports[reg_id] = [event_report_obj]
                        elif report_type.text == 'X report':
                            self.__all_x_reports[reg_id] = [event_report_obj]
                    if reg_id in self.__all_event_reports:
                        self.__all_event_reports[reg_id].append(event_report_obj)
                    else:
                        self.__all_event_reports[reg_id] = [event_report_obj]

    def __gen_all_cash_trans(self) -> Dict[str, List[CashTrans]]:
        all_cash_trans = {}
        for cash_reg in self.xml_file[1].findall(f"{self.xml_root_find}cashregister"):
            CashTrans.reset_class_variables()
            reg_id = cash_reg.find(f"{self.xml_root_find}registerID").text
            for cash_trans in cash_reg.findall(f"{self.xml_root_find}cashtransaction"):
                cash_trans_obj = CashTrans(self, cash_trans, self.all_basics, self.all_articles)
                if reg_id in all_cash_trans:
                    all_cash_trans[reg_id].append(cash_trans_obj)
                else:
                    all_cash_trans[reg_id] = [cash_trans_obj]
        return all_cash_trans

    def __gen_start_end_date(self):
        start_date = self.xml_file[1].find(f"{self.xml_root_find}startDate").text
        end_date = self.xml_file[1].find(f"{self.xml_root_find}endDate").text
        self.__start_date = date_time_handler.convert_to_date(start_date)
        self.__end_date = date_time_handler.convert_to_date(end_date)

    def __gen_all_events(self) -> Dict[str, List[Event]]:
        all_events = {}
        for cash_reg in self.xml_file[1].findall(f"{self.xml_root_find}cashregister"):
            reg_id = cash_reg.find(f"{self.xml_root_find}registerID").text
            for event in cash_reg.findall(f"{self.xml_root_find}event"):
                event_obj = Event(event, self.all_basics)
                if reg_id in all_events:
                    all_events[reg_id].append(event_obj)
                else:
                    all_events[reg_id] = [event_obj]
        return all_events

    def __gen_metadata(self) -> Metadata:
        return Metadata(header=self.xml_file[1].find(f"{self.xml_root_find}header"),
                        company=self.xml_file[1].find(f"{self.xml_root_find}company"))

    def log_validation_error(self, check_, element: _Element, error_type: Union[Enum, str],
                             special_error_msg: Union[None, List] = None):
        if isinstance(error_type, Enum):
            error_type = error_type.value
        self.validation.append(Validation(
            check=check_,
            check_obj=self.check,
            status=self.status.error,
            technical_error_type=error_type,
            error_xml_element=self.extract_tag_from_element(element),
            error_row=self.get_row_nr(element),
            audit_trail=self.get_audit_trail(element),
            special_error_message=special_error_msg
        ))

    def log_validation_error_no_element(self, check_, error_type: Union[Enum, str]):
        if isinstance(error_type, Enum):
            error_type = error_type.value
        self.validation.append(Validation(check=check_,
                                          check_obj=self.check,
                                          status=self.status.error,
                                          technical_error_type=error_type))

    @property
    def end_date(self) -> datetime:
        if not self.__end_date:
            self.__gen_start_end_date()
        return self.__end_date

    @property
    def start_date(self) -> datetime:
        if not self.__start_date:
            self.__gen_start_end_date()
        return self.__start_date

    @property
    def all_articles(self) -> ArticleCollection:
        if not self.__all_articles:
            self.__all_articles = self.__gen_all_articles()
        return self.__all_articles

    @property
    def all_employees(self) -> EmployeeCollection:
        if not self.__all_employees:
            self.__all_employees = self.__gen_all_employees()
        return self.__all_employees

    @property
    def metadata(self) -> Metadata:
        if not self.__metadata:
            self.__metadata = self.__gen_metadata()
        return self.__metadata

    @property
    def all_basics(self) -> List[Basics]:
        if not self.__all_basics:
            self.__all_basics = self.__gen_all_basics()
        return self.__all_basics

    @property
    def z_reports(self) -> Dict[str, List[EventReport]]:
        if not self.__all_event_reports:
            self.__gen_all_event_reports()
        return self.__all_z_reports

    @property
    def x_reports(self) -> Dict[str, List[EventReport]]:
        if not self.__all_event_reports:
            self.__gen_all_event_reports()
        return self.__all_x_reports

    @property
    def event_reports(self) -> Dict[str, List[EventReport]]:
        if not self.__all_event_reports:
            self.__gen_all_event_reports()
        return self.__all_event_reports

    @property
    def cash_transactions(self) -> Dict[str, List[CashTrans]]:
        if not self.__all_cash_trans:
            self.__all_cash_trans = self.__gen_all_cash_trans()
        return self.__all_cash_trans

    @property
    def events(self) -> Dict[str, List[Event]]:
        if not self.__all_events:
            self.__all_events = self.__gen_all_events()
        return self.__all_events

    def run_analysis(self, xml_file_path: str, delete_xml_file: bool = None, write_report: bool = True,
                     run_value_test: bool = True):
        """
        Runs the analysis process on the provided XML file.

        This method orchestrates the analysis process by calling various validation methods.
        It handles exceptions and adds corresponding validation errors if any occur.

        :return: List[Validation]
        """
        try:
            self.__read_xml(xml_file_path)
        except Exception as e_:
            if self.xml_file[0] is None:
                return
            self.xml_file = (self.xml_file[0], None)
            self.log_validation_error_no_element(self.check.xml_read, XMLReadErrors.read_error)
            for check_ in [self.check.structure_check, self.check.certificate_check, self.check.signature_check]:
                self.log_validation_error_no_element(check_, XMLReadErrors.read_error_other_checks)
            self.structure_error = True
            self.certificate_error = True
            self.signature_error = True
        if self.xml_file[0] is None:
            return
        self.master_data = self.__run_function(self.__get_master_data)
        self.__run_function(self.__validate_naming)
        if self.xml_file[1]:
            self.__run_function(self.__build_line_mapping)
            self.__run_function(self.__validate_structure)
            self.__run_function(self.__validate_certificate)
            self.__run_function(self.__validate_signature)
            if run_value_test:
                self.__run_function(self.__validate_value_test)
        self.__run_function(self.__check_if_no_errors)
        self.validation = self.__run_function(self.remove_duplicates_and_sort_validation, self.validation)
        if write_report:
            self.__run_function(self.__write_report, False)
        self.__run_function(self.__delete_xml_file, delete_xml_file)

        return self.validation


if __name__ == '__main__':
    try:
        logger.info(Texts.init_model[lang])
        xml_validation = XMLValidator()
        logger.info(Texts.model_init[lang])

        """Runs an inputted XML file"""
        while True:
            time.sleep(0.1)
            path_ = input(Texts.path_to_xml[lang]).strip()

            # Mulighed for at afslutte manuelt med tomt input
            if not path_:
                logger.info("Ingen sti angivet. Programmet afsluttes.")
                break

            xml_validation.run_analysis(
                xml_file_path=path_,
                write_report=True
            )

    except KeyboardInterrupt:
        print("\n[INFO] Afbrudt af brugeren. Lukker ned…")
        logger.info("Programmet blev afbrudt af brugeren (Ctrl+C).")
        sys.exit(0)

    except Exception as e:
        logger.exception(f"Uventet fejl: {e}")
        sys.exit(1)

