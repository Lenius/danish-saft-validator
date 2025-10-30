import datetime
import re
from enum import Enum
from typing import Optional, List, Union, Tuple, TYPE_CHECKING

from lxml.etree import _Element

from modules.conventions.date_handler import date_time_handler
from modules.conventions.error_types import StructureErrors
from modules.conventions.variables import Basics, get_predefined_basic_id, get_basic, ArticleCollection, \
    get_predefined_basic

if TYPE_CHECKING:
    from main import XMLValidator


def to_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(0)


def get_child_element(element: _Element, element_name: str, add_element_name: str = None):
    __root = "{urn:StandardAuditFile-Taxation-CashRegister:DK}"
    value = None
    if add_element_name:
        element = element.find(f"{__root}{element_name}")
        if element is not None:
            value = element.find(f"{__root}{add_element_name}")
    else:
        value = element.find(f"{__root}{element_name}")
    return value


def get_text_from_element(element) -> str | None:
    if element is not None:
        return element.text


def get_child_text(element: _Element, element_name: str, add_element_name: str = None) -> str | None:
    value = get_child_element(element, element_name, add_element_name)
    return get_text_from_element(value)


def get_all_children(element: _Element, element_name: str, add_element_name: str = None):
    __root = "{urn:StandardAuditFile-Taxation-CashRegister:DK}"
    value = None
    if add_element_name:
        element = element.findall(f"{__root}{element_name}")
        if element is not None:
            value = element.findall(f"{__root}{add_element_name}")
    else:
        value = element.findall(f"{__root}{element_name}")
    return value


tolerance = 1e-3


class BaseElement:
    correct_predefined_basic_totals: List[str] = []

    def __init__(self, element: _Element, basic_type_element: _Element,
                 all_basics: Union[List['Basics'], None] = None):
        """
        Initialize the base element with common properties.

        :param element: The XML element to parse.
        :param basic_type_element: The type of the basic element.
        :param all_basics: Optional list of all basics.
        """
        self.element = element
        self.basic_type_element = basic_type_element
        self.basic_type = get_text_from_element(self.basic_type_element)
        self.all_basics = all_basics

    @property
    def basic(self):
        if self.all_basics and self.basic_type:
            return get_basic(self.all_basics, self.basic_type)
        return None

    @property
    def predefined_basic(self) -> Union[str, None]:
        """
        Retrieve the predefined basic for the element based on all_basics and basic_type.

        :return: The predefined basic if available, otherwise None.
        """
        if self.basic:
            return get_predefined_basic_id(self.basic)
        return None

    @property
    def relation_to_basic_check(self) -> bool:
        """
        Check if the relation to basic is valid.

        :return: True if predefined_basic is not None, otherwise False.
        """
        return self.basic is not None

    def is_correct_predefined_basic(self, predefined_basic: str) -> bool:
        """
        Determine if the predefined basic is correct. Can be overridden by subclasses.

        :param predefined_basic: The predefined basic to check.
        :return: True if the predefined basic is correct, otherwise False.
        """
        if not self.__class__.correct_predefined_basic_totals:
            return True
        return predefined_basic[:2] in self.__class__.correct_predefined_basic_totals

    @property
    def correct_predefined_basic_check(self) -> bool:
        """
        Check if the predefined basic is correct based on accepted totals and relation to basic check.

        :return: True if correct, otherwise False.
        """
        if not self.relation_to_basic_check:
            return False
        if isinstance(self.predefined_basic, str):
            return self.is_correct_predefined_basic(self.predefined_basic)
        return False

    def mandatory_if_available(self, attribute: str, predefined_basic_list: set[str]) -> bool:
        """
        Check if the attribute is mandatory if available.

        :param attribute: The attribute to check.
        :param predefined_basic_list: The list of predefined basics.
        :return: True if the attribute is mandatory if available, otherwise False.
        """
        attr_value = getattr(self, attribute, None)
        if self.predefined_basic in predefined_basic_list:
            if isinstance(attr_value, list) and len(attr_value) == 0:
                return False
            if attr_value is not None:
                return True
            return False
        return True

    def __repr__(self):
        """
        Return a string representation of the element.
        """
        raise NotImplementedError("Subclasses must implement __repr__")


