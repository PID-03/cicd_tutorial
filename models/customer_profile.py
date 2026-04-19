import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID

# class CustomerProfile(db.Model):

#     __tablename__ = "tbl_customer_profiles"

#     id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

#     user_id = db.Column(
#         db.UUID(as_uuid=True),
#         db.ForeignKey("tbl_users.id"),
#         nullable=False,
#         unique=True
#     )

#     first_name = db.Column(db.String(100), nullable=False)
#     last_name = db.Column(db.String(100), nullable=False)

#     company_name = db.Column(db.String(255))
#     consent = db.Column(db.Boolean, default=False)

#     created_at = db.Column(db.DateTime, server_default=db.func.now())
#     updated_at = db.Column(db.DateTime, server_default=db.func.now())


class CustomerProfile(db.Model):

    __tablename__ = "tbl_customer_profiles"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

   
    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("tbl_users.id"),
        nullable=True,
        unique=True
    )

   
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)

  
    company_name = db.Column(db.String(255))
    company_email = db.Column(db.String(255))
    company_phone = db.Column(db.String(50))
    company_address = db.Column(db.Text)

   
    personal_phone = db.Column(db.String(50))



    customer_type = db.Column(db.String(20), nullable=False)
    # "SELF"  → signup / google login
    # "STAFF" → created by staff

    # 👨‍💼 Who created (only for STAFF customers)
    created_by_user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("tbl_users.id"),
        nullable=True
    )
    created_by = db.relationship(
    "User",
    foreign_keys=[created_by_user_id],
    backref="created_customers"
)

    # 📜 Consent (used for signup users)
    consent = db.Column(db.Boolean, default=False)

    # ⏱ Timestamps
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now())