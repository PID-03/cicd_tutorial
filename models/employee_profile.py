import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID

class EmployeeProfile(db.Model):

    __tablename__ = "tbl_employee_profiles"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("tbl_users.id"),
        nullable=False,
        unique=True
    )

    employee_id = db.Column(db.String(100), unique=True)

    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)

    department = db.Column(db.String(100))
    designation = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now())