import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import Integer, Float,REAL, Numeric, TIMESTAMP


# class IFDData(db.Model):
#     __tablename__ = "ifd_data"

#     id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

#     duration_minutes = db.Column(Integer, nullable=False, index=True)

#     aep_percentage = db.Column(REAL, nullable=False, index=True)
#     intensity = db.Column(REAL, nullable=False)

#     created_at = db.Column(TIMESTAMP, server_default=func.now())

#     __table_args__ = (
#         db.Index("idx_ifd_lookup", "duration_minutes", "aep_percentage"),
#     )

from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION

class IFDData(db.Model):
    __tablename__ = "ifd_data"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    duration_minutes = db.Column(Integer, nullable=False, index=True)

    aep_percentage = db.Column(db.Float(precision=53), nullable=False)
    intensity = db.Column(db.Float(precision=53), nullable=False)

    created_at = db.Column(TIMESTAMP, server_default=func.now())

class PrecastSoakwellSpec(db.Model):
    __tablename__ = "precast_soakwell_data"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    model_label = db.Column(db.String(50), nullable=False)

    diameter_mm = db.Column(db.Integer, nullable=False, index=True)
    height_mm = db.Column(db.Integer, nullable=False)

    volume_m3 = db.Column(db.Float, nullable=False)
    weep_hole_area_m2 = db.Column(db.Float, nullable=False)

    created_at = db.Column(TIMESTAMP, server_default=func.now())


class CircularAreaReference(db.Model):
    __tablename__ = "stormwater_pipe_size"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    diameter_mm = db.Column(db.Integer, nullable=False, index=True)
    radius_m = db.Column(db.Float, nullable=False)
    area_m2 = db.Column(db.Float, nullable=False)

    label = db.Column(db.String(50))

    created_at = db.Column(TIMESTAMP, server_default=func.now())