class Event(BaseElement):
    correct_predefined_basic_totals = ['06', '13', '14']
    __predefined_basic_trans_id_list = {'13010', '13011', '13012', '13013', '13014', '13015', '13016', '13019', '13028'}
    __predefined_basic_event_report_list = {'13008', '13009'}

    def __init__(self, event: _Element, all_basics: Union[List[Basics], None] = None):
        self.element = event
        basic_type = get_child_element(self.element, 'eventType')
        super().__init__(self.element, basic_type, all_basics)
        self.all_basics = all_basics
        self.event_id = get_child_text(self.element, 'eventID')
        self.event_type = get_text_from_element(basic_type)
        self.trans_id = get_child_text(self.element, 'transID')
        self.emp_id = get_child_text(self.element, 'empID')
        self.event_text = get_child_text(self.element, 'eventText')
        self.event_date = get_child_text(self.element, 'eventDate')
        self.event_time = get_child_text(self.element, 'eventTime')
        self.event_datetime = date_time_handler.convert_to_datetime(self.event_date, self.event_time)
        self.event_datetime_min = date_time_handler.truncate_seconds(self.event_datetime)
        self.event_report = get_child_element(self.element, 'eventReport')

    def is_correct_predefined_basic(self, predefined_basic: str) -> bool:
        """
        Determine if the predefined basic is correct, with an additional check for Event.

        :param predefined_basic: The predefined basic to check.
        :return: True if the predefined basic is correct, otherwise False.
        """
        return (predefined_basic[:2] in self.__class__.correct_predefined_basic_totals or
                predefined_basic.startswith('6'))

    @property
    def predefined_basic(self) -> Union[str, None]:
        """
        Retrieve the predefined basic for the element based on all_basics and basic_type.

        :return: The predefined basic if available, otherwise None.
        """
        if self.basic:
            predefined_basic_id = get_predefined_basic_id(self.basic)
            if predefined_basic_id:
                return predefined_basic_id
            return get_predefined_basic(self.basic)
        return None

    @property
    def mandatory_if_available_event_report(self) -> Tuple[str, bool]:
        return 'eventReport', self.mandatory_if_available('event_report', self.__predefined_basic_event_report_list)

    @property
    def mandatory_if_available_trans_id(self) -> Tuple[str, bool]:
        return 'transID', self.mandatory_if_available('trans_id', self.__predefined_basic_trans_id_list)

    def __repr__(self) -> str:
        return (f"Event(event_id={self.event_id!r}, trans_id={self.trans_id!r}, "
                f"emp_id={self.emp_id!r}, event_text={self.event_text!r}, "
                f"event_datetime={self.event_datetime!r}, predefined_basic={self.predefined_basic!r}, "
                f"correct_predefined_basic_check={self.correct_predefined_basic_check!r}, "
                f"relation_to_basic_check={self.relation_to_basic_check!r})")


class Payment(BaseElement):
    correct_predefined_basic_totals = ['12']
    __predefined_basic_payment_ref = {'12002', '12003', '12011'}

    def __init__(self, payment: _Element, all_basics: Union[List[Basics], None] = None):
        self.element = payment
        basic_type = get_child_element(self.element, 'paymentType')
        super().__init__(self.element, basic_type, all_basics)
        self.all_basics = all_basics
        self.payment_type = get_text_from_element(basic_type)
        self.paid_amnt = get_child_text(self.element, 'paidAmnt')
        self.paid_amnt_fl = to_float(get_child_text(self.element, 'paidAmnt'))
        self.emp_id = get_child_text(self.element, 'empID')
        self.cur_code = get_child_text(self.element, 'curCode')
        self.exchange_rate = get_child_text(self.element, 'exchRt')
        self.payment_ref_id = get_child_text(self.element, 'paymentRefID')

    @property
    def mandatory_if_available_payment_ref_id(self) -> Tuple[str, bool]:
        return 'paymentRefID', self.mandatory_if_available('payment_ref_id', self.__predefined_basic_payment_ref)

    def __repr__(self):
        return (f"Payment(payment_type={self.payment_type!r}, paid_amnt={self.paid_amnt!r}, emp_id={self.emp_id!r}, "
                f"cur_code={self.cur_code!r}, payment_ref_id={self.payment_ref_id!r}, "
                f"mandatory_if_available_payment_ref_id={self.mandatory_if_available_payment_ref_id!r})")


