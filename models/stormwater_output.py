# import uuid
# from extensions import db
# from sqlalchemy.dialects.postgresql import UUID,JSONB
# from sqlalchemy.sql import func
# from sqlalchemy import Float, ForeignKey, TIMESTAMP
# from sqlalchemy.orm import relationship

# #new models

# class StormwaterAreaParameters(db.Model):
#     __tablename__ = "tbl_stormwater_sizing_input_outputs"

#     id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

#     project_id = db.Column(
#         UUID(as_uuid=True),
#         ForeignKey("project_info.id", ondelete="CASCADE"),
#         nullable=False,
#         index=True
#     )

#     # -------- AREA & SOIL PARAMETERS --------
#     equivalent_area = db.Column(Float)
#     soil_permiability_mm_day = db.Column(Float)
#     detention_tank_allowance_m3_per_hour = db.Column(Float)

#     # -------- TIMESTAMPS --------
#     created_at = db.Column(
#         TIMESTAMP,
#         server_default=func.now()
#     )

#     updated_at = db.Column(
#         TIMESTAMP,
#         server_default=func.now(),
#         onupdate=func.now()
#     )

#     # -------- RELATIONSHIP --------
#     project = relationship(
#         "ProjectInfo",
#         backref="area_parameters",
#         passive_deletes=True
#     )


# class AdditionalVolumeOutput(db.Model):
#     __tablename__ = "tbl_stormwater_sizing_additional_area_outputs"

#     id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

#     project_id = db.Column(
#         UUID(as_uuid=True),
#         ForeignKey("project_info.id", ondelete="CASCADE"),
#         nullable=False,
#         index=True
#     )

#     # -------- CATCHMENT AREAS --------
#     roof_catchment_area = db.Column(Float)
#     carpark_catchment_area = db.Column(Float)
#     landscaping_catchment_area = db.Column(Float)

#     # -------- STORAGE --------
#     total_additional_storage = db.Column(Float)

#     # -------- STRUCTURED DATA --------
#     precast_soakwell_area = db.Column(JSONB)
#     stormwater_pipes = db.Column(JSONB)
#     other_additional_area = db.Column(Float)

#     # -------- TIMESTAMPS --------
#     created_at = db.Column(
#         TIMESTAMP,
#         server_default=func.now()
#     )

#     updated_at = db.Column(
#         TIMESTAMP,
#         server_default=func.now(),
#         onupdate=func.now()
#     )

#     # -------- RELATIONSHIP --------
#     project = relationship(
#         "ProjectInfo",
#         backref="additional_area_outputs",
#         passive_deletes=True
#     )


# class StormwaterTankCalculation(db.Model):
#     __tablename__ = "tbl_stormwater_sizing_tank_outputs"

#     id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

#     project_id = db.Column(
#         UUID(as_uuid=True),
#         ForeignKey("project_info.id", ondelete="CASCADE"),
#         nullable=False,
#         index=True
#     )

#     # -------- VOLUME INPUT --------
#     volume_provided = db.Column(Float)
#     volume_required = db.Column(Float)

#     # -------- TANK DIMENSIONS --------
#     tank_length = db.Column(Float)
#     tank_width = db.Column(Float)
#     tank_bredth = db.Column(Float)
#     module_length = db.Column(Float)
#     module_width = db.Column(Float)
#     module_breadth = db.Column(Float)

#     # -------- VOLUME CALCULATIONS --------
#     gross_volume = db.Column(Float)
#     net_volume = db.Column(Float)

#     bluemetal_gross_volume = db.Column(Float)
#     bluemetal_net_volume = db.Column(Float)

#     tank_base_soakwell_base_max_stormwater_height = db.Column(Float)

#     graph = db.Column(JSONB)

#     # -------- TIMESTAMPS --------
#     created_at = db.Column(TIMESTAMP, server_default=func.now())
#     updated_at = db.Column(
#         TIMESTAMP,
#         server_default=func.now(),
#         onupdate=func.now()
#     )

#     # -------- RELATIONSHIP --------
#     project = relationship(
#         "ProjectInfo",
#         backref="volume_calculation_v2",
#         passive_deletes=True
#     )   



import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID,JSONB
from sqlalchemy.sql import func
from sqlalchemy import Float, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship


class StormwaterAreaParameters(db.Model):
    __tablename__ = "tbl_stormwater_sizing_input_outputs"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ✅ FIXED FK
    project_id = db.Column(
        UUID(as_uuid=True),
        ForeignKey("tbl_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # AREA & SOIL PARAMETERS
    equivalent_area = db.Column(Float)
    soil_permiability_mm_day = db.Column(Float)
    detention_tank_allowance_m3_per_hour = db.Column(Float)

    # TIMESTAMPS
    created_at = db.Column(TIMESTAMP, server_default=func.now())
    updated_at = db.Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )

    # ✅ FIXED RELATIONSHIP
    project = relationship(
        "Project",
        back_populates="area_parameters"
    )

class AdditionalVolumeOutput(db.Model):
    __tablename__ = "tbl_stormwater_sizing_additional_area_outputs"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ✅ FIXED FK
    project_id = db.Column(
        UUID(as_uuid=True),
        ForeignKey("tbl_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # CATCHMENT AREAS
    roof_catchment_area = db.Column(Float)
    carpark_catchment_area = db.Column(Float)
    landscaping_catchment_area = db.Column(Float)

    # STORAGE
    total_additional_storage = db.Column(Float)

    # STRUCTURED DATA
    precast_soakwell_area = db.Column(JSONB)
    stormwater_pipes = db.Column(JSONB)
    other_additional_area = db.Column(Float)

    # TIMESTAMPS
    created_at = db.Column(TIMESTAMP, server_default=func.now())
    updated_at = db.Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )

    # ✅ FIXED RELATIONSHIP
    project = relationship(
        "Project",
        back_populates="additional_area_outputs"
    )



class StormwaterTankCalculation(db.Model):
    __tablename__ = "tbl_stormwater_sizing_tank_outputs"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ✅ FIXED FK
    project_id = db.Column(
        UUID(as_uuid=True),
        ForeignKey("tbl_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # VOLUME INPUT
    volume_provided = db.Column(Float)
    volume_required = db.Column(Float)

    # TANK DIMENSIONS
    tank_length = db.Column(Float)
    tank_width = db.Column(Float)
    tank_bredth = db.Column(Float)
    module_length = db.Column(Float)
    module_width = db.Column(Float)
    module_breadth = db.Column(Float)

    # VOLUME CALCULATIONS
    gross_volume = db.Column(Float)
    net_volume = db.Column(Float)

    bluemetal_gross_volume = db.Column(Float)
    bluemetal_net_volume = db.Column(Float)

    tank_base_soakwell_base_max_stormwater_height = db.Column(Float)

    graph = db.Column(JSONB)

    # TIMESTAMPS
    created_at = db.Column(TIMESTAMP, server_default=func.now())
    updated_at = db.Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )

    # ✅ FIXED RELATIONSHIP
    project = relationship(
        "Project",
        back_populates="tank_outputs"
    )