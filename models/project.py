

import enum
import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import Enum, String, Boolean, TIMESTAMP, ForeignKey, Text

def normalize_enum(enum_class, value):
    if not value:
        return None

    value = value.strip().lower()

    for e in enum_class:
        if e.value.lower() == value:
            return e

    raise ValueError(f"Invalid value '{value}' for {enum_class.__name__}")

class CalculatorType(enum.Enum):
    DETENTION = "Detention"
    INFILTRATION = "Infiltration"

class ProjectStatus(enum.Enum):
    DRAFT  = "draft"
    COMPLETED  = "completed"


class Project(db.Model):
    __tablename__ = "tbl_projects"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    project_name = db.Column(String(255), nullable=False)
    project_address = db.Column(Text, nullable=True)

    # client_name = db.Column(String(255), nullable=True)
    customer_id = db.Column(
    UUID(as_uuid=True),
    db.ForeignKey("tbl_customer_profiles.id"),
    nullable=True
)

    rainfall_location_id = db.Column(UUID(as_uuid=True), nullable=True)
    
    calculator_type = db.Column(
    Enum(
        CalculatorType,
        name="calculator_type_enum",
        values_callable=lambda obj: [e.value for e in obj]  
    ),
    nullable=False
)

    status = db.Column(
    Enum(
        ProjectStatus,
        name="project_status_enum",
        values_callable=lambda obj: [e.value for e in obj]  
    ),
    nullable=False,
    default=ProjectStatus.DRAFT
)

    user_id = db.Column(UUID(as_uuid=True), ForeignKey("tbl_users.id", ondelete="CASCADE"), nullable=False)

    # created_by = db.Column(UUID(as_uuid=True), nullable=True)

    del_flg = db.Column(Boolean, default=False, nullable=False)

    volume_known = db.Column(db.Boolean, default=False)

    created_at = db.Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    user = db.relationship("User", back_populates="projects")

    updated_at = db.Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

     # Relationships
    stormwater = db.relationship(
        "StormwaterSizingCalculation",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    customer = db.relationship("CustomerProfile")

    area_parameters = db.relationship(
        "StormwaterAreaParameters",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    additional_area_outputs = db.relationship(
        "AdditionalVolumeOutput",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    tank_outputs = db.relationship(
        "StormwaterTankCalculation",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    ecocube = db.relationship(
    "EcocubeCostCalculation",
    back_populates="project",
    cascade="all, delete-orphan"
)

    megavault = db.relationship(
    "MegavaultInput",
    back_populates="project",
    cascade="all, delete-orphan",
    passive_deletes=True
)

    megavault_output = db.relationship(
    "MegavaultOutput",
    back_populates="project",
    cascade="all, delete-orphan",
    passive_deletes=True
)
    