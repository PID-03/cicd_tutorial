import pandas as pd
import logging
import re

logger = logging.getLogger(__name__)

# =====================================================
# Utility
# =====================================================

def safe_float(value):
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


# =====================================================
# Duration Parsing (STRICT)
# =====================================================

def parse_duration(value: str):
    """
    Strict duration parser.
    Accepts:
        - min / mins / minute / minutes
        - hr / hrs / hour / hours
    Returns duration in minutes.
    """

    if not isinstance(value, str):
        return None

    value = value.lower().strip()

    number_match = re.search(r"(\d+)", value)
    if not number_match:
        return None

    number = int(number_match.group(1))

    if re.search(r"\b(min|mins|minute|minutes)\b", value):
        return number

    if re.search(r"\b(hr|hrs|hour|hours)\b", value):
        return number * 60

    return None


# =====================================================
# Header Detection
# =====================================================

def detect_header_row(df: pd.DataFrame) -> int:
    for idx, row in df.iterrows():
        percent_count = 0

        for cell in row.tolist():

            if isinstance(cell, str) and re.search(r"\d+\s*%", cell):
                percent_count += 1

            elif isinstance(cell, (int, float)) and 0 < float(cell) < 1:
                percent_count += 1

        if percent_count >= 3:
            logger.info(f"Header detected at row {idx}")
            return idx

    raise ValueError("Table header not found.")


def detect_duration_column(df_table: pd.DataFrame) -> int:

    best_col = None
    best_count = 0

    for col_index in range(len(df_table.columns)):

        series = (
            df_table.iloc[:, col_index]
            .astype(str)
            .str.replace("\xa0", " ", regex=False)
            .str.strip()
        )

        duration_count = series.apply(parse_duration).notna().sum()

        if duration_count > best_count:
            best_count = duration_count
            best_col = col_index

    if best_col is None or best_count < 3:
        raise ValueError("Duration column not detected from data.")

    logger.info(f"Duration column detected at index {best_col}")
    return best_col


def detect_premium_columns(header_row: pd.Series) -> dict:

    mapping = {}

    for idx, val in enumerate(header_row.tolist()):

        if isinstance(val, (int, float)) and 0 < float(val) < 1:
            percent_value = round(float(val) * 100)
            mapping[f"{percent_value}%"] = idx
            continue

        if isinstance(val, str):
            match = re.search(r"(\d+)\s*%", val)
            if match:
                mapping[f"{match.group(1)}%"] = idx

    if len(mapping) < 3:
        raise ValueError("Premium columns not properly detected.")

    logger.info(f"Detected premium columns: {list(mapping.keys())}")
    return mapping


# =====================================================
# Table Isolation
# =====================================================

def extract_table_block(df_raw: pd.DataFrame, header_index: int) -> pd.DataFrame:
    df = df_raw.iloc[header_index + 1:].copy()
    df.reset_index(drop=True, inplace=True)
    return df


# =====================================================
# Cleaning & Footer Handling
# =====================================================

def clean_and_validate_rows(df, duration_col, premium_mapping):

    df = df.copy()

    df.iloc[:, duration_col] = (
        df.iloc[:, duration_col]
        .astype(str)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
    )

    df["duration_minutes"] = df.iloc[:, duration_col].apply(parse_duration)

    premium_cols = list(premium_mapping.values())

    df.iloc[:, premium_cols] = df.iloc[:, premium_cols].apply(
        pd.to_numeric, errors="coerce"
    )

    df["valid_premium_count"] = df.iloc[:, premium_cols].notna().sum(axis=1)

    valid_rows = []
    invalid_streak = 0
    MAX_INVALID_STREAK = 5

    for _, row in df.iterrows():

        duration = row["duration_minutes"]
        premium_count = row["valid_premium_count"]

        if pd.notna(duration) and duration > 0 and premium_count >= 3:
            valid_rows.append(row)
            invalid_streak = 0
        else:
            invalid_streak += 1
            if invalid_streak >= MAX_INVALID_STREAK:
                logger.info("Footer detected. Stopping parse.")
                break

    if not valid_rows:
        raise ValueError("No valid rows detected after cleaning.")

    result_df = pd.DataFrame(valid_rows)

    result_df = result_df.drop_duplicates(subset=["duration_minutes"])
    result_df = result_df.sort_values("duration_minutes").reset_index(drop=True)

    return result_df


# =====================================================
# Sheet Parser
# =====================================================

def parse_sheet(df_raw: pd.DataFrame, sheet_name: str) -> dict:

    header_index = detect_header_row(df_raw)
    header_row = df_raw.iloc[header_index]

    df_table = extract_table_block(df_raw, header_index)

    duration_col = detect_duration_column(df_table)
    premium_mapping = detect_premium_columns(header_row)

    df_clean = clean_and_validate_rows(
        df_table,
        duration_col,
        premium_mapping
    )

    data = []

    for _, row in df_clean.iterrows():

        entry = {
            "duration_minutes": int(row["duration_minutes"]),
            "values": {}
        }

        for percent_label, col_index in premium_mapping.items():
            entry["values"][percent_label] = safe_float(row.iloc[col_index])

        data.append(entry)

    logger.info(f"{sheet_name} - Parsed {len(data)} valid rows")

    return {
        "region_name": sheet_name,
        "data": data
    }


# =====================================================
# Excel Wrapper (Merged from parser_wrapper.py)
# =====================================================

def parse_excel_in_memory(file_stream) -> dict:
    """
    Parse all sheets in the Excel file (in-memory)
    """

    parsed_sheets = []
    failed_sheets = {}

    try:
        xls = pd.ExcelFile(file_stream)
    except Exception as e:
        return {
            "parsed_sheets": [],
            "failed_sheets": {"__file__": f"Failed to read Excel file: {str(e)}"}
        }

    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            result = parse_sheet(df, sheet_name)
            parsed_sheets.append(result)
        except Exception as e:
            logger.exception(f"Failed to parse sheet {sheet_name}")
            failed_sheets[sheet_name] = str(e)

    return {
        "parsed_sheets": parsed_sheets,
        "failed_sheets": failed_sheets
    }