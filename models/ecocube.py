
import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import Integer, Boolean, Float, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship


# class EcocubeCostCalculation(db.Model):
#     __tablename__ = "ecocube_cost_calculation"

#     id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

#     # ✅ FIXED FOREIGN KEY
#     project_id = db.Column(
#         UUID(as_uuid=True),
#         ForeignKey("tbl_projects.id", ondelete="CASCADE"),
#         nullable=False,
#         index=True
#     )

#     available_depth_to_invert = db.Column(Integer)
#     max_layers_possible = db.Column(Integer)
#     layers_in_system = db.Column(Integer)

#     include_liner = db.Column(Boolean)
#     target_storage_volume = db.Column(Float)

#     constraining_factor = db.Column(String(50))
#     constraining_dimension = db.Column(Float)

#     number_of_outlets = db.Column(Integer, default=0)
#     number_of_inlets = db.Column(Integer, default=0)

#     created_at = db.Column(TIMESTAMP, server_default=func.now())

#     # ✅ FIXED RELATIONSHIP
#     project = relationship(
#         "Project",
#         back_populates="ecocube"
#     )

#     # output = relationship(
#     #     "EcocubeOutput",
#     #     back_populates="ecocube",
#     #     uselist=False,
#     #     cascade="all, delete-orphan"
#     # )

# class EcocubeOutput(db.Model):
#     __tablename__ = "ecocube_output"

#     id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

#     project_id = db.Column(          # ✅ Changed from ecocube_id to project_id
#         UUID(as_uuid=True),
#         # ForeignKey("project_info.id", ondelete="CASCADE"),  # ✅ Points to project_info like stormwater
#         ForeignKey("tbl_projects.id", ondelete="CASCADE"),
#         nullable=False,
#         unique=True,
#         index=True
#     )

#     # SYSTEM LAYOUT
#     metres_wide = db.Column(Float)
#     metres_long = db.Column(Float)
#     cubes_wide = db.Column(Integer)
#     cubes_long = db.Column(Integer)

#     system_footprint = db.Column(Float)
#     tank_storage = db.Column(Float)
#     excavation_volume = db.Column(Float)
#     initial_backfill_required = db.Column(Float)
#     final_backfill_required = db.Column(Float)

#     half_cubes = db.Column(Integer)
#     side_plates = db.Column(Integer)
#     double_clips = db.Column(Integer)
#     single_clips = db.Column(Integer)

#     # MATERIAL
#     non_woven_geotextile = db.Column(Float)
#     liner_required = db.Column(Float)

#     created_at = db.Column(TIMESTAMP, server_default=func.now())

#     # ecocube = relationship(
#     #     "EcocubeCostCalculation",
#     #     back_populates="output"
#     # )

# class EcocubeData(db.Model):
#     __tablename__ = "ecocube_data"

#     id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

#     module_width = db.Column(Float)
#     module_length = db.Column(Float)
#     module_height = db.Column(Float)
#     cube_water_capacity = db.Column(Float)

#     side_plate_width = db.Column(Integer)
#     side_backfill_width = db.Column(Float)

#     geotextile_overlap_wastage = db.Column(Float)
#     liner_wastage = db.Column(Float)

#     created_at = db.Column(TIMESTAMP, server_default=func.now())

# class EcocubeGeometryOutput(db.Model):
#     __tablename__ = "ecocube_geometry_output"

#     project_id = db.Column(
#         UUID(as_uuid=True),
#         db.ForeignKey("project_info.id", ondelete="CASCADE"),
#         primary_key=True
#     )

#     finished_surface_level = db.Column(db.Float)
#     double_stack           = db.Column(db.Float)
#     outlet_invert_level    = db.Column(db.Float)
#     cover_depth = db.Column(db.Float)
#     length_mm  = db.Column(db.Float)
#     breadth_mm = db.Column(db.Float)
#     height_mm  = db.Column(db.Float)

#     minimum_cover_depth = db.Column(
#         db.Float,
#         default=100.0
#     )

class EcocubeCostCalculation(db.Model):
    __tablename__ = "tbl_ecocube_cost_calculation"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    project_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("tbl_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    available_depth_to_invert = db.Column(db.Integer)
    max_layers_possible = db.Column(db.Integer)
    layers_in_system = db.Column(db.Integer)

    # include_liner = db.Column(db.Boolean)
    include_liner = db.Column(db.String(3),nullable=False,default="no")
    target_storage_volume = db.Column(db.Float)

    constraining_factor = db.Column(db.String(50))
    constraining_dimension = db.Column(db.Float)

    number_of_outlets = db.Column(db.Integer, default=0)
    number_of_inlets = db.Column(db.Integer, default=0)

    created_at = db.Column(
        db.TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    updated_at = db.Column(
        db.TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    project = db.relationship(
        "Project",
        back_populates="ecocube"
    )



class EcocubeOutput(db.Model):
    __tablename__ = "tbl_ecocube_output"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    project_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("tbl_projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    metres_wide = db.Column(db.Float)
    metres_long = db.Column(db.Float)
    cubes_wide = db.Column(db.Integer)
    cubes_long = db.Column(db.Integer)

    system_footprint = db.Column(db.Float)
    tank_storage = db.Column(db.Float)
    excavation_volume = db.Column(db.Float)
    initial_backfill_required = db.Column(db.Float)
    final_backfill_required = db.Column(db.Float)

    half_cubes = db.Column(db.Integer)
    side_plates = db.Column(db.Integer)
    double_clips = db.Column(db.Integer)
    single_clips = db.Column(db.Integer)

    non_woven_geotextile = db.Column(db.Float)
    liner_required = db.Column(db.Float)

    created_at = db.Column(
        db.TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    updated_at = db.Column(
        db.TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

class EcocubeData(db.Model):
    __tablename__ = "tbl_ecocube_data"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    module_width = db.Column(db.Float)
    module_length = db.Column(db.Float)
    module_height = db.Column(db.Float)
    cube_water_capacity = db.Column(db.Float)

    side_plate_width = db.Column(db.Integer)
    side_backfill_width = db.Column(db.Float)

    geotextile_overlap_wastage = db.Column(db.Float)
    liner_wastage = db.Column(db.Float)

    created_at = db.Column(
        db.TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    updated_at = db.Column(
        db.TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
class EcocubeGeometryOutput(db.Model):
    __tablename__ = "tbl_ecocube_geometry_output"

    project_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("tbl_projects.id", ondelete="CASCADE"),
        primary_key=True
    )

    finished_surface_level = db.Column(db.Float)
    double_stack = db.Column(db.Float)
    outlet_invert_level = db.Column(db.Float)

    cover_depth = db.Column(db.Float)
    length_mm = db.Column(db.Float)
    breadth_mm = db.Column(db.Float)
    height_mm = db.Column(db.Float)

    minimum_cover_depth = db.Column(db.Float, default=100.0)

    created_at = db.Column(
        db.TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    updated_at = db.Column(
        db.TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )