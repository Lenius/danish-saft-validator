from enum import Enum

from modules.conventions.file_system import FileSystem
from modules.conventions.read_write import Read
from modules.conventions.text_lang import Language


def error_messages(lang: Language):
    return Read.excel_dict(path=FileSystem.error_types,
                           sheet_name_='Sheet1',
                           key='type_name',
                           val=lang.value)


class XMLReadErrors(Enum):
    read_error = 'XML_FILE_CORRUPT'
    encoding_error = 'XML_FILE_ENCODING_CORRUPT'
    read_error_other_checks = 'CANNOT_DO_CHECK_DUE_TO_READ_ERROR'


class CertificateErrors(Enum):
    not_trusted_issuer = 'CERTIFICATE_NOT_TRUSTED_ISSUER'
    expired = 'CERTIFICATE_EXPIRED'
    not_valid = 'CERTIFICATE_NOT_VALID_YET'
    complete_error = 'CERTIFICATE_COMPLETE_ERROR'
    xml_element = 'certificateData'
    ocsp_revoked = 'CERTIFICATE_REVOKED'
    ocsp_unknown = 'CERTIFICATE_UNKNOWN'
    ocsp_complete_error = 'CERTIFICATE_OCSP_COMPLETE_ERROR'
    could_not_run = 'CERTIFICATE_COULD_NOT_RUN'
    no_certificate = 'NO_CERTIFICATE'


class SignatureErrors(Enum):
    could_not_verify = 'SIGNATURE_NOT_VERIFIED'
    signature_break = 'SIGNATURE_BREAK'
    complete_error = 'SIGNATURE_COMPLETE_ERROR'
    certificate_error = 'CANNOT_GET_PUBLIC_KEY'
    xml_element = 'signature'
    no_signature = 'NO_SIGNATURE'


class NamingErrors(Enum):
    filename = 'FILENAME'


class StructureErrors(Enum):
    out_of_sequence = 'SCHEMAV_OUT_OF_SEQUENCE'
    should_contain_number = 'VALUE_DOES_NOT_CONTAIN_NR'


class ArticleErrors(Enum):
    error_reading_articles = 'ERROR_READING_ARTICLES'


class EmployeeErrors(Enum):
    error_reading_employees = 'ERROR_READING_EMPLOYEES'


class BasicErrors(Enum):
    error_reading_basics = 'ERROR_READING_BASICS'
