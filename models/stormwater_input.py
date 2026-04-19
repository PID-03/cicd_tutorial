# import uuid
# from extensions import db
# from sqlalchemy.dialects.postgresql import UUID, JSONB
# from sqlalchemy.sql import func
# from sqlalchemy import Float, Integer, Boolean, String, ForeignKey, TIMESTAMP
# from sqlalchemy.orm import relationship

# class StormwaterSizingCalculation(db.Model):
#     __tablename__ = "tbl_stormwater_sizing_project_inputs"

#     id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

#     project_id = db.Column(
#         UUID(as_uuid=True),
#         ForeignKey("project_info.id", ondelete="CASCADE"),
#         nullable=False,
#         index=True
#     )

#     # -------- INPUT SECTION --------
#     annual_exceedence_probability = db.Column(Float)
#     rainfall_intensity_increase_allowance = db.Column(Float)
#     maximum_storm_duration = db.Column(Integer)

#     roof_area = db.Column(Float)
#     roof_coefficient = db.Column(Float)
#     carpark_area = db.Column(Float)
#     carpark_coefficient = db.Column(Float)
#     landscaping_area = db.Column(Float)
#     landscaping_coefficient = db.Column(Float)

#     soil_permeability = db.Column(Float)
#     detention_tank_discharge_allowance = db.Column(Float)

#     # -------- CATCHMENT SECTION --------
#     roof_depth_mm = db.Column(Float)
#     carpark_depth_mm = db.Column(Float)
#     landscaping_depth_mm = db.Column(Float)

#     precast_soakwells = db.Column(JSONB)
#     stormwater_pipes = db.Column(JSONB)

#     other_additional_volume = db.Column(Float)

#     # -------- TANK SECTION --------
#     constraint_type = db.Column(String(50))  # length/width
#     constraint_value = db.Column(Float)

#     approx_net_volume_depth = db.Column(Float)
#     tank_width = db.Column(Float)
#     tank_depth = db.Column(Float)

#     bluemetal_base_height = db.Column(Float)
#     bluemetal_base_factor = db.Column(Float)

#     include_water_half_height_peripheral = db.Column(Boolean)

#     region = db.Column(String(50))

#     created_at = db.Column(TIMESTAMP,server_default=func.now(),nullable=False)

#     updated_at = db.Column(TIMESTAMP,server_default=func.now(),onupdate=func.now(),nullable=False)


#     project = relationship(
#         "ProjectInfo",
#         back_populates="stormwater",
#         passive_deletes=True
#     )



import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy import Float, Integer, Boolean, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship


class StormwaterSizingCalculation(db.Model):
    __tablename__ = "tbl_stormwater_sizing_project_inputs"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ✅ FIXED FOREIGN KEY
    project_id = db.Column(
        UUID(as_uuid=True),
        ForeignKey("tbl_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # -------- INPUT SECTION --------
    annual_exceedence_probability = db.Column(Float)
    rainfall_intensity_increase_allowance = db.Column(Float)
    maximum_storm_duration = db.Column(Integer)

    roof_area = db.Column(Float)
    roof_coefficient = db.Column(Float)
    carpark_area = db.Column(Float)
    carpark_coefficient = db.Column(Float)
    landscaping_area = db.Column(Float)
    landscaping_coefficient = db.Column(Float)

    soil_permeability = db.Column(Float)
    detention_tank_discharge_allowance = db.Column(Float)

    # -------- CATCHMENT SECTION --------
    roof_depth_mm = db.Column(Float)
    carpark_depth_mm = db.Column(Float)
    landscaping_depth_mm = db.Column(Float)

    precast_soakwells = db.Column(JSONB)
    stormwater_pipes = db.Column(JSONB)

    other_additional_volume = db.Column(Float)

    # -------- TANK SECTION --------
    constraint_type = db.Column(String(50))  # length/width
    tank_length = db.Column(Float)

    approx_net_volume_depth = db.Column(Float)
    tank_width = db.Column(Float)
    tank_depth = db.Column(Float)

    bluemetal_base_height = db.Column(Float)
    bluemetal_base_factor = db.Column(Float)

    include_water_half_height_peripheral = db.Column(Boolean)

    created_at = db.Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    updated_at = db.Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # ✅ FIXED RELATIONSHIP
    project = relationship(
        "Project",
        back_populates="stormwater"
    )