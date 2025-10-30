from datetime import datetime
from typing import TYPE_CHECKING, List, Union, Any, Tuple

from modules.conventions.variables_value_test import CashTrans, EventReport, ValueTestErrors, tolerance

if TYPE_CHECKING:
    from main import XMLValidator


class XMLValueTestValidator:

    def __init__(self, validator_: 'XMLValidator'):
        self.validator = validator_

    @staticmethod
    def filter_transactions_on_date(transactions: List[CashTrans], start_date: datetime, end_date: datetime) -> Union[
        List[CashTrans], None]:
        """Filters transactions within a specified date range.

        Args:
            transactions (List[CashTrans]): List of CashTrans instances.
            start_date (datetime.datetime): The start date of the range.
            end_date (datetime.datetime): The end date of the range.

        Returns:
            List[CashTrans]: Filtered list of transactions.
        """
        try:
            return [trans for trans in transactions if start_date < trans.cash_tran_datetime <= end_date]
        except:
            return None

    def __event_report_vs_cash_trans(self, event_reports: dict[str, list[EventReport]]):
        for cash_reg, event_reports_ in event_reports.items():
            for event_report in event_reports_:
                if event_report.skip is None:  # skips every event report before first z-report
                    cash_transactions = self.filter_transactions_on_date(
                        transactions=self.validator.cash_transactions[cash_reg],
                        start_date=event_report.report_datetime_start,
                        end_date=event_report.report_datetime)
                    if cash_transactions is not None:
                        tips_amnt = sum([x.tips for x in cash_transactions if x.to_be_excluded is False])
                        cash_trans_amnt = sum(
                            [x.trans_amnt_incl_fl for x in cash_transactions if x.to_be_excluded is False]) + abs(
                            event_report.total_return)
                        if not abs(cash_trans_amnt - event_report.total_cash_sale) <= tolerance:
                            self.validator.log_validation_error(self.validator.check.value_check,
                                                                event_report.element,
                                                                ValueTestErrors.event_report_total_cash_sales,
                                                                [event_report.total_cash_sale, cash_trans_amnt])
                            self.validator.value_error = True
                        if not abs(tips_amnt - event_report.report_tip) <= tolerance:
                            self.validator.log_validation_error(self.validator.check.value_check,
                                                                event_report.element,
                                                                ValueTestErrors.event_report_tips,
                                                                [event_report.report_tip, tips_amnt])
                            self.validator.value_error = True
                        if not event_report.grand_total_check:
                            self.validator.log_validation_error(self.validator.check.value_check,
                                                                event_report.element,
                                                                ValueTestErrors.event_report_grand_total_sales,
                                                                [event_report.grand_total_cash_sale,
                                                                 event_report.grand_total_cash_sale_previous,
                                                                 event_report.total_cash_sale])
                            self.validator.value_error = True
                    else:
                        """Could not filter on cash transactions"""
                        self.validator.log_validation_error(self.validator.check.value_check, event_report.element,
                                                            ValueTestErrors.event_report_could_not_run)
                        self.validator.value_error = True

    def __check_continous_numbering_in_cash_tran_pr_cash_register(self) -> bool:
        if len(self.validator.cash_transactions.keys()) > 1:
            continous_numbering_pr_cash_reg = True
            for cash_reg, cash_trans in self.validator.cash_transactions.items():
                for cash_tran in cash_trans:
                    if not cash_tran.nr_previous_check:
                        continous_numbering_pr_cash_reg = False
                        # self.validator.structure_error = True
                        # self.validator.log_validation_error(self.validator.check.structure_check,
                        #                                     cash_tran.element, LogicalTestErrors.not_continous_numbering,
                        #                                     [cash_tran.nr, cash_tran.nr_previous])

            return continous_numbering_pr_cash_reg

    @staticmethod
    def __get_unique_transactions_nr(cash_trans: List[CashTrans]) -> List[CashTrans]:
        seen_nrs = set()
        unique_transactions = []
        for trans in cash_trans:
            if trans.nr_fl not in seen_nrs:
                unique_transactions.append(trans)
                seen_nrs.add(trans.nr_fl)
        return unique_transactions

    def __check_continous_numbering_in_cash_tran(self):
        numbering = 0
        previous_numbering = ""
        all_cash_trans = [cash_tran for sublist in self.validator.cash_transactions.values() for cash_tran in sublist]
        all_cash_trans = self.__get_unique_transactions_nr(all_cash_trans)
        all_cash_trans.sort(key=lambda obj: obj.nr_fl)
        if self.__check_continous_numbering_in_cash_tran_pr_cash_register():
            self.validator.value_error = True
            self.validator.log_validation_error_no_element(self.validator.check.value_check,
                                                           ValueTestErrors.continous_numbering_pr_cash_reg)
            return

        if all_cash_trans:
            for idx, cash_tran in enumerate(all_cash_trans):
                if idx == 0:
                    numbering = cash_tran.nr_fl
                else:
                    if not abs(cash_tran.nr_fl - (numbering + 1)) <= tolerance:
                        cash_tran.chain_break = 1
                        self.validator.value_error = True
                        self.validator.log_validation_error(self.validator.check.value_check,
                                                            cash_tran.element,
                                                            ValueTestErrors.not_continous_numbering,
                                                            [cash_tran.nr, previous_numbering])
                    numbering = cash_tran.nr_fl
                previous_numbering = cash_tran.nr

    def __get_all_missed_relations_to_basics(self) -> List[Any]:
        """Get all objects with missed relations to basics."""

        def get_missed_relations(objects):
            """Helper function to filter objects without relation to basic check."""
            return [obj for obj in objects if not obj.relation_to_basic_check]

        all_missed_relations = []
        # All events
        all_missed_relations.extend(
            get_missed_relations(obj for list_ in self.validator.events.values() for obj in list_))
        # All cash transactions
        all_missed_relations.extend(
            get_missed_relations(obj for list_ in self.validator.cash_transactions.values() for obj in list_))
        # All raises in cash transactions
        all_missed_relations.extend(get_missed_relations(
            raise_ for list_ in self.validator.cash_transactions.values() for cash_tran in list_ for raise_ in
            cash_tran.raises))
        # All ctlines
        all_missed_relations.extend(get_missed_relations(
            ctline for list_ in self.validator.cash_transactions.values() for cash_tran in list_ for ctline in
            cash_tran.ct_lines))
        # All payments
        all_missed_relations.extend(get_missed_relations(
            payment for list_ in self.validator.cash_transactions.values() for cash_tran in list_ for payment in
            cash_tran.payments))
        return all_missed_relations

    def __check_relation_to_basics(self) -> None:
        """Check all relations to basics and append validation errors."""
        all_missed_relations = self.__get_all_missed_relations_to_basics()
        for missed_relation in all_missed_relations:
            self.validator.log_validation_error(check_=self.validator.check.value_check,
                                                element=missed_relation.basic_type_element,
                                                error_type=ValueTestErrors.no_relation_to_basics_found,
                                                special_error_msg=[missed_relation.basic_type])
            self.validator.value_error = True

    def __get_all_missed_relations_to_articles(self) -> List[Any]:
        """Get all objects with missed relations to basics."""

        def get_missed_relations(objects):
            """Helper function to filter objects without relation to basic check."""
            return [obj for obj in objects if not obj.article]

        all_missed_relations = []
        # All ctlines
        all_missed_relations.extend(get_missed_relations(
            ctline for list_ in self.validator.cash_transactions.values() for cash_tran in list_ for ctline in
            cash_tran.ct_lines))
        return all_missed_relations

    def __check_relation_to_articles(self) -> None:
        """Check all relations to basics and append validation errors."""
        all_missed_relations = self.__get_all_missed_relations_to_articles()
        for missed_relation in all_missed_relations:
            self.validator.log_validation_error(check_=self.validator.check.value_check,
                                                element=missed_relation.element,
                                                error_type=ValueTestErrors.no_relation_to_articles_found,
                                                special_error_msg=[missed_relation.art_id])
            self.validator.value_error = True

    def __get_all_missed_mandatory_if_available(self) -> List[Tuple[Any, Any]]:
        """Get all objects with missed mandatory if available checks."""

        def get_missed_mandatory(objects, attr):
            """Helper function to filter objects with missed mandatory checks."""
            return [(obj, getattr(obj, attr)) for obj in objects if not getattr(obj, attr)[1]]

        all_missed_mandatory_if_available = []
        # Events - eventreport
        all_missed_mandatory_if_available.extend(
            get_missed_mandatory((obj for list_ in self.validator.events.values() for obj in list_),
                                 'mandatory_if_available_event_report'))
        # Events - trans_id
        all_missed_mandatory_if_available.extend(
            get_missed_mandatory((obj for list_ in self.validator.events.values() for obj in list_),
                                 'mandatory_if_available_trans_id'))
        # Payment - payment_ref_id
        all_missed_mandatory_if_available.extend(get_missed_mandatory(
            (payment for list_ in self.validator.cash_transactions.values() for cash_tran in list_ for payment in
             cash_tran.payments), 'mandatory_if_available_payment_ref_id'))
        # Cash transaction - CT line - qnt
        all_missed_mandatory_if_available.extend(
            get_missed_mandatory((obj for list_ in self.validator.cash_transactions.values() for obj in list_),
                                 'mandatory_if_available_ct_line_qnt'))
        # Cash transaction - CT line - art_id
        all_missed_mandatory_if_available.extend(
            get_missed_mandatory((obj for list_ in self.validator.cash_transactions.values() for obj in list_),
                                 'mandatory_if_available_ct_line_art_id'))
        # Cash transaction - Payment
        all_missed_mandatory_if_available.extend(
            get_missed_mandatory((obj for list_ in self.validator.cash_transactions.values() for obj in list_),
                                 'mandatory_if_available_payment'))
        # Cash transaction - CTLINE
        all_missed_mandatory_if_available.extend(
            get_missed_mandatory((obj for list_ in self.validator.cash_transactions.values() for obj in list_),
                                 'mandatory_if_available_ct_line'))
        # Basics - predefined basic
        all_missed_mandatory_if_available.extend(
            get_missed_mandatory(self.validator.all_basics, 'mandatory_if_available_predefined_basic_id'))
        return all_missed_mandatory_if_available

    def __mandatory_if_available(self):
        """Check all mandatory if available fields and append validation errors."""
        all_missed_mandatory_if_available = self.__get_all_missed_mandatory_if_available()
        for missed_relation_obj, missed_relation_mandatory in all_missed_mandatory_if_available:
            self.validator.log_validation_error(check_=self.validator.check.value_check,
                                                element=missed_relation_obj.basic_type_element,
                                                error_type=ValueTestErrors.mandatory_if_available,
                                                special_error_msg=[missed_relation_obj.predefined_basic,
                                                                   missed_relation_mandatory[0]])
            self.validator.value_error = True

    def __get_all_wrongly_used_predefined_basics(self) -> List[Any]:
        """Get all objects with wrongly used predefined basics."""

        def get_wrongly_used(objects):
            """Helper function to filter objects with wrongly used predefined basics."""
            return [obj for obj in objects if not obj.correct_predefined_basic_check]

        all_wrongly_used_predefined_basics = []
        # All events
        all_wrongly_used_predefined_basics.extend(
            get_wrongly_used(obj for list_ in self.validator.events.values() for obj in list_))
        # All cash transactions
        all_wrongly_used_predefined_basics.extend(
            get_wrongly_used(obj for list_ in self.validator.cash_transactions.values() for obj in list_))
        # All raises in cash transactions
        all_wrongly_used_predefined_basics.extend(get_wrongly_used(
            raise_ for list_ in self.validator.cash_transactions.values() for cash_tran in list_ for raise_ in
            cash_tran.raises))
        # All payments
        all_wrongly_used_predefined_basics.extend(get_wrongly_used(
            payment for list_ in self.validator.cash_transactions.values() for cash_tran in list_ for payment in
            cash_tran.payments))
        return all_wrongly_used_predefined_basics

    def __correct_predefined_basic_used(self) -> None:
        """Check all predefined basic usages and append validation errors."""
        all_wrongly_used_predefined_basics = self.__get_all_wrongly_used_predefined_basics()
        for wrong_predefined_basic in all_wrongly_used_predefined_basics:
            self.validator.log_validation_error(
                check_=self.validator.check.value_check,
                element=wrong_predefined_basic.basic_type_element,
                error_type=ValueTestErrors.wrong_predefined_basic_used,
                special_error_msg=[wrong_predefined_basic.predefined_basic,
                                   wrong_predefined_basic.correct_predefined_basic_totals])
            self.validator.value_error = True

    def validate(self):
        """Runs all value tests"""
        #  Event report value tests
        self.__event_report_vs_cash_trans(self.validator.z_reports)
        self.__event_report_vs_cash_trans(self.validator.x_reports)
        #  Check if running nr in cashTran
        self.__check_continous_numbering_in_cash_tran()
        #  All relations to basic check
        self.__check_relation_to_basics()
        #  All relations to articles check
        self.__check_relation_to_articles()
        # All mandatory if available check
        self.__mandatory_if_available()
        # all correct predefined basic check
        self.__correct_predefined_basic_used()