class CTLine(BaseElement):
    __predefined_basic_qnt = {"11001", "11002", "11003", "11004", "11006", "11008", "11009", "11012", "11013",
                              "11014", "11015", "11016", "11017", "11999"}
    __predefined_basic_art_id = __predefined_basic_qnt

    def __init__(self, ct_line: _Element, all_basics: Union[List[Basics], None] = None,
                 all_articles: Union[ArticleCollection, None] = None):
        self.element = ct_line
        basic_type = get_child_element(self.element, 'lineType')
        super().__init__(self.element, basic_type)
        self.all_basics = all_basics
        self.all_articles = all_articles
        self.nr = to_float(get_child_text(self.element, 'nr'))
        self.line_id = get_child_text(self.element, 'lineID')
        self.line_type = get_text_from_element(basic_type)
        self.art_group_id = get_child_text(self.element, 'artGroupID')
        self.art_id_element = get_child_element(self.element, 'artID')
        self.art_id = get_child_text(self.element, 'artID')
        self.qnt = get_child_text(self.element, 'qnt')
        self.line_amnt_incl = get_child_text(self.element, 'lineAmntIn')
        self.line_amnt_excl = get_child_text(self.element, 'lineAmntEx')
        self.amount_type = get_child_text(self.element, 'amntTp')
        self.ct_line_date = get_child_text(self.element, 'lineDate')
        self.ct_line_time = get_child_text(self.element, 'lineTime')
        if self.amount_type == 'D':
            sign = -1
        else:
            sign = 1
        self.line_amnt_incl_fl = abs(to_float(self.line_amnt_incl)) * sign
        self.line_amnt_excl_fl = abs(to_float(self.line_amnt_excl)) * sign
        self.price_per_unit = get_child_text(self.element, 'ppu')
        self.desc = get_child_text(self.element, 'cashTransLineDescr')

    @property
    def article(self):
        if self.all_articles and self.art_id:
            return self.all_articles[self.art_id]
        return True

    def __repr__(self):
        return (f"CTLine(nr={self.nr!r}, trans_id={self.line_id!r}, line_type={self.line_type!r}, "
                f"art_group_id={self.art_group_id!r}, art_id={self.art_id!r}, qnt={self.qnt!r}, "
                f"line_amnt_in={self.line_amnt_incl!r}, line_amnt_ex={self.line_amnt_excl!r}, "
                f"amount_type={self.amount_type!r}")


class CashTransRaise(BaseElement):
    correct_predefined_basic_totals = ['10']

    def __init__(self, raise_: _Element, all_basics: Union[List[Basics], None] = None):
        self.element = raise_
        basic_type = get_child_element(self.element, 'raiseType')
        super().__init__(self.element, basic_type, all_basics)

    def __repr__(self):
        return f"CashTransRaise(basic_type:{self.basic_type!r}"


