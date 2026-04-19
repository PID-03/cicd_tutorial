# import uuid
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy import UniqueConstraint, Index
# from sqlalchemy.sql import func
# from datetime import datetime

# from extensions import db


# # ==========================================================
# # IFD REGIONS TABLE
# # ==========================================================
# class IFDRegion(db.Model):
#     __tablename__ = "ifd_regions"

#     id = db.Column(
#         UUID(as_uuid=True),
#         primary_key=True,
#         default=uuid.uuid4
#     )

#     name = db.Column(
#         db.String(200),
#         nullable=False,
#         unique=True,
#         index=True
#     )

#     created_at = db.Column(
#         db.TIMESTAMP,
#         server_default=func.now()
#     )

#     # Relationship
#     ifd_data = db.relationship(
#         "IFDRegionData",
#         backref="region",
#         cascade="all, delete-orphan",
#         lazy=True
#     )

#     def __repr__(self):
#         return f"<IFDRegion {self.name}>"



# # ==========================================================
# # IFD REGION DATA TABLE
# # ==========================================================
# class IFDRegionData(db.Model):
#     __tablename__ = "ifd_region_data"

#     id = db.Column(
#         UUID(as_uuid=True),
#         primary_key=True,
#         default=uuid.uuid4
#     )

#     region_id = db.Column(
#         UUID(as_uuid=True),
#         db.ForeignKey("ifd_regions.id", ondelete="CASCADE"),
#         nullable=False,
#         index=True
#     )

#     duration_minutes = db.Column(
#         db.Integer,
#         nullable=False,
#         index=True
#     )

#     aep_percentage = db.Column(
#         db.Float,
#         nullable=False
#     )

#     intensity = db.Column(
#         db.Float,
#         nullable=False
#     )

#     created_at = db.Column(
#         db.TIMESTAMP,
#         server_default=func.now()
#     )

#     # Unique + Performance Index
#     __table_args__ = (
#         UniqueConstraint(
#             "region_id",
#             "duration_minutes",
#             "aep_percentage",
#             name="uq_region_duration_aep"
#         ),
#         Index(
#             "idx_ifd_lookup",
#             "region_id",
#             "duration_minutes",
#             "aep_percentage"
#         ),
#     )

#     def __repr__(self):
#         return (
#             f"<IFDRegionData "
#             f"Region={self.region_id} "
#             f"Duration={self.duration_minutes} "
#             f"AEP={self.aep_percentage} "
#             f"Intensity={self.intensity}>"
#         )

import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import UniqueConstraint, Index, Sequence
from sqlalchemy.sql import func

from extensions import db


# ==========================================================
# IFD REGIONS TABLE
# ==========================================================
class IFDRegion(db.Model):
    __tablename__ = "tbl_ifd_region"

    # ------------------------------------------
    # Primary UUID
    # ------------------------------------------
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # ------------------------------------------
    # Auto Increment Region Number (Human ID)
    # ------------------------------------------
    region_number_seq = Sequence("region_number_seq")

    region_number = db.Column(
        db.Integer,
        region_number_seq,
        server_default=region_number_seq.next_value(),
        unique=True,
        nullable=False,
        index=True
    )

    # ------------------------------------------
    # Region Name
    # ------------------------------------------
    name = db.Column(
        db.String(200),
        nullable=False,
        unique=True,
        index=True
    )

    # ------------------------------------------
    # Geographic Coordinates
    # ------------------------------------------
    latitude = db.Column(
        db.Float,
        nullable=True
    )

    longitude = db.Column(
        db.Float,
        nullable=True
    )

    # ------------------------------------------
    # Soft Delete Fields
    # ------------------------------------------
    is_deleted = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        index=True
    )

    deleted_at = db.Column(
        db.TIMESTAMP,
        nullable=True
    )

    # ------------------------------------------
    # Audit Fields
    # ------------------------------------------
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

    # ------------------------------------------
    # Relationship
    # ------------------------------------------
    ifd_data = db.relationship(
        "IFDRegionData",
        backref="region",
        cascade="all, delete-orphan",
        lazy=True
    )

    # ------------------------------------------
    # Soft Delete Methods
    # ------------------------------------------
    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None

    def __repr__(self):
        return (
            f"<IFDRegion "
            f"name={self.name} "
            f"region_number={self.region_number} "
            f"lat={self.latitude} "
            f"lon={self.longitude}>"
        )


# ==========================================================
# IFD REGION DATA TABLE
# ==========================================================
class IFDRegionData(db.Model):
    __tablename__ = "tbl_ifd_data"

    # ------------------------------------------
    # Primary UUID
    # ------------------------------------------
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # ------------------------------------------
    # Foreign Key to Region
    # ------------------------------------------
    region_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("tbl_ifd_region.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ------------------------------------------
    # IFD Parameters
    # ------------------------------------------
    duration_minutes = db.Column(
        db.Integer,
        nullable=False,
        index=True
    )

    aep_percentage = db.Column(
        db.Float,
        nullable=False,
        index=True
    )

    intensity = db.Column(
        db.Float,
        nullable=False
    )

    # ------------------------------------------
    # Soft Delete Fields
    # ------------------------------------------
    is_deleted = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        index=True
    )

    deleted_at = db.Column(
        db.TIMESTAMP,
        nullable=True
    )

    # ------------------------------------------
    # Audit Fields
    # ------------------------------------------
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

    # ------------------------------------------
    # Constraints & Indexing
    # ------------------------------------------
    __table_args__ = (
        UniqueConstraint(
            "region_id",
            "duration_minutes",
            "aep_percentage",
            name="uq_tbl_ifd_data_region_duration_aep"
        ),
        Index(
            "idx_tbl_ifd_lookup",
            "region_id",
            "duration_minutes",
            "aep_percentage"
        ),
    )

    # ------------------------------------------
    # Soft Delete Methods
    # ------------------------------------------
    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None

    def __repr__(self):
        return (
            f"<IFDRegionData "
            f"region_id={self.region_id} "
            f"duration={self.duration_minutes} "
            f"aep={self.aep_percentage} "
            f"intensity={self.intensity}>"
        )