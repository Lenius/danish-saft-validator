from cryptography import x509
from cryptography.hazmat.backends import default_backend
from typing import Set
from pathlib import Path

from cryptography.x509 import Certificate

from modules.conventions.file_system import FileSystem


class TrustedCertificates:
    """
    A class to read and store X.509 certificates from .cer files in a specified directory.
    """

    def __init__(self, directory: str):
        """
        Initializes the CertificateReader with a directory to search for .cer files.

        Args:
            directory (str): The path to the directory containing .cer files.
        """
        self.__directory = directory
        self.certificates: Set[x509.Certificate] = set()
        self.__load_certificates()

    def __load_certificates(self) -> None:
        """
        Reads all .cer files in the directory and loads them as X.509 certificates,
        storing each certificate in a set to ensure uniqueness.
        """
        cer_files = Path(self.__directory).glob("*.cer")

        for cer_file in cer_files:
            with open(cer_file, "rb") as file:
                cert_data = file.read()
                certificate = None
                try:
                    # Try loading as PEM format
                    certificate = x509.load_pem_x509_certificate(cert_data, default_backend())
                except ValueError:
                    # If PEM parsing fails, try DER format
                    try:
                        certificate = x509.load_der_x509_certificate(cert_data, default_backend())
                    except ValueError:
                        print(f"Error loading certificate from file: {cer_file}")

                # Add the certificate to the set if successfully loaded
                if certificate:
                    self.certificates.add(certificate)

    def get_set_trusted_certificates(self) -> Set[x509.Certificate]:
        """
        Returns the set of loaded X.509 certificates.

        Returns:
            Set[x509.Certificate]: A set of X.509 certificates.
        """
        return self.certificates

    def validate_certificate(self, cert: Certificate) -> bool:
        if cert in self.certificates:
            return True
        return False


trusted_certificates = TrustedCertificates(directory=FileSystem.trusted_certificates_dir)

if __name__ == '__main__':
    pass

    # trusted_certificates.()