class CashTrans(BaseElement):
    correct_predefined_basic_totals = ['11']
    __predefined_basic_ctline = {"11001", "11002", "11003", "11004", "11006", "11008", "11009", "11012", "11013",
                                 "11014", "11015", "11016", "11017", "11999"}
    __predefined_basic_payment = {"11001", "11002", "11003", "11004", "11005", "11006", "11008", "11009", "11012",
                                  "11015", "11016", "11017", "11999"}
    __predefined_basic_for_event_report_sum = {'11001', '11002', '11004', '11005', '11006', '11009', '11012', '11013',
                                               '11015', '11016', '11017'}

    __last_nr_fl: Optional[str] = None  # Class variable to hold the last transaction number
    __last_nr: Optional[str] = None  # Class variable to hold the last transaction number

    def __init__(self, validator_: 'XMLValidator', cash_trans: _Element, all_basics: Union[List[Basics], None] = None,
                 all_articles: Union[ArticleCollection, None] = None):
        self.validator = validator_
        self.element = cash_trans
        basic_type = get_child_element(self.element, 'transType')
        super().__init__(self.element, basic_type, all_basics)
        self.all_basics = all_basics
        self.all_articles = all_articles
        self.nr = get_child_text(self.element, 'nr')
        self.nr_fl = self.convert_nr(self.nr)
        self.trans_id = get_child_text(self.element, 'transID')
        self.trans_type = get_text_from_element(basic_type)
        self.trans_amnt_incl = get_child_text(self.element, 'transAmntIn')
        self.trans_amnt_excl = get_child_text(self.element, 'transAmntEx')
        self.amount_type = get_child_text(self.element, 'amntTp')
        if self.amount_type == 'D':
            sign = -1
        else:
            sign = 1
        self.trans_amnt_incl_fl = abs(to_float(self.trans_amnt_incl)) * sign
        self.trans_amnt_excl_fl = abs(to_float(self.trans_amnt_excl)) * sign
        self.employee_id = get_child_text(self.element, 'empID')
        self.trans_date = get_child_text(self.element, 'transDate')
        self.trans_time = get_child_text(self.element, 'transTime')
        self.cash_tran_datetime = date_time_handler.convert_to_datetime(self.trans_date, self.trans_time)
        self.cash_tran_datetime_min = date_time_handler.truncate_seconds(self.cash_tran_datetime)
        void_trans = get_child_text(self.element, 'voidTransaction')
        self.void_trans = True if void_trans is not None and (void_trans == 'true' or void_trans == '1') else False
        training_id = get_child_text(self.element, 'trainingID')
        self.training_id = True if training_id is not None and (training_id == 'true' or training_id == '1') else False
        self.chain_break = 0
        self.ref_id = get_child_text(self.element, 'refID')
        self.desc = get_child_text(self.element, 'desc')

        self.raise_type = get_child_text(self.element, 'raise', 'raiseType')
        self.__raise_amnt = to_float(get_child_text(self.element, 'raise', 'raiseAmnt'))

        # Assign the previous transaction number to an instance variable, if needed
        self.nr_previous_fl = CashTrans.__last_nr_fl
        self.nr_previous = CashTrans.__last_nr
        self.nr_previous_check = (True if CashTrans.__last_nr_fl is None else self.nr_fl == self.nr_previous_fl + 1)
        # Update the class variable with the current transaction number
        CashTrans.__last_nr_fl = self.nr_fl
        CashTrans.__last_nr = self.nr

        self.signature_element = get_child_element(self.element, 'signature')
        self.signature = get_child_text(self.element, 'signature')
        self.certificate_data = get_child_text(self.element, 'certificateData')

        self.raises = [CashTransRaise(x, self.all_basics) for x in get_all_children(self.element, 'raise')]

        self.ct_lines = [CTLine(x, self.all_basics, self.all_articles) for x in
                         get_all_children(self.element, 'ctLine')]
        self.payments = [Payment(x, self.all_basics) for x in get_all_children(self.element, 'payment')]

    def convert_nr(self, value: str) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            if ',' in value:
                self.validator.log_validation_error(self.validator.check.structure_check,
                                                    get_child_element(self.element, 'nr'),
                                                    StructureErrors.should_contain_number,
                                                    [self.nr])
                return float(0)
            digits = re.findall(r'\d+', value)
            if digits:
                return float(''.join(digits))
            else:
                self.validator.log_validation_error(self.validator.check.structure_check,
                                                    get_child_element(self.element, 'nr'),
                                                    StructureErrors.should_contain_number,
                                                    [self.nr])
                return float(0)

    @property
    def mandatory_if_available_ct_line(self) -> Tuple[str, bool]:
        if self.void_trans is True:
            return 'ctLine', True
        return 'ctLine', self.mandatory_if_available('ct_lines', self.__predefined_basic_ctline)

    @property
    def mandatory_if_available_ct_line_qnt(self) -> Tuple[str, bool]:
        if self.void_trans is True:
            return 'qnt', True
        if self.ct_lines:
            if self.predefined_basic in self.__predefined_basic_ctline:
                if [x for x in self.ct_lines if x.qnt is not None] != self.ct_lines:
                    return 'qnt', False
        return 'qnt', True

    @property
    def mandatory_if_available_ct_line_art_id(self) -> Tuple[str, bool]:
        if self.void_trans is True:
            return 'artID', True
        if self.ct_lines:
            if self.predefined_basic in self.__predefined_basic_ctline:
                if [x for x in self.ct_lines if x.art_id is not None] != self.ct_lines:
                    return 'artID', False
        return 'artID', True

    @property
    def mandatory_if_available_payment(self) -> Tuple[str, bool]:
        if self.void_trans is True:
            return 'payment', True
        return 'payment', self.mandatory_if_available('payments', self.__predefined_basic_payment)

    @property
    def tips(self):
        if self.all_basics and get_predefined_basic_id(get_basic(self.all_basics, self.raise_type)) == "10001":
            return self.__raise_amnt
        return 0

    @classmethod
    def reset_class_variables(cls):
        """Resets the class variable __last_nr to None."""
        cls.__last_nr_fl = None
        cls.__last_nr = None

    @property
    def to_be_excluded(self) -> bool:
        exclude_ = False
        if self.void_trans is True:
            exclude_ = True
        elif self.training_id is True:
            exclude_ = True
        elif self.predefined_basic not in self.__predefined_basic_for_event_report_sum:
            exclude_ = True
        return exclude_

    def __repr__(self):
        return (f"CashTrans(nr={self.nr_fl!r}, trans_id={self.trans_id!r}, trans_type={self.trans_type!r}, "
                f"trans_amnt_incl={self.trans_amnt_incl_fl!r}, trans_amnt_excl={self.trans_amnt_excl_fl!r}, "
                f"tips={self.tips!r}. "
                f"amount_type={self.amount_type!r}, employee_id={self.employee_id!r}, "
                f"report_datetime={self.cash_tran_datetime!r}, void_trans={self.void_trans!r}, "
                f"training_id={self.training_id!r})")


