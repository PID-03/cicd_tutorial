from flask import jsonify

def error_response(status_code, name, message):
    response = {
        "error": {
            "statusCode": status_code,
            "name": name,
            "message": message
        }
    }
    return jsonify(response), status_code