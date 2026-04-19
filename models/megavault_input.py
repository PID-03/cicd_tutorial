import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy import Float, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship


class MegavaultInput(db.Model):
    __tablename__ = "tbl_megavault_input"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    project_id = db.Column(
        UUID(as_uuid=True),
        ForeignKey("tbl_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # -------- GRID SECTION --------
    grid      = db.Column(JSONB, nullable=False)
    direction = db.Column(String(10), nullable=False)

    # -------- HEIGHT & STORAGE --------
    internal_height    = db.Column(Float, nullable=False)
    max_storage_height = db.Column(Float, nullable=False)

    # -------- TANK SETTINGS --------
    tank_grade    = db.Column(Float, nullable=False)
    target_volume = db.Column(Float, nullable=False)

    # -------- CHAMBER & FILTER --------
    head_chamber  = db.Column(String(10), nullable=False)
    hed_volume    = db.Column(Float, nullable=False, default=0)
    filter_volume = db.Column(Float, nullable=False, default=0)

    # -------- OSD --------
    osd_invert_level = db.Column(Float, nullable=False, default=0)

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

    # -------- RELATIONSHIP --------
    project = relationship(
        "Project",
        back_populates="megavault"
    )