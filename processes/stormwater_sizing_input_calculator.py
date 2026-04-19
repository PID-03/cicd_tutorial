from extensions import db
from models.stormwater_output import StormwaterAreaParameters
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


# =========================================================
# EQUIVALENT AREA CALCULATION
# =========================================================
def calculate_equivalent_area(
    roof_area,
    roof_coeff,
    carpark_area,
    carpark_coeff,
    landscaping_area,
    landscaping_coeff,
):
    """
    Calculates equivalent impervious area:
    Aeq = (Roof × C1) + (Carpark × C2) + (Landscaping × C3)
    """

    try:
        roof_area = float(roof_area or 0)
        roof_coeff = float(roof_coeff or 0)
        carpark_area = float(carpark_area or 0)
        carpark_coeff = float(carpark_coeff or 0)
        landscaping_area = float(landscaping_area or 0)
        landscaping_coeff = float(landscaping_coeff or 0)

        equivalent_area = (
            (roof_area * roof_coeff)
            + (carpark_area * carpark_coeff)
            + (landscaping_area * landscaping_coeff)
        )

        result = round(equivalent_area, 2)

        logger.info(f"Equivalent area calculated | value={result}")

        return result

    except Exception:
        logger.exception("Error during equivalent area calculation")
        raise


# =========================================================
# MAIN INPUT PROCESSING FUNCTION
# =========================================================
def input_calculations(project_id, data):
    """
    Calculates and stores:
    - Equivalent Area
    - Converted Soil Permeability
    - Converted Detention Tank Discharge Allowance
    """

    logger.info(f"Stormwater area parameter process started | project_id={project_id}")

    try:
        # -------------------------------------------------
        # EXTRACT INPUTS
        # -------------------------------------------------
        roof_area = data.get("roof_area")
        roof_coeff = data.get("roof_coefficient")

        carpark_area = data.get("carpark_area")
        carpark_coeff = data.get("carpark_coefficient")

        landscaping_area = data.get("landscaping_area")
        landscaping_coeff = data.get("landscaping_coefficient")

        soil_per_input = data.get("soil_permeability")
        detention_input = data.get("detention_tank_discharge_allowance")

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------
        required_fields = [
            roof_area,
            roof_coeff,
            carpark_area,
            carpark_coeff,
            landscaping_area,
            landscaping_coeff,
            soil_per_input,
            detention_input,
        ]

        if any(value is None for value in required_fields):
            logger.warning(
                f"Validation failed - missing required fields | project_id={project_id}"
            )
            return False, "Missing required fields"

        # -------------------------------------------------
        # TYPE CONVERSION
        # -------------------------------------------------
        roof_area = float(roof_area)
        roof_coeff = float(roof_coeff)
        carpark_area = float(carpark_area)
        carpark_coeff = float(carpark_coeff)
        landscaping_area = float(landscaping_area)
        landscaping_coeff = float(landscaping_coeff)

        soil_per_input = float(soil_per_input)
        detention_input = float(detention_input)

        # -------------------------------------------------
        # CALCULATIONS
        # -------------------------------------------------

        # 1️⃣ Equivalent Area
        equivalent_area = calculate_equivalent_area(
            roof_area,
            roof_coeff,
            carpark_area,
            carpark_coeff,
            landscaping_area,
            landscaping_coeff,
        )

        # 2️⃣ Soil Permeability Conversion
        # Formula: soil_per = soil_per / 24 / 60 * 1000
        soil_per_calculated = (soil_per_input / 24 / 60) * 1000
        soil_per_calculated = round(soil_per_calculated, 4)

        # 3️⃣ Detention Discharge Conversion
        # Formula: detention = detention * 3600 / 1000
        detention_calculated = (detention_input * 3600) / 1000
        detention_calculated = round(detention_calculated, 4)

        logger.info(
            f"Calculated values | "
            f"Equivalent Area={equivalent_area}, "
            f"Soil Converted={soil_per_calculated}, "
            f"Detention Converted={detention_calculated}"
        )

        # -------------------------------------------------
        # DATABASE INSERT OR UPDATE
        # -------------------------------------------------
        record = StormwaterAreaParameters.query.filter_by(
            project_id=project_id
        ).first()

        if record:
            logger.info(f"Existing record found - updating | project_id={project_id}")

            record.equivalent_area = equivalent_area
            record.soil_permiability_mm_day = soil_per_calculated
            record.detention_tank_allowance_m3_per_hour = detention_calculated

            message = "Area parameters updated"

        else:
            logger.info(f"No record found - creating | project_id={project_id}")

            record = StormwaterAreaParameters(
                project_id=project_id,
                equivalent_area=equivalent_area,
                soil_permiability_mm_day=soil_per_calculated,
                detention_tank_allowance_m3_per_hour=detention_calculated,
            )

            db.session.add(record)
            message = "Area parameters created"

        db.session.commit()

        logger.info(f"Database commit successful | project_id={project_id}")

        return True, {
            "project_id": str(project_id),
            "equivalent_area": equivalent_area,
            "soil_permiability_mm_day": soil_per_calculated,
            "detention_tank_allowance_m3_per_hour": detention_calculated,
            "message": message,
        }

    except SQLAlchemyError:
        db.session.rollback()
        logger.exception(
            f"Database error during stormwater area parameter process | project_id={project_id}"
        )
        return False, "Database Error"

    except Exception:
        logger.exception(
            f"Unexpected error during stormwater area parameter process | project_id={project_id}"
        )
        return False, "Internal Server Error"