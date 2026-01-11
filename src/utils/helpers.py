import logging
import re
from datetime import date, datetime, timedelta
from html import unescape
from typing import Optional, Tuple, Union

import pandas as pd

log = logging.getLogger(__name__)


def clean_response_text(raw_text: str) -> str:
    # Convert HTML entities (e.g. &#160;)
    text = unescape(raw_text)

    # Remove soft hyphen (SHY)
    text = text.replace("\u00ad", "")

    # Convert NBSP (non-breaking space) to normal space
    text = text.replace("\xa0", " ")

    # Remove other problematic invisible characters
    text = text.replace("\u200b", "")  # zero width space
    text = text.replace("\uFEFF", "")  # invisible BOM

    return text


def keep_numeric_and_allowed_chars(text: str, characters: list):
    if pd.isna(text):
        return text

    return "".join(ch for ch in text if ch.isdigit() or ch in characters)


def convert_values(
    value: Optional[str], allow_negative: bool = False
) -> Optional[float]:
    try:
        if value is None:
            return None

        value = value.strip()

        # remove spaces, commas and dots only to validate if it's numeric
        numeric_pattern = r"[ ,.]"
        cleaned = re.sub(numeric_pattern, "", value)

        if allow_negative:
            # for validation, allow a '-' only at the beginning
            if cleaned.startswith("-"):
                cleaned_to_check = cleaned[1:]
            else:
                cleaned_to_check = cleaned
        else:
            # if negatives are not allowed, any '-' makes it invalid
            if "-" in cleaned:
                return None
            cleaned_to_check = cleaned

        if not cleaned_to_check.isnumeric():
            return None

        # Patterns to detect decimal places
        dot_decimal_pattern = r"\.\d{2,}$"
        comma_decimal_pattern = r",\d{2,}$"

        if re.search(dot_decimal_pattern, value):
            # Example: "1,234.56" → "1234.56"
            return float(value.replace(",", "").replace(" ", ""))

        if re.search(comma_decimal_pattern, value):
            # Example: "1.234,56" → "1234.56"
            return float(value.replace(".", "").replace(" ", "").replace(",", "."))

        # No comma as decimal separator — try direct conversion (remove spaces only)
        return float(value.replace(" ", ""))

    except Exception:
        log.exception(f"'{value}' is not a valid number.")
        raise


def process_numeric_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    for column in columns:
        df[column] = df[column].astype(str)
        df[column] = df[column].apply(
            lambda x: keep_numeric_and_allowed_chars(x, [",", "."])
        )
        df[column] = df[column].apply(convert_values)

    return df


def replace_empty_with_none(df):
    null_values = ["", "-", "n/a"]

    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: (
                None
                if isinstance(x, str) and x.strip().lower() in null_values
                else x.strip() if isinstance(x, str) else x
            )
        )

    return df


def get_current_timestamp(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return datetime.now().strftime(fmt)
