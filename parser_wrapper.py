import pandas as pd
import logging
from parser import parse_sheet  # your existing parser file

logger = logging.getLogger(__name__)

def parse_excel_in_memory(file_stream) -> dict:
    """
    Parse all sheets in the Excel file (in-memory) and return structured data.
    Returns:
        {
            "parsed_sheets": [...],
            "failed_sheets": {...}
        }
    """
    parsed_sheets = []
    failed_sheets = {}

    try:
        # Read all sheets
        xls = pd.ExcelFile(file_stream)
    except Exception as e:
        return {
            "parsed_sheets": [],
            "failed_sheets": {"__file__": f"Failed to read Excel file: {str(e)}"}
        }

    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)

            # # DEBUG START
            # logger.info(f"Sheet: {sheet_name}")
            # logger.info(f"Columns: {df.columns}")
            # logger.info(f"Head:\n{df.head(3)}")
            # # DEBUG END

            result = parse_sheet(df, sheet_name)
            parsed_sheets.append(result)
        except Exception as e:
            logger.exception(f"Failed to parse sheet {sheet_name}")
            failed_sheets[sheet_name] = str(e)

    return {
        "parsed_sheets": parsed_sheets,
        "failed_sheets": failed_sheets
    }