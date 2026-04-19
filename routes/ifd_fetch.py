# from flask import Blueprint, request, jsonify
# from processes.fetch_ifd_data_from_lat_long import fetch_rainfall_density
# import logging
# from dotenv import load_dotenv
# import os
# import requests

# load_dotenv()

# rainfall_bp = Blueprint("rainfall", __name__)

# logger = logging.getLogger(__name__)


# LOCATIONIQ_API_KEY = os.getenv("LOCATIONIQ_API_KEY")


# # ==========================================================
# # HELPER: GET LOCATION NAME FROM LAT/LON
# # ==========================================================
# def get_location_name(lat, lon):
#     url = "https://us1.locationiq.com/v1/reverse"

#     params = {
#         "key": LOCATIONIQ_API_KEY,
#         "lat": lat,
#         "lon": lon,
#         "format": "json"
#     }

#     logger.info("Getting location information")

#     try:
#         response = requests.get(url, params=params, timeout=10)
#         response.raise_for_status()

#         data = response.json()

#         return {
#             "display_name": data.get("display_name"),
#             "city": data.get("address", {}).get("city"),
#             "state": data.get("address", {}).get("state"),
#             "country": data.get("address", {}).get("country")
#         }

#     except requests.exceptions.RequestException as e:
#         logger.error(f"LocationIQ error: {str(e)}")
#         return None


# # ==========================================================
# # HELPER: CONVERT DURATION TEXT TO MINUTES
# # ==========================================================
# def convert_hour_to_min(duration_text):

#     if "min" in duration_text:
#         return int(duration_text.replace("min", "").strip())

#     if "hour" in duration_text:
#         value = float(duration_text.replace("hour", "").strip())
#         return int(value * 60)

#     if "day" in duration_text:
#         value = float(duration_text.replace("day", "").strip())
#         return int(value * 24 * 60)

#     return None


# # ==========================================================
# # FETCH RAINFALL DATA (POST)
# # ==========================================================
# @rainfall_bp.route("/fetch_idf_data", methods=["POST"])
# def get_rainfall():
#     try:
#         data = request.get_json()
#         logger.info("Rainfall endpoint called")

#         if not data:
#             return jsonify({"error": "Request body must be JSON"}), 400

#         lat = data.get("lat")
#         lon = data.get("lon")

#         if lat is None or lon is None:
#             return jsonify({"error": "latitude and longitude are required"}), 400

#         try:
#             lat = float(lat)
#             lon = float(lon)
#         except ValueError:
#             return jsonify({"error": "latitude and longitude must be numbers"}), 400

#         logger.info(f"Fetching rainfall for lat={lat}, lon={lon}")

#         raw_data = fetch_rainfall_density(lat, lon)

#         if isinstance(raw_data, dict) and "error" in raw_data:
#             return jsonify(raw_data), 500

#         transformed_data = []

#         for item in raw_data:
#             minutes = convert_hour_to_min(item["duration_minutes"])

#             transformed_data.append({
#                 "duration_minutes": minutes,
#                 "values_mm_per_hr": item["values_mm_per_hr"]
#             })

#         location_info = get_location_name(lat, lon)

#         if not location_info:
#             region_name = "Unknown Region"
#         else:
#             region_name = f"{location_info.get('state', '')} - {location_info.get('city', '')}"

#         logger.info("Rainfall data fetched successfully")

#         return jsonify({
#             "region_name": region_name,
#             "latitude": lat,
#             "longitude": lon,
#             "data": transformed_data
#         }), 200

#     except Exception as e:
#         logger.error(f"Rainfall Route Error: {str(e)}")
#         return jsonify({"msg": "Something went wrong"}), 500

from flask import Blueprint, request, jsonify
from processes.fetch_ifd_data_from_lat_long import fetch_rainfall_density
import logging
from dotenv import load_dotenv
import os
import requests
from utils.error_response import error_response  # ✅ ADDED

load_dotenv()

rainfall_bp = Blueprint("rainfall", __name__)

logger = logging.getLogger(__name__)

LOCATIONIQ_API_KEY = os.getenv("LOCATIONIQ_API_KEY")


# ==========================================================
# HELPER: GET LOCATION NAME FROM LAT/LON
# ==========================================================
def get_location_name(lat, lon):
    url = "https://us1.locationiq.com/v1/reverse"

    params = {
        "key": LOCATIONIQ_API_KEY,
        "lat": lat,
        "lon": lon,
        "format": "json"
    }

    logger.info("Getting location information")

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        return {
            "display_name": data.get("display_name"),
            "city": data.get("address", {}).get("city"),
            "state": data.get("address", {}).get("state"),
            "country": data.get("address", {}).get("country")
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"LocationIQ error: {str(e)}")
        return None


# ==========================================================
# HELPER: CONVERT DURATION TEXT TO MINUTES
# ==========================================================
def convert_hour_to_min(duration_text):
    if "min" in duration_text:
        return int(duration_text.replace("min", "").strip())

    if "hour" in duration_text:
        value = float(duration_text.replace("hour", "").strip())
        return int(value * 60)

    if "day" in duration_text:
        value = float(duration_text.replace("day", "").strip())
        return int(value * 24 * 60)

    return None


# ==========================================================
# FETCH RAINFALL DATA (POST)
# ==========================================================
@rainfall_bp.route("/fetch_idf_data", methods=["POST"])
def get_rainfall():
    try:
        data = request.get_json()
        logger.info("Rainfall endpoint called")

        if not data:
            return error_response(400, "ValidationError", "Request body must be JSON")  # ✅

        lat = data.get("lat")
        lon = data.get("lon")

        if lat is None or lon is None:
            return error_response(400, "ValidationError", "latitude and longitude are required")  # ✅

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return error_response(400, "ValidationError", "latitude and longitude must be numbers")  # ✅

        logger.info(f"Fetching rainfall for lat={lat}, lon={lon}")

        raw_data = fetch_rainfall_density(lat, lon)

        if isinstance(raw_data, dict) and "error" in raw_data:
            return error_response(500, "RainfallFetchError", raw_data["error"])  # ✅

        transformed_data = []

        for item in raw_data:
            minutes = convert_hour_to_min(item["duration_minutes"])
            transformed_data.append({
                "duration_minutes": minutes,
                "values_mm_per_hr": item["values_mm_per_hr"]
            })

        location_info = get_location_name(lat, lon)

        if not location_info:
            region_name = "Unknown Region"
        else:
            region_name = f"{location_info.get('state', '')} - {location_info.get('city', '')}"

        logger.info("Rainfall data fetched successfully")

        return jsonify({
            "region_name": region_name,
            "latitude": lat,
            "longitude": lon,
            "data": transformed_data
        }), 200

    except Exception as e:
        logger.error(f"Rainfall Route Error: {str(e)}")
        return error_response(500, "InternalServerError", "Something went wrong")  # ✅