class ValueTestErrors(Enum):
    event_report_total_cash_sales = "EVENT_REPORT_TOTAL_CASH_SALES"
    event_report_grand_total_sales = "EVENT_REPORT_GRAND_TOTAL_SALES"
    event_report_tips = "EVENT_REPORT_TIPS"
    event_report_could_not_run = "EVENT_REPORT_COULD_NOT_RUN"
    not_continous_numbering = 'NOT_CONTINOUS_NUMBERING'
    continous_numbering_pr_cash_reg = 'CONTINOUS_NUMBERING_PR_CASH_REGISTER'

    no_relation_to_basics_found = 'NO_RELATION_TO_BASICS_FOUND'
    no_relation_to_articles_found = 'NO_RELATION_TO_ARTICLES_FOUND'
    mandatory_if_available = 'ELEMENT_NOT_FOUND_WHEN_EXPECTED'
    wrong_predefined_basic_used = 'WRONG_PREDEFINED_BASIC_USED'


class EventReport:
    __last_datetime: Optional[datetime.datetime] = date_time_handler.convert_to_datetime("2000-01-01", "00:00:00")
    __last_grand_total_cash_sale: Optional[float] = None

    def __init__(self, event_report: _Element):
        self.element = event_report
        self.report_id = get_child_text(event_report, 'reportID')
        self.report_type = get_child_text(event_report, 'reportType')
        self.report_date = get_child_text(event_report, 'reportDate')
        self.report_time = get_child_text(event_report, 'reportTime')
        self.report_datetime = date_time_handler.convert_to_datetime(self.report_date, self.report_time)
        self.register_id = get_child_text(event_report, 'registerID')
        self.total_cash_sale = to_float(
            get_child_text(event_report, 'reportTotalCashSales', 'totalCashSaleAmnt'))
        self.grand_total_cash_sale = to_float(get_child_text(event_report, 'reportGrandTotalSales'))
        self.report_tip = to_float(get_child_text(event_report, 'reportTip', 'tipAmnt'))
        self.total_return_num = to_float(get_child_text(event_report, 'reportReturnNum'))
        self.total_return = to_float(get_child_text(event_report, 'reportReturnAmnt'))
        self.discount_num = to_float(get_child_text(event_report, 'reportDiscountNum'))
        self.discount = to_float(get_child_text(event_report, 'reportDiscountAmnt'))

        # Assign the previous report's datetime and grand total cash sale to the new instance
        self.report_datetime_start = EventReport.__last_datetime
        self.grand_total_cash_sale_previous = EventReport.__last_grand_total_cash_sale
        self.grand_total_diff_from_previous = (self.grand_total_cash_sale - self.total_cash_sale)
        self.grand_total_check = (True if EventReport.__last_grand_total_cash_sale is None else abs(
            self.grand_total_diff_from_previous - self.grand_total_cash_sale_previous) <= tolerance)
        # skip every report before first z report.
        if EventReport.__last_datetime == date_time_handler.convert_to_datetime("2000-01-01", "00:00:00"):
            self.skip = True
        else:
            self.skip = None

        if self.report_type == "Z report":
            # Update the class variables to the current report's values
            EventReport.__last_datetime = self.report_datetime
            EventReport.__last_grand_total_cash_sale = self.grand_total_cash_sale

    @classmethod
    def reset_class_variables(cls):
        """Resets the class variables to their default values."""
        cls.__last_datetime = date_time_handler.convert_to_datetime("2000-01-01", "00:00:00")
        cls.__last_grand_total_cash_sale = None

    @staticmethod
    def sort_reports_by_datetime(reports: List['EventReport']) -> List['EventReport']:
        """Sorts a list of ZReport objects by the report_datetime attribute.

        Args:
            reports (List['ZReport']): List of ZReport objects.

        Returns:
            List['ZReport']: List of ZReport objects sorted by report_datetime.
        """
        return sorted(reports, key=lambda report: report.cash_tran_datetime)

    def __repr__(self):
        return (f"EventReport(report_type={self.report_type}, "
                f"report_id={self.report_id}, "
                f"report_datetime={self.report_datetime}, "
                f"total_cash_sale={self.total_cash_sale}, "
                f"grand_total_cash_sale={self.grand_total_cash_sale}, "
                f"report_tip={self.report_tip})")


