from extensions import db
from models.static_data import PrecastSoakwellSpec, CircularAreaReference
from models.stormwater import StormwaterSizingCalculation
from models.stormwater_output import StormwaterVolumeCalculation
from run import app


# ==========================================================
# 1️⃣ Catchment Storage Calculation
# ==========================================================
def calculate_catchment_storage(
    roof_area, roof_depth_mm,
    carpark_area, carpark_depth_mm,
    landscaping_area, landscaping_depth_mm
):
    roof_volume = roof_area * roof_depth_mm / 1000
    carpark_volume = carpark_area * carpark_depth_mm / 1000
    landscaping_volume = landscaping_area * landscaping_depth_mm / 1000

    total_volume = roof_volume + carpark_volume + landscaping_volume

    return round(total_volume, 2)


# ==========================================================
# 2️⃣ Precast Soakwell Volume (DB Lookup)
# ==========================================================
def calculate_precast_soakwells(soakwells):

    total_volume = 0

    for item in soakwells:
        size = item["size"]
        quantity = item["quantity"]

        soakwell = PrecastSoakwellSpec.query.filter_by(
            model_label=size
        ).first()

        if not soakwell:
            raise ValueError(f"Soakwell size {size} not found in database.")

        total_volume += soakwell.volume_m3 * quantity

    return round(total_volume, 2)


# ==========================================================
# 3️⃣ Stormwater Pipe Volume (DB Lookup)
# ==========================================================
def calculate_stormwater_pipes(pipes):

    total_volume = 0

    for pipe in pipes:
        diameter = pipe["diameter_mm"]
        length = pipe["length_m"]

        if diameter > 0:
            pipe_data = CircularAreaReference.query.filter_by(
                diameter_mm=diameter
            ).first()

            if not pipe_data:
                raise ValueError(f"Pipe size {diameter}mm not found in database.")

            cross_section_area = pipe_data.area_m2
            volume = cross_section_area * length
        else:
            volume = 0

        total_volume += volume

    return round(total_volume, 2)


# ==========================================================
# 4️⃣ Master Calculation + Save To DB
# ==========================================================
def calculate_total_additional_storage_with_db_area(
    project_id,
    roof_depth_mm,
    carpark_depth_mm,
    landscaping_depth_mm,
    soakwells,
    pipes,
    additional_volume_m3=0
):

    # --------------------------------------------
    # Fetch sizing input from DB
    # --------------------------------------------
    sizing = StormwaterSizingCalculation.query.filter_by(
        project_id=project_id
    ).first()

    if not sizing:
        raise ValueError("Stormwater sizing record not found for this project.")

    # --------------------------------------------
    # Catchment Volume
    # --------------------------------------------
    catchment_volume = calculate_catchment_storage(
        roof_area=sizing.roof_area,
        roof_depth_mm=roof_depth_mm,
        carpark_area=sizing.carpark_area,
        carpark_depth_mm=carpark_depth_mm,
        landscaping_area=sizing.landscaping_area,
        landscaping_depth_mm=landscaping_depth_mm
    )

    # --------------------------------------------
    # Soakwell Volume
    # --------------------------------------------
    soakwell_volume = calculate_precast_soakwells(soakwells)

    # --------------------------------------------
    # Pipe Volume
    # --------------------------------------------
    pipe_volume = calculate_stormwater_pipes(pipes)

    # --------------------------------------------
    # Final Total
    # --------------------------------------------
    total_volume = round(
        catchment_volume
        + soakwell_volume
        + pipe_volume
        + additional_volume_m3,
        2
    )

    # ==========================================================
    # 💾 SAVE / UPDATE stormwater_volume_calculation
    # ==========================================================
    volume_record = StormwaterVolumeCalculation.query.filter_by(
        project_id=project_id
    ).first()

    if volume_record:
        volume_record.total_additional_storage = total_volume
    else:
        volume_record = StormwaterVolumeCalculation(
            project_id=project_id,
            total_additional_storage=total_volume
        )
        db.session.add(volume_record)

    db.session.commit()

    # --------------------------------------------
    # Return Result
    # --------------------------------------------
    return {
        "Catchment Storage (m³)": catchment_volume,
        "Soakwell Volume (m³)": soakwell_volume,
        "Pipe Volume (m³)": pipe_volume,
        "Additional Volume (m³)": additional_volume_m3,
        "Total Storage Provided (m³)": total_volume
    }


# ==========================================================
# 5️⃣ Run Example
# ==========================================================
if __name__ == "__main__":
    with app.app_context():

        project_id = "21155589-b3f8-4796-81f7-2a80132086eb"

        result = calculate_total_additional_storage_with_db_area(
            project_id=project_id,

            # Depths (manual)
            roof_depth_mm=87,
            carpark_depth_mm=67,
            landscaping_depth_mm=48,

            # Soakwells (manual)
            soakwells=[
                {"size": "Ø1800x1500", "quantity": 1},
                {"size": "Ø1800x1500", "quantity": 4}
            ],

            # Pipes (manual)
            pipes=[
                {"diameter_mm": 1500, "length_m": 1},
                {"diameter_mm": 1200, "length_m": 2},
                {"diameter_mm": 300, "length_m": 1}
            ],

            # Additional volume (manual)
            additional_volume_m3=1
        )

        print(result)