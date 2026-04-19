import uuid
from extensions import db

class Company(db.Model):

    __tablename__ = "tbl_companies"

    id = db.Column(
        db.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    company_name = db.Column(
        db.String(150),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )