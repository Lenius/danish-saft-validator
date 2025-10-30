from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Set

from lxml import etree
from lxml.etree import _LogEntry, _Element
from tqdm import tqdm

from modules.conventions.variables import Validation
from modules.conventions.error_types import StructureErrors
from modules.conventions.dummy_variables import get_dummy

if TYPE_CHECKING:
    from main import XMLValidator


@dataclass
class AddedDummy:
    parent_element: _Element
    added_element: _Element
    row: int

    def __post_init__(self):
        self.name_of_added_element = self.added_element.tag

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AddedDummy):
            return NotImplemented
        return (self.parent_element == other.parent_element and
                self.added_element.tag == other.added_element.tag)

    def __hash__(self) -> int:
        return hash((self.parent_element, self.added_element.tag))


@dataclass
class AddedDummies:
    dummies: Set[AddedDummy] = field(default_factory=set)

    def add_dummy(self, parent_element: _Element, added_element: _Element, row: int) -> None:
        """
        Adds a new dummy to the set if it doesn't already exist.

        :param parent_element: The parent XML element.
        :param added_element: The XML element to be added.
        """
        new_dummy = AddedDummy(parent_element, added_element, row)
        if new_dummy not in self.dummies:
            self.dummies.add(new_dummy)

    def has_dummy_by_element(self, parent_element: _Element, added_element: _Element) -> bool:
        """
        Checks if a dummy with the specified parent element and added element already exists.

        :param parent_element: The parent XML element.
        :param added_element: The XML element to check.
        :return: True if the dummy exists, False otherwise.
        """
        dummy_to_check = AddedDummy(parent_element, added_element)
        return dummy_to_check in self.dummies

    def has_dummy_by_name(self, parent_element: _Element, element_name: str) -> bool:
        """
        Checks if a dummy with the specified parent element and element name already exists.

        :param parent_element: The parent XML element.
        :param element_name: The name of the element to check.
        :return: True if the dummy exists, False otherwise.
        """
        for dummy in self.dummies:
            if dummy.parent_element == parent_element and dummy.name_of_added_element == element_name:
                return True
        return False

    @property
    def all_added_elements(self):
        return [(x.name_of_added_element, x.parent_element) for x in self.dummies]


