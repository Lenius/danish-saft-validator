from typing import TYPE_CHECKING, List, Dict, Union

import ssl
from urllib import request

from cryptography import x509
from cryptography.hazmat._oid import ExtensionOID, AuthorityInformationAccessOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.x509 import Certificate, ocsp

from cryptography.x509.ocsp import OCSPResponseStatus, OCSPCertStatus, OCSPResponse
from loguru import logger
from lxml.etree import _Element

from modules.certificate_modules.trusted_certificates import trusted_certificates
from modules.conventions.date_handler import date_time_handler
from modules.conventions.variables import Validation
from modules.conventions.error_types import CertificateErrors
from modules.conventions.dummy_variables import string_dummy, date_dummy

if TYPE_CHECKING:
    from main import XMLValidator


class XMLCertificateValidator:

    def __init__(self, validator_: 'XMLValidator'):
        self.validator = validator_
        self.trusted_certificates = trusted_certificates

    @staticmethod
    def __get_ocsp_request_data(cert: Certificate, issuer_cert: Certificate) -> bytes:
        """
        Builds and retrieves the OCSP request data for the provided certificate and its issuer certificate.

        :param cert: The certificate for which to generate the OCSP request.
        :param issuer_cert: The issuer certificate of the provided certificate.
        :return: The OCSP request data in DER format.
        """
        builder = ocsp.OCSPRequestBuilder()
        builder = builder.add_certificate(cert, issuer_cert, SHA1())
        ocsp_data = builder.build()
        return ocsp_data.public_bytes(serialization.Encoding.DER)

    def __get_ocsp_response(self, ocsp_server: str, cert: Certificate, issuer_cert: Certificate) -> bytes:
        """
        Sends an OCSP request to the specified OCSP server and retrieves the OCSP response.

        :param ocsp_server: The URL of the OCSP server to which the request is sent.
        :param cert: The certificate for which to request the OCSP status.
        :param issuer_cert: The issuer certificate of the provided certificate.
        :return: The OCSP response data in bytes.
        """
        ocsp_req_data = self.__get_ocsp_request_data(cert, issuer_cert)
        ocsp_request = request.Request(ocsp_server, data=ocsp_req_data,
                                       headers={"Content-Type": "application/ocsp-request"})

        with request.urlopen(ocsp_request, timeout=3) as resp:
            return resp.read()

    def __decode_ocsp_response(self, ocsp_server: str, cert: Certificate, issuer_cert: Certificate) -> OCSPResponse:
        """
        Sends an OCSP request for the provided certificate and retrieves the OCSP response.

        :param ocsp_server: The URL of the OCSP server to which the request is sent.
        :param cert: The certificate for which to request the OCSP status.
        :param issuer_cert: The issuer certificate of the provided certificate.
        :return: The OCSP response object.
        :raises Exception: If decoding or verifying the OCSP response fails.
        """
        ocsp_resp = self.__get_ocsp_response(ocsp_server, cert, issuer_cert)
        ocsp_decoded = ocsp.load_der_ocsp_response(ocsp_resp)
        if ocsp_decoded.response_status == OCSPResponseStatus.SUCCESSFUL:
            return ocsp_decoded
        else:
            raise Exception(f'Decoding OCSP response failed: {ocsp_decoded.response_status}')

    @staticmethod
    def __get_ocsp_server(certificate: Certificate) -> str:
        """
        Extracts the OCSP server URL from the Authority Information Access (AIA) extension of a certificate.

        :param certificate: The certificate from which to extract the OCSP server URL.
        :return: The OCSP server URL.
        """
        aia = certificate.extensions.get_extension_for_oid(ExtensionOID.AUTHORITY_INFORMATION_ACCESS).value
        ocsps = [ia for ia in aia if ia.access_method == AuthorityInformationAccessOID.OCSP]
        if not ocsps:
            logger.debug('No OCSP server entry in Certificate')
        return ocsps[0].access_location.value

    @staticmethod
    def __get_issuer(certificate: Certificate):
        """
        Retrieves the CA Issuers URL from the Authority Information Access (AIA) extension of the certificate.

        :param certificate: The certificate from which to extract the CA Issuers URL.
        :return: The CA Issuers URL.
        :raises Exception: If no CA Issuers entry is found in the AIA extension.
        """
        aia = certificate.extensions.get_extension_for_oid(ExtensionOID.AUTHORITY_INFORMATION_ACCESS).value
        issuers = [ia for ia in aia if ia.access_method == AuthorityInformationAccessOID.CA_ISSUERS]
        if not issuers:
            raise Exception('No issuers entry in AIA')
        return issuers[0].access_location.value

    def get_issuer_cert(self, certificate: Certificate) -> Certificate:
        """
        Fetches and loads the issuer certificate.

        :param certificate: The certificate.
        :return: The loaded issuer certificate.
        :raises Exception: If there is an error fetching or processing the issuer certificate.
        """
        ca_issuer = self.__get_issuer(certificate)
        issuer_response = self.validator.session.get(ca_issuer)
        if issuer_response.ok:
            issuer_der = issuer_response.content
            issuer_pem = ssl.DER_cert_to_PEM_cert(issuer_der)
            return x509.load_pem_x509_certificate(issuer_pem.encode('ascii'), default_backend())
        raise Exception(f'Fetching issuer cert failed with response status: {issuer_response.status_code}')

    def __run_ocsp_status_check(self, cert: Certificate, issuer_cert: Union[Certificate, None]) -> OCSPResponse:
        """
        Private method to run an OCSP status check for a given certificate.

        :param cert: The certificate to be checked.
        :return: The OCSP certificate status.
        """
        ocsp_server = self.__get_ocsp_server(cert)
        return self.__decode_ocsp_response(ocsp_server, cert, issuer_cert)

    def __get_all_ocsp(self, all_xml_cert_data: List[_Element], all_cert: List[Certificate],
                       all_issuer_certificates: Dict[Certificate, Union[Certificate, None]]) -> Dict[
        Certificate, OCSPResponse]:
        """
        Private method to retrieve OCSP status for a list of certificates.

        :param all_xml_cert_data: List of XML certificate data.
        :param all_cert: List of certificates.
        :return: A dictionary of OCSP status for each certificate and a flag indicating any certificate errors.
        """
        ocsp_ = {}
        all_ocsp_tested = set()
        for xml_cert, cert in zip(all_xml_cert_data, all_cert):
            try:
                if cert not in all_ocsp_tested and cert != string_dummy:
                    all_ocsp_tested.add(cert)
                    ocsp_[cert] = self.__run_ocsp_status_check(cert, all_issuer_certificates[cert])
            except Exception as e:
                self.validator.certificate_error = True
                self.validator.log_validation_error(self.validator.check.certificate_check, xml_cert,
                                                    CertificateErrors.ocsp_complete_error)
        return ocsp_

    def __get_all_issuer_certificates(self, all_cert) -> Dict[Certificate, Union[Certificate, None]]:
        issuer_certificates = {}
        for cert in all_cert:
            try:
                if cert not in issuer_certificates and cert != string_dummy:
                    issuer_certificates[cert] = self.get_issuer_cert(cert)
            except:
                issuer_certificates[cert] = None
        return issuer_certificates

    def validate(self):
        """
        Validates certificate-related information in the XML file.

        This method performs various checks on the certificates found in the XML data.
        It checks for issues like revocation, expiration, validity period, trusted issuer, and more.
        It also handles potential exceptions that may occur while processing the certificates.

        :return: None
        """
        all_cert, all_xml_cert_data = self.collect_certificates()
        all_issuer_certificates = self.__get_all_issuer_certificates(all_cert)
        all_ocsp = self.__get_all_ocsp(all_xml_cert_data, all_cert, all_issuer_certificates)

        if not all_xml_cert_data or not any(x.text != string_dummy for x in all_xml_cert_data):
            self.log_no_certificate_error()

        for xml_cert, cert in zip(all_xml_cert_data, all_cert):
            if cert == string_dummy or xml_cert.getparent().find(
                    f"{self.validator.xml_root_find}transDate").text == date_dummy:
                continue
            trans_date = date_time_handler.convert_to_date(
                xml_cert.getparent().find(f"{self.validator.xml_root_find}transDate").text)
            if trans_date is None:
                self.validator.log_validation_error(self.validator.check.certificate_check, xml_cert,
                                                    CertificateErrors.could_not_run)
                self.validator.certificate_error = True
            else:
                self.validate_certificate_status(cert, xml_cert, all_ocsp, trans_date, all_issuer_certificates)

    def collect_certificates(self):
        """
        Collects all certificates from the XML data.

        :return: A tuple containing a list of all certificates and a list of all XML certificate data.
        """
        all_cert = []
        all_xml_cert_data = self.validator.xml_file[1].findall(f"{self.validator.xml_root_find}certificateData")
        for xml_cert in all_xml_cert_data:
            try:
                if xml_cert.text != string_dummy:
                    all_cert.append(self.validator.certificate(xml_cert.text))
            except Exception as e:
                all_cert.append(string_dummy)
                self.validator.certificate_error = True
                self.validator.log_validation_error(self.validator.check.certificate_check, xml_cert,
                                                    CertificateErrors.complete_error)
        return all_cert, all_xml_cert_data

    def validate_certificate_status(self, cert: Certificate, xml_cert, all_ocsp, trans_date, all_issuer_certificates):
        """
        Validates the status of a single certificate.

        :param cert: The certificate to be validated.
        :param xml_cert: The corresponding XML certificate data.
        :param all_ocsp: The OCSP status dictionary.
        :param trans_date: The transaction date.
        """
        if cert in all_ocsp:
            self.check_ocsp_status(cert, xml_cert, all_ocsp, trans_date)

        if cert in all_issuer_certificates.keys():
            if not self.trusted_certificates.validate_certificate(all_issuer_certificates[cert]):
                self.validator.log_validation_error(self.validator.check.certificate_check, xml_cert,
                                                    CertificateErrors.not_trusted_issuer)
                self.validator.certificate_error = True
        else:
            self.validator.log_validation_error(self.validator.check.certificate_check, xml_cert,
                                                CertificateErrors.not_trusted_issuer)
            self.validator.certificate_error = True

        if trans_date > cert.not_valid_after_utc.date():
            self.validator.log_validation_error(self.validator.check.certificate_check, xml_cert,
                                                CertificateErrors.expired)
            self.validator.certificate_error = True
        if trans_date < cert.not_valid_before_utc.date():
            self.validator.log_validation_error(self.validator.check.certificate_check, xml_cert,
                                                CertificateErrors.not_valid)
            self.validator.certificate_error = True

    def check_ocsp_status(self, cert, xml_cert, all_ocsp, trans_date):
        """
        Checks the OCSP status of a certificate.

        :param cert: The certificate to be checked.
        :param xml_cert: The corresponding XML certificate data.
        :param all_ocsp: The OCSP status dictionary.
        :param trans_date: The transaction date.
        """
        ocsp_status = all_ocsp[cert]
        if ocsp_status.certificate_status == OCSPCertStatus.REVOKED and ocsp_status.revocation_time is not None and trans_date > ocsp_status.revocation_time.date():
            self.validator.log_validation_error(self.validator.check.certificate_check, xml_cert,
                                                CertificateErrors.ocsp_revoked)
            self.validator.certificate_error = True
        elif ocsp_status.certificate_status == OCSPCertStatus.UNKNOWN:
            if trans_date <= cert.not_valid_after.date():
                self.validator.log_validation_error(self.validator.check.certificate_check, xml_cert,
                                                    CertificateErrors.ocsp_unknown)
                self.validator.certificate_error = True

    def log_no_certificate_error(self):
        """
        Logs an error if no certificates are found.
        """
        self.validator.certificate_error = True
        self.validator.validation.append(Validation(
            check=self.validator.check.certificate_check,
            check_obj=self.validator.check,
            status=self.validator.status.error,
            technical_error_type=CertificateErrors.no_certificate.value,
            error_xml_element=CertificateErrors.xml_element.value
        ))
