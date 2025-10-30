from typing import List, Tuple, Callable

import cryptography.exceptions
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from modules.conventions.variables import Signature


def verify_with_pkcs1_v1_5(public_key, message, signature):
    try:
        public_key.verify(
            signature,
            message,
            padding.PKCS1v15(),
            hashes.SHA512()
        )
        return True
    except cryptography.exceptions.InvalidSignature:
        return False


def verify_with_pss_max_length(public_key, message, signature):
    try:
        public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA512()),
                salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA512())
        return True
    except cryptography.exceptions.InvalidSignature:
        return False


def verify_with_pss_digest_length(public_key, message, signature):
    try:
        public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA512()),
                salt_length=padding.PSS.DIGEST_LENGTH),
            hashes.SHA512())
        return True
    except cryptography.exceptions.InvalidSignature:
        return False


def encode_full_message(signature: Signature) -> bytes:
    return signature.full_message_encoded


def encode_full_message_sha512(signature: Signature) -> bytes:
    return signature.full_message_sha512


def encode_full_message_hh_mm_ss(signature: Signature) -> bytes:
    return signature.full_message_encoded_hh_mm_ss


def encode_full_message_sha512_hh_mm_ss(signature: Signature) -> bytes:
    return signature.full_message_sha512_hh_mm_ss


class SignatureVerificationStrategy:
    # Class-level priority list (shared by all instances)
    verification_priority: List[Tuple[Callable, Callable]] = [
        (verify_with_pkcs1_v1_5, encode_full_message),
        (verify_with_pkcs1_v1_5, encode_full_message_sha512),
        (verify_with_pss_digest_length, encode_full_message),
        (verify_with_pss_digest_length, encode_full_message_sha512),
        (verify_with_pss_max_length, encode_full_message),
        (verify_with_pss_max_length, encode_full_message_sha512),
        (verify_with_pkcs1_v1_5, encode_full_message_hh_mm_ss),
        (verify_with_pkcs1_v1_5, encode_full_message_sha512_hh_mm_ss),
        (verify_with_pss_digest_length, encode_full_message_hh_mm_ss),
        (verify_with_pss_digest_length, encode_full_message_sha512_hh_mm_ss),
        (verify_with_pss_max_length, encode_full_message_hh_mm_ss),
        (verify_with_pss_max_length, encode_full_message_sha512_hh_mm_ss)
    ]

    def __init__(self, public_key):
        self.public_key = public_key

    def verify(self, message: Signature, signature: bytes, print_it_worked: bool = False) -> bool:
        """
        Tries each combination of verification method and message encoding in priority order.
        If a method succeeds, it is moved to the front of the list for next time.
        """
        for idx, (verify_method, encode_method) in enumerate(SignatureVerificationStrategy.verification_priority):
            # Apply the encoding method to get the encoded message
            message_to_verify = encode_method(message)
            # print(f"Testing Verification using {verify_method.__name__} with {encode_method.__name__}")

            if verify_method(self.public_key, message_to_verify, signature):
                if print_it_worked:
                    print(f"Verification successful using {verify_method.__name__} with {encode_method.__name__}")
                # Move the successful method/encoding pair to the front of the list
                if idx != 0:
                    self._update_priority(idx)
                return True

    @staticmethod
    def _update_priority(successful_idx: int) -> None:
        """
        Moves the successful verification method and message encoding combination to the front of the list.
        """
        successful_method = SignatureVerificationStrategy.verification_priority.pop(successful_idx)
        SignatureVerificationStrategy.verification_priority.insert(0, successful_method)


if __name__ == '__main__':
    pass
