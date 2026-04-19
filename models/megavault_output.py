import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy import Float, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship


class MegavaultOutput(db.Model):
    __tablename__ = "tbl_megavault_output"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    project_id = db.Column(
        UUID(as_uuid=True),
        ForeignKey("tbl_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    input_id = db.Column(
        UUID(as_uuid=True),
        ForeignKey("tbl_megavault_input.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # -------- MODULE COUNTS --------
    selected_modules  = db.Column(Float, nullable=False)
    modules_required  = db.Column(Float, nullable=False)

    # -------- TANK DIMENSIONS --------
    tank_length = db.Column(Float, nullable=False)
    tank_width  = db.Column(Float, nullable=False)

    # -------- STORAGE HEIGHTS --------
    min_storage_height       = db.Column(Float, nullable=False)
    effective_storage_height = db.Column(Float, nullable=False)

    # -------- VOLUMES --------
    total_volume_per_base     = db.Column(Float, nullable=False)
    effective_volume_per_base = db.Column(Float, nullable=False)
    proposed_total_volume     = db.Column(Float, nullable=False)
    proposed_effective_volume = db.Column(Float, nullable=False)

    # -------- OSD CURVE (arrays stored as JSONB) --------
    elevations    = db.Column(JSONB, nullable=False)   # list of 4 floats
    surface_areas = db.Column(JSONB, nullable=False)   # list of 4 floats

    # -------- TIMESTAMPS --------
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

    # -------- RELATIONSHIPS --------
    project = relationship("Project", back_populates="megavault_output")
    input   = relationship("MegavaultInput", backref="output")