class StreetAddress:
    def __init__(self, street_address: _Element | None):
        if street_address is None:
            self.street_name = None
            self.number = None
            self.building = None
            self.additional_address_details = None
            self.city = None
            self.postal_code = None
            self.region = None
            self.country = None
        else:
            self.street_name = get_child_text(street_address, 'streetname')
            self.number = get_child_text(street_address, 'number')
            self.building = get_child_text(street_address, 'building')
            self.additional_address_details = get_child_text(street_address, 'additionalAddressDetails')
            self.city = get_child_text(street_address, 'city')
            self.postal_code = get_child_text(street_address, 'postalCode')
            self.region = get_child_text(street_address, 'region')
            self.country = get_child_text(street_address, 'country')

    def __repr__(self) -> str:
        return (
            f"StreetAddress("
            f"full_address={self.full_address!r}, "
            f"street_name={self.street_name!r}, number={self.number!r}, "
            f"building={self.building!r}, additional_address_details={self.additional_address_details!r}, "
            f"city={self.city!r}, postal_code={self.postal_code!r}, "
            f"region={self.region!r}, country={self.country!r}"
        )

    @property
    def full_address(self) -> str:
        """
        Property to format the address in a single line (Danish style).

        Returns:
            str: A single-line formatted address without the region and country.
        """
        if not self.street_name or not self.city or not self.postal_code:
            return "Incomplete address information."

        # Check if the street_name already contains the number
        if self.number and self.number in self.street_name:
            formatted_street = self.street_name
        else:
            formatted_street = f"{self.street_name} {self.number}"

        # Append building (house letter) if present, without a space between number and building
        if self.building:
            formatted_street += f"{self.building}"

        # Create a formatted address string
        address_parts = [formatted_street]

        if self.additional_address_details:
            address_parts.append(self.additional_address_details)

        # Append the city and postal code
        address_parts.append(f"{self.postal_code} {self.city}")

        # Join all parts with a comma for a single line format
        return ", ".join(address_parts)


class Metadata:
    def __init__(self, header: _Element, company: _Element):
        self.__header = header
        self.__company = company
        self.__generate_header_info()
        self.__generate_company_info()

    def __generate_header_info(self):
        self.fiscal_year = get_child_text(self.__header, 'fiscalYear')
        self.start_date = date_time_handler.convert_to_date(get_child_text(self.__header, 'startDate'))
        self.end_Date = date_time_handler.convert_to_date(get_child_text(self.__header, 'endDate'))
        self.cur_code = get_child_text(self.__header, 'curCode')
        self.date_created = date_time_handler.convert_to_date(get_child_text(self.__header, 'dateCreated'))
        self.time_created = date_time_handler.convert_to_time(get_child_text(self.__header, 'timeCreated'),
                                                              self.date_created)
        self.software_desc = get_child_text(self.__header, 'softwareDesc')
        self.software_version = get_child_text(self.__header, 'softwareVersion')
        self.software_company_name = get_child_text(self.__header, 'softwareCompanyName')
        self.audit_file_cvr = get_child_text(self.__header, 'auditfileSender', 'companyIdent')
        self.audit_file_name = get_child_text(self.__header, 'auditfileSender', 'companyName')
        self.audit_file_street_address = StreetAddress(
            get_child_element(self.__header, 'auditfileSender', 'streetAddress'))

    def __generate_company_info(self):
        self.cvr = get_child_text(self.__company, 'companyIdent')
        self.name = get_child_text(self.__company, 'companyName')
        self.__street_address = StreetAddress(get_child_element(self.__company, 'streetAddress'))
