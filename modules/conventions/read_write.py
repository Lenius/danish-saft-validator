import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import pandas as pd


class Write:
    @staticmethod
    def __sanitize_data(data: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Sanitizes the data by removing any newline characters from the string values
        and formatting decimal numbers with a comma as the decimal separator.

        :param data: A list of dictionaries, where each dictionary represents a row in the CSV file.
        :return: The sanitized data with newline characters removed and decimal points replaced by commas.
        """
        sanitized_data = []
        for row in data:
            sanitized_row = {}
            for key, value in row.items():
                if isinstance(value, str):
                    # Remove newline characters and strip whitespace
                    sanitized_value = value.replace('\n', '').strip()
                elif isinstance(value, float):
                    # Format float with a comma as the decimal separator
                    sanitized_value = f"{value:.2f}".replace('.', ',')
                else:
                    sanitized_value = value
                sanitized_row[key] = sanitized_value
            sanitized_data.append(sanitized_row)
        return sanitized_data

    @staticmethod
    def csv(file_path: str, data: List[Dict[str, str]]):
        """
        Write the provided data to a CSV file using csv.DictWriter.

        :param file_path: The path to the CSV file to be written.
        :param data: A list of dictionaries, where each dictionary represents a row in the CSV file.
        """
        if not data:
            raise ValueError("No data provided to write.")

        sanitized_data = Write.__sanitize_data(data)  # Sanitize the data before writing to CSV

        fieldnames = sanitized_data[
            0].keys()  # Dynamically determine the fieldnames from the keys of the first dictionary.

        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter="|")
            writer.writeheader()
            writer.writerows(sanitized_data)

    @staticmethod
    def json(file_path: str, data: List[Dict[str, str]]):
        """
        Write the provided data to a JSON file, converting datetime objects to strings.

        :param file_path: The path to the JSON file to be written.
        :param data: A list of dictionaries to be written as JSON. Handles datetime serialization.
        """
        if not data:
            raise ValueError("No data provided to write.")

        # Custom JSON encoder to handle datetime objects
        def default_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()  # Convert datetime to ISO format string
            raise TypeError(f"Type {type(obj)} not serializable")

        # Write the data to the file using the custom serializer
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4, default=default_serializer)

    @staticmethod
    def __fix_column_widths(writer: pd.ExcelWriter, df: pd.DataFrame, sheet_name: str):
        """
        Helper function to adjust column widths in the Excel sheet.

        :param df: The DataFrame containing the validation results.
        :param sheet_name: The name of the Excel sheet.
        """
        worksheet = writer.sheets[sheet_name]
        for i, col in enumerate(df.columns):
            width = max(df[col].apply(lambda x: len(str(x))).max(), len(col))
            worksheet.set_column(i, i, width)

    @staticmethod
    def __excel(writer: pd.ExcelWriter, data: List[Dict[str, str]], sheet_name: str, fix_column_width: bool = True):
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        if fix_column_width:
            Write.__fix_column_widths(writer, df, sheet_name)

    @staticmethod
    def excel(file_path: str, data: List[Dict[str, str]], sheet_name: str, fix_column_width: bool = True):
        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
            Write.__excel(writer=writer,
                          data=data,
                          sheet_name=sheet_name,
                          fix_column_width=fix_column_width)

    @staticmethod
    def excel_multiple_sheets(file_path: str | Path, data: Dict[str, List[Dict[str, str]]],
                              fix_column_width: bool = True):
        """
        :param file_path: path to the excel file
        :param data: The key in the dict is sheet_name
        :return:
        """
        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
            for sheet_name, data_ in data.items():
                Write.__excel(writer=writer,
                              data=data_,
                              sheet_name=sheet_name,
                              fix_column_width=fix_column_width)


class Read:

    @staticmethod
    def excel_dict(path: Path, sheet_name_: str, key: str, val: str, engine_: str = 'openpyxl') -> Dict[str, str]:
        return {col[key]: col[val] for row, col in
                pd.read_excel(path, sheet_name=sheet_name_, engine=engine_).iterrows()}
