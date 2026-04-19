from extensions import db
from models.stormwater_output import AdditionalVolumeOutput
from models.stormwater_input import StormwaterSizingCalculation
from sqlalchemy.exc import SQLAlchemyError
import math
import logging
import re

logger = logging.getLogger(__name__)


def calculate_additional_storage(project_id, data):
    """
    Calculates total additional storage using formulas
    and stores detailed output in AdditionalVolumeOutput table.
    """

    logger.info(f"Additional storage process started | project_id={project_id}")

    try:
        # ---------------------------------------------------
        # Fetch sizing record
        # ---------------------------------------------------
        sizing = StormwaterSizingCalculation.query.filter_by(
            project_id=project_id
        ).first()

        if not sizing:
            logger.warning(f"Sizing record not found | project_id={project_id}")
            return False, "Stormwater sizing record not found"

        # ---------------------------------------------------
        # Extract depths
        # ---------------------------------------------------
        roof_depth_mm = float(data.get("roof_depth_mm", 0))
        carpark_depth_mm = float(data.get("carpark_depth_mm", 0))
        landscaping_depth_mm = float(data.get("landscaping_depth_mm", 0))

        soakwells = data.get("precast_soakwells", [])
        pipes = data.get("stormwater_pipes", [])
        other_additional_volume = float(data.get("other_additional_volume", 0))

        # ---------------------------------------------------
        # Catchment Volume Calculation
        # ---------------------------------------------------
        roof_volume = (float(sizing.roof_area or 0) * roof_depth_mm) / 1000
        carpark_volume = (float(sizing.carpark_area or 0) * carpark_depth_mm) / 1000
        landscaping_volume = (float(sizing.landscaping_area or 0) * landscaping_depth_mm) / 1000

        catchment_volume = roof_volume + carpark_volume + landscaping_volume

        logger.info(f"Catchment volume calculated | {round(catchment_volume,2)} m3")

        # ---------------------------------------------------
        # Soakwell Calculation (Formula Based)
        # Formula:
        # (diameter/2000)^2 * height * 22/7
        # ---------------------------------------------------
        soakwell_volume = 0
        soakwell_output_json = []

        for item in soakwells:
            size = item.get("size")  # Ø1800x1500
            quantity = float(item.get("quantity", 0))

            # Extract diameter & height
            match = re.search(r"(\d+)x(\d+)", size)
            if not match:
                return False, f"Invalid soakwell size format: {size}"

            diameter_mm = float(match.group(1))
            height_mm = float(match.group(2))

            diameter_m = diameter_mm / 1000
            height_m = height_mm / 1000

            # Volume formula
            volume_one = ((diameter_mm / 2000) ** 2) * height_m * (22 / 7)
            total_volume = volume_one * quantity

            soakwell_volume += total_volume

            soakwell_output_json.append({
                "size": size,
                "area": round(total_volume, 2)
            })

        logger.info(f"Soakwell volume calculated | {round(soakwell_volume,2)} m3")

        # ---------------------------------------------------
        # Pipe Calculation (Formula Based)
        # Area = πr²
        # ---------------------------------------------------
        pipe_volume = 0
        pipe_output_json = []

        for pipe in pipes:
            diameter_mm = float(pipe.get("diameter_mm", 0))
            length_m = float(pipe.get("length_m", 0))

            if diameter_mm > 0 and length_m > 0:
                radius_m = (diameter_mm / 1000) / 2
                area = (22 / 7) * (radius_m ** 2)

                volume = area * length_m
                pipe_volume += volume

                pipe_output_json.append({
                    "diameter_mm": diameter_mm,
                    "area": round(volume, 2)
                })

        logger.info(f"Pipe volume calculated | {round(pipe_volume,2)} m3")

        # ---------------------------------------------------
        # Final Total Storage
        # ---------------------------------------------------
        total_volume = round(
            catchment_volume + soakwell_volume + pipe_volume + other_additional_volume,
            2
        )

        logger.info(f"Total additional storage | {total_volume} m3")

        # ---------------------------------------------------
        # Save / Update AdditionalVolumeOutput Table
        # ---------------------------------------------------
        record = AdditionalVolumeOutput.query.filter_by(
            project_id=project_id
        ).first()

        if record:
            record.roof_catchment_area = roof_volume
            record.carpark_catchment_area = carpark_volume
            record.landscaping_catchment_area = landscaping_volume
            record.total_additional_storage = total_volume
            record.precast_soakwell_area = soakwell_output_json
            record.stormwater_pipes = pipe_output_json
            record.other_additional_area = other_additional_volume

            message = "Additional volume output updated"
            logger.info("Updating existing record")

        else:
            record = AdditionalVolumeOutput(
                project_id=project_id,
                roof_catchment_area=roof_volume,
                carpark_catchment_area=carpark_volume,
                landscaping_catchment_area=landscaping_volume,
                total_additional_storage=total_volume,
                precast_soakwell_area=soakwell_output_json,
                stormwater_pipes=pipe_output_json,
                other_additional_area=other_additional_volume
            )
            db.session.add(record)
            message = "Additional volume output created"
            logger.info("Creating new record")

        db.session.commit()

        return True, {
            "project_id": str(project_id),
            "total_additional_storage": total_volume,
            "message": message
        }

    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error")
        return False, "Database Error"

    except Exception:
        logger.exception("Unexpected error")
        return False, "Internal Error"