class XMLStructureValidator:
    __error_element_not_exists = 'SCHEMAV_ELEMENT_CONTENT'

    def __init__(self, validator_: 'XMLValidator'):
        self.validator = validator_
        self.all_identical_structure_errors = None
        self.structural_error = None
        self.handled_error = None
        self.added_dummies = AddedDummies()

    def __get_dummy_text(self, full_element_name: str):
        """
        This private method retrieves dummy text based on the provided element name.

        :param full_element_name: The name of the XML element to get dummy text for.
        :return: The dummy text for the element.
        """
        return get_dummy[self.__get_type_from_xsd(full_element_name=full_element_name)]

    @staticmethod
    def __get_element_name_from_full_element_name(full_element_name: str):
        return full_element_name.split("}")[-1]

    def __get_type_from_xsd(self, full_element_name: str):
        """
        This private method gets the data type of an element from the XSD structure.

        :param full_element_name: The name of the XML element.
        :return: The data type of the element.
        """
        full_element_name = self.__get_element_name_from_full_element_name(full_element_name)
        for xsd_element in self.validator.xsd_elements:
            if 'name' in xsd_element.attrib:
                if xsd_element.attrib['name'] == full_element_name:
                    if 'type' not in xsd_element.attrib.keys():
                        return 'Empty'
                    elif 'String'.lower() in xsd_element.attrib['type'].lower() and not 'report' in xsd_element.attrib['type'].lower():
                        return 'String'
                    elif 'Nonnegativeinteger'.lower() in xsd_element.attrib['type'].lower():
                        return 'Nonnegativeinteger'
                    elif 'IdentificationString'.lower() in xsd_element.attrib['type'].lower():
                        return 'IdentificationString'
                    return xsd_element.attrib['type']
            elif 'ref' in xsd_element.attrib:
                if xsd_element.attrib['ref'] == f"ds:{full_element_name}":
                    return 'Extrasignature'

    def __line_mapping_log_add_dummy(self, element_to_add: _Element, error: _LogEntry, expected_element_name: str,
                                     element_for_row_nr: _Element):
        self.validator.add_to_line_mapping(key=element_to_add,
                                           value=(self.validator.get_row_nr(element_for_row_nr), True))
        self.log_structural_error(element=element_to_add, error=error,
                                  error_tag_name=self.__get_element_name_from_full_element_name(expected_element_name))
        self.added_dummies.add_dummy(parent_element=element_to_add.getparent(), added_element=element_to_add,
                                     row=self.validator.get_row_nr(element_to_add))

    def add_expected_element_above_not_expected(self, not_expected_element: _Element, expected_element_name: str,
                                                error: _LogEntry):
        element_to_add = etree.Element(expected_element_name)
        element_to_add.text = self.__get_dummy_text(expected_element_name)
        not_expected_element.addprevious(element_to_add)
        self.__line_mapping_log_add_dummy(element_to_add, error, expected_element_name, not_expected_element)

    def add_missing_child_element(self, parent_element: _Element, expected_element_name: str, error: _LogEntry):
        element_to_add = etree.SubElement(parent_element, expected_element_name)
        element_to_add.text = self.__get_dummy_text(expected_element_name)
        self.__line_mapping_log_add_dummy(element_to_add, error, expected_element_name, parent_element)

    def handle_out_of_sequence_error(self, parent_element, not_expected_element, not_expected_element_name):
        if self.added_dummies.has_dummy_by_name(parent_element, not_expected_element_name):
            self.validator.log_validation_error(self.validator.check.structure_check, element=not_expected_element,
                                                error_type=StructureErrors.out_of_sequence)
            parent_element.remove(not_expected_element)
            self.handled_error = True

    def handle_if_element_should_not_exist(self, not_expected_element: _Element, parent_element: _Element):
        """
        This method checks against the XSD schema if the error element exists in the correct place.
        If not, it deletes it.

        :param not_expected_element: The XML error element
        :param parent_element: The parent element of the not_expected_element in the XML
        :return: bool indicating if the element should be deleted
        """
        parent_name = self.validator.extract_tag_from_element(parent_element)
        not_expected_element_name = self.validator.extract_tag_from_element(not_expected_element)
        # Check if the parent element exists in the schema dictionary
        if parent_name in self.validator.schema_dict.elements:
            # Check if the not expected element name is in the list of children for the parent
            if not_expected_element_name not in [x.name for x in self.validator.schema_dict.elements[parent_name].immediate_children.values()]:
                self.validator.log_validation_error(check_=self.validator.check.structure_check,
                                                    element=not_expected_element,
                                                    error_type=StructureErrors.out_of_sequence)
                parent_element.remove(not_expected_element)
                self.handled_error = True

    def handle_multiple_of_same_element(self, not_expected_element: _Element,
                                        not_expected_element_name: str, parent_element: _Element):
        if not not_expected_element.getchildren():
            all_identical_elements = [x for x in parent_element.getchildren() if x.tag == not_expected_element_name]
            if len(all_identical_elements) > 1:
                while len(all_identical_elements) > 1:
                    self.validator.log_validation_error(self.validator.check.structure_check,
                                                        element=all_identical_elements[-1],
                                                        error_type=StructureErrors.out_of_sequence)
                    parent_element.remove(all_identical_elements[-1])
                    all_identical_elements.pop(-1)
                self.handled_error = True

    def handle_missing_child(self, error: _LogEntry, parent_element: _Element, expected_element_name: str):
        if self.validator.missing_child in error.message:
            self.add_missing_child_element(parent_element, expected_element_name, error)
            self.handled_error = True

    def handle_want_to_build_optional(self, not_expected_element: _Element, expected_element_name: str, parent_element: _Element):
        parent_name = self.validator.extract_tag_from_element(parent_element)
        expected_element_name_ = self.validator.extract_tag_from_tag(expected_element_name)
        # not_expected_element_name = self.validator.extract_tag_from_element(not_expected_element)
        # Check if the parent element exists in the schema dictionary
        if parent_name in self.validator.schema_dict.elements:
            # Check if the not expected element name is in the list of children for the parent
            if expected_element_name_ in [x.name for x in self.validator.schema_dict.elements[parent_name].immediate_children.values()]:
                if self.validator.schema_dict.elements[parent_name].immediate_children[expected_element_name_].optional is True:
                    self.validator.log_validation_error(check_=self.validator.check.structure_check,
                                                        element=not_expected_element,
                                                        error_type=StructureErrors.out_of_sequence)
                    parent_element.remove(not_expected_element)
                    self.handled_error = True

    def handle_structural_errors(self, all_errors: List[_LogEntry]):
        first_error = all_errors[0]
        self.all_identical_structure_errors = [x for x in all_errors if x.message == first_error.message]
        expected_element_name = self.validator.extract_missing_element(first_error)
        # for structure_error in tqdm(self.all_identical_structure_errors, desc=f"Fixing structure error on expected_element_name: {expected_element_name}"):
        for structure_error in self.all_identical_structure_errors:
            self.handled_error = None
            not_expected_element, not_expected_element_name = self.validator.extract_error_element_and_name(
                structure_error, expected_element_name, self.added_dummies)
            parent_element = not_expected_element.getparent()

            if self.handled_error is None:
                self.handle_if_element_should_not_exist(not_expected_element, parent_element)
            if self.handled_error is None and self.validator.missing_child not in structure_error.message:
                self.handle_out_of_sequence_error(parent_element, not_expected_element, not_expected_element_name)
            if self.handled_error is None:
                self.handle_multiple_of_same_element(not_expected_element, not_expected_element_name, parent_element)
            if self.handled_error is None:
                self.handle_missing_child(error=structure_error, parent_element=not_expected_element,
                                          expected_element_name=expected_element_name)
            if self.handled_error is None:
                self.handle_want_to_build_optional(not_expected_element, expected_element_name, parent_element)
            if self.handled_error is None:
                self.add_expected_element_above_not_expected(not_expected_element, expected_element_name,
                                                             error=structure_error)
        self.validate()

    def handle_non_structural_errors(self, all_errors: List[_LogEntry]):
        """Handles all errors that are not structural related"""
        for error in all_errors:
            xml_error_element = self.validator.extract_error_element(error)
            self.validator.log_validation_error(self.validator.check.structure_check, element=xml_error_element,
                                                error_type=error.type_name)

    def validate(self):
        try:
            self.validator.xsd_structure.assertValid(self.validator.xml_file[1])
        except etree.DocumentInvalid:
            self.structural_error = None
            self.validator.structure_error = True
            all_errors = [x for x in self.validator.xsd_structure.error_log]
            all_structure_errors = [x for x in all_errors if x.type_name == self.__error_element_not_exists]

            if all_structure_errors:
                self.handle_structural_errors(all_structure_errors)
            else:
                self.handle_non_structural_errors(all_errors)

    def log_structural_error(self, element: _Element, error: _LogEntry, error_tag_name):
        self.validator.validation.append(Validation(check=self.validator.check.structure_check,
                                                    check_obj=self.validator.check,
                                                    status=self.validator.status.error,
                                                    technical_error_type=error.type_name,
                                                    error_xml_element=error_tag_name,
                                                    error_row=self.validator.get_row_nr(element),
                                                    audit_trail=self.validator.get_audit_trail(element)))
