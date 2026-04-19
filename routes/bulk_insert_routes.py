from flask import Blueprint, request, jsonify
from parser_wrapper import parse_excel_in_memory
import logging

excel_bp = Blueprint("excel", __name__)
logger = logging.getLogger(__name__)


# ==========================================================
# UPLOAD & PARSE EXCEL (POST)
# ==========================================================
@excel_bp.route("/upload_excel", methods=["POST"])
def upload_excel():
    try:
        logger.info("Excel upload endpoint called")

        # Validate file existence
        if "file" not in request.files:
            logger.warning("No file part in request")
            return jsonify({
                "status": "error",
                "message": "No file part in request"
            }), 400

        file = request.files["file"]

        # Validate filename
        if file.filename == "":
            logger.warning("No file selected")
            return jsonify({
                "status": "error",
                "message": "No file selected"
            }), 400

        logger.info(f"Processing file: {file.filename}")

        # Parse Excel in memory
        result = parse_excel_in_memory(file)

        parsed_sheets = result.get("parsed_sheets", [])
        failed_sheets = result.get("failed_sheets", {})

        # If no sheets parsed successfully
        if not parsed_sheets:
            logger.warning("No sheets could be parsed successfully")

            return jsonify({
                "status": "error",
                "message": "No sheets could be parsed successfully.",
                "parsed_sheets": [],
                "failed_sheets": failed_sheets,
                "parsed_sheets_count": 0,
                "failed_sheets_count": len(failed_sheets),
                "total_sheets_count": len(failed_sheets)
            }), 400

        # Success response
        logger.info(f"Successfully parsed {len(parsed_sheets)} sheet(s)")

        return jsonify({
            "status": "success",
            "message": f"Parsed {len(parsed_sheets)} sheet(s) successfully.",
            "parsed_sheets": parsed_sheets,
            "parsed_sheets_count": len(parsed_sheets),
            "failed_sheets": failed_sheets,
            "failed_sheets_count": len(failed_sheets),
            "total_sheets_count": len(parsed_sheets) + len(failed_sheets)
        }), 200

    except Exception as e:
        logger.exception("Unexpected error during Excel parsing")

        return jsonify({
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }), 500