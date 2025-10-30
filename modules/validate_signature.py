import base64
from typing import TYPE_CHECKING

from modules.conventions.variables import Validation, Signature
from modules.conventions.error_types import SignatureErrors
from modules.conventions.dummy_variables import string_dummy
from modules.conventions.variables_value_test import CashTrans
from modules.conventions.verify_signature import SignatureVerificationStrategy

if TYPE_CHECKING:
    from main import XMLValidator


class XMLSignatureValidator:

    def __init__(self, validator_: 'XMLValidator'):
        self.validator = validator_

    @staticmethod
    def encode(value: bytes) -> str:
        """
        Encodes a value to base64.

        This method takes a value and encodes it to base64.

        :param value: The value to be encoded (as bytes).
        :return: The base64 encoded value as a string.
        """
        return base64.b64encode(value).decode('utf-8')

    @staticmethod
    def decode(value) -> bytes:
        """
        Decodes a base64 encoded value.

        This method takes a base64 encoded value and decodes it.

        :param value: The base64 encoded value to decode.
        :return: The decoded value as bytes.
        """
        return base64.b64decode(value)

    def validate(self):
        """
        Validates signatures in the XML data.

        This method iterates through the XML data and validates the signatures of cash transactions.
        It checks the signature against the public key of the associated certificate and verifies the message.

        :return: None
        """
        signature = None
        for cash_reg, cash_trans in self.validator.cash_transactions.items():
            prev_signature = "0"
            nr_of_errors = 0
            nr_of_signatures = 0
            for cash_tran in cash_trans:
                signature = cash_tran.signature_element
                if signature is None or signature.text == string_dummy or signature.text is None:
                    continue
                signature_text = "".join(signature.text.split("\n")).strip()
                try:
                    if prev_signature != "0":
                        signature_encoded = self.decode(signature_text)
                        nr_of_signatures += 1
                        try:
                            certificate = self.validator.certificate(cash_tran.certificate_data)
                            public_key = certificate.public_key()
                        except Exception as e:
                            self.validator.log_validation_error(self.validator.check.signature_check,
                                                                cash_tran.signature_element,
                                                                SignatureErrors.certificate_error)
                            self.validator.signature_error = True
                            nr_of_errors += 1
                            continue

                        if self.is_invalid_company_id():
                            raise Exception("Could not get company ID")

                        signature_message = self.create_signature_message(prev_signature, cash_tran, cash_reg)
                        # print(f"{cash_tran.nr}: {signature_message.full_message}")

                        verification_strategy = SignatureVerificationStrategy(public_key)
                        if not verification_strategy.verify(message=signature_message,
                                                            signature=signature_encoded,
                                                            print_it_worked=False):
                            signature_message.prev_signature = "0"
                            if verification_strategy.verify(message=signature_message,
                                                            signature=signature_encoded):
                                self.validator.log_validation_error(self.validator.check.signature_check, signature,
                                                                    SignatureErrors.signature_break)
                            else:
                                self.validator.log_validation_error(self.validator.check.signature_check, signature,
                                                                    SignatureErrors.could_not_verify)
                            self.validator.signature_error = True
                            nr_of_errors += 1

                    else:  # First signature
                        first_signature = signature
                    prev_signature = signature_text

                except Exception as e:
                    self.validator.log_validation_error(self.validator.check.signature_check,
                                                        cash_tran.signature_element,
                                                        SignatureErrors.complete_error)
                    self.validator.signature_error = True
                    nr_of_errors += 1

            if nr_of_signatures == nr_of_errors and nr_of_errors != 0:
                self.check_first_signature_error(first_signature)

        if signature is None:
            self.log_no_signature_error()

    def is_invalid_company_id(self):
        return self.validator.master_data.company_id in {self.validator.error_messages['MASTERDATA'], string_dummy}

    def create_signature_message(self, prev_signature, cash_tran: CashTrans, cash_reg) -> Signature:
        return Signature(
            prev_signature=prev_signature,
            nr=cash_tran.nr,
            trans_id=cash_tran.trans_id,
            trans_type=cash_tran.trans_type,
            trans_date=cash_tran.trans_date,
            trans_time=cash_tran.trans_time,
            emp_id=cash_tran.employee_id,
            trans_amnt_in=cash_tran.trans_amnt_incl,
            trans_amnt_ex=cash_tran.trans_amnt_excl,
            register_id=cash_reg,
            company_ident=self.validator.master_data.company_id
        )

    def check_first_signature_error(self, first_signature):
        self.validator.log_validation_error(self.validator.check.signature_check, first_signature,
                                            SignatureErrors.could_not_verify)
        self.validator.signature_error = True

    def log_no_signature_error(self):
        self.validator.signature_error = True
        self.validator.validation.append(Validation(
            check=self.validator.check.signature_check,
            check_obj=self.validator.check,
            status=self.validator.status.error,
            technical_error_type=SignatureErrors.no_signature.value,
            error_xml_element=SignatureErrors.xml_element.value
        ))
