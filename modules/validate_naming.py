from typing import TYPE_CHECKING

from modules.conventions.error_types import NamingErrors

if TYPE_CHECKING:
    from main import XMLValidator


class XMLNamingValidator:

    def __init__(self, validator_: 'XMLValidator'):
        self.validator = validator_

    @staticmethod
    def __filename_name_check(name: str) -> bool:
        """
        Static method to check if the provided name is "SAF-T Cash Register".

        :param name: The name to be checked.
        :return: True if the name is "SAF-T Cash Register", False otherwise.
        """
        if name == "SAF-T Cash Register":
            return True
        return False

    @staticmethod
    def __filename_id_check(id_: str) -> bool:
        """
        Static method to check if the provided ID is a valid 8-digit integer.

        :param id_: The ID to be checked.
        :return: True if the ID is a valid 8-digit integer, False otherwise.
        """
        if len(id_) != 8:
            return False
        if all([digit_.isdigit() for digit_ in id_]):
            id_ = int(id_)
            if 0 <= id_ <= 99999999:
                return True
        return False

    @staticmethod
    def __filename_date_check(date: str) -> bool:
        """
        Static method to check if the provided date is in the format 'YYYYMMDDhhmmss' and represents a valid date.

        :param date: The date string to be checked.
        :return: True if the date is valid, False otherwise.
        """
        if all([digit_.isdigit() for digit_ in date]):
            if len(date) != 14:
                return False
            year = date[0:4]
            month = date[4:6]
            day = date[6:8]
            hour = date[8:10]
            minute = date[10:12]
            second = date[12:14]
            return all([1970 <= int(year) < 2050,
                        0 < int(month) <= 12,
                        0 < int(day) <= 31,
                        0 <= int(hour) < 24,
                        0 <= int(minute) <= 60,
                        0 <= int(second) <= 60])
        return False

    @staticmethod
    def __filename_file_number_check(file_number: str) -> bool:
        """
        Static method to check if the provided file number is a valid two-digit integer.

        :param file_number: The file number to be checked.
        :return: True if the file number is a valid two-digit integer, False otherwise.
        """
        if len(file_number) == 2:
            try:
                return all([0 < int(file_version) < 10 for file_version in file_number])
            except ValueError:
                pass
        return False

    def validate(self):
        """
        Private method to validate the naming convention of the XML file.

        If the file name follows the expected format, a validation status of 'ok' is appended.
        Otherwise, a validation status of 'error' with the technical error type 'FILENAME' is appended.
        """
        file_name = self.validator.xml_file[0].stem.split("_")
        if len(file_name) == 5:
            self.validator.naming_error = not all([self.__filename_name_check(file_name[0]),
                                                   self.__filename_id_check(file_name[1]),
                                                   self.__filename_date_check(file_name[2]),
                                                   self.__filename_file_number_check(file_name[3:5])])
        elif len(file_name) == 7:
            self.validator.naming_error = not all([self.__filename_name_check(" ".join(file_name[0:3])),
                                                   self.__filename_id_check(file_name[3]),
                                                   self.__filename_date_check(file_name[4]),
                                                   self.__filename_file_number_check(file_name[5:7])])
        else:
            self.validator.naming_error = True
        if self.validator.naming_error:
            self.validator.log_validation_error_no_element(self.validator.check.naming_check,
                                                           NamingErrors.filename)
