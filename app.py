import logging
from flask import Flask, request, jsonify
from parser_wrapper import parse_excel_in_memory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/upload_excel", methods=["POST"])
def upload_excel():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "No file selected"}), 400

    try:
        result = parse_excel_in_memory(file)
        parsed_sheets = result.get("parsed_sheets", [])
        failed_sheets = result.get("failed_sheets", {})

        if not parsed_sheets:
            # ERROR because no sheets could be parsed
            return jsonify({
                "status": "error",
                "message": "No sheets could be parsed successfully.",
                "parsed_sheets": [],
                "failed_sheets": failed_sheets
            }), 400

        # SUCCESS if at least one sheet parsed
        return jsonify({
            "status": "success",
            "message": f"Parsed {len(parsed_sheets)} sheet(s) successfully.",
            "parsed_sheets": parsed_sheets,
            "parsed_sheets_count": len(parsed_sheets),
            "failed_sheets": failed_sheets,
            "failed_sheets_count": len(failed_sheets),
            "total_sheets_count": len(parsed_sheets) + len(failed_sheets)
        })

    except Exception as e:
        logger.exception("Unexpected error during parsing")
        return jsonify({"status": "error", "message": f"Unexpected error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5005)