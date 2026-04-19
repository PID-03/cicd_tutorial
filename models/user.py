
import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String
from werkzeug.security import generate_password_hash, check_password_hash

# ==========================
# ROLE MODEL
# ==========================

class Role(db.Model):

    __tablename__ = "tbl_roles"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    role_name = db.Column(db.String(50), unique=True, nullable=False)

    description = db.Column(db.String(255))

    del_flg = db.Column(db.Boolean, default=False)
    user_roles = db.relationship("UserRole", back_populates="role")

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now())






class User(db.Model):

    __tablename__ = "tbl_users"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    email = db.Column(db.String(255), unique=True, nullable=False)

    password_hash = db.Column(
        db.String(255),
        nullable=True 
    )

    auth_provider = db.Column(
        db.String(50),
        default="email" 
    )

    is_active = db.Column(db.Boolean, default=True)

    del_flg = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now())

    # roles = db.relationship(
    #     "Role",
    #     secondary="tbl_user_roles",
    #     backref="users"
    # )
    user_roles = db.relationship("UserRole", back_populates="user")
    projects = db.relationship(
        "Project",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # customer_profile = db.relationship(
    #     "CustomerProfile",
    #     backref="user",
    #     uselist=False,
    #     overlaps="user_roles,role"

    # )
    customer_profile = db.relationship(
    "CustomerProfile",
    backref="user",
    uselist=False,
    foreign_keys="CustomerProfile.user_id"   # 🔥 CRITICAL FIX
)

    employee_profile = db.relationship(
        "EmployeeProfile",
        backref="user",
        uselist=False
    )

    sessions = db.relationship(
        "UserSession",
        backref="user"
    )

    # 🔐 Password helpers
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)




class UserRole(db.Model):

    __tablename__ = "tbl_user_roles"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("tbl_users.id", ondelete="CASCADE"),
        nullable=False
    )

    role_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("tbl_roles.id", ondelete="CASCADE"),
        nullable=False
    )
    

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship("User", back_populates="user_roles")
    role = db.relationship("Role", back_populates="user_roles")

    __table_args__ = (
        db.UniqueConstraint('user_id', 'role_id', name='unique_user_role'),
        db.Index('idx_user_roles_user_id', 'user_id'),
        db.Index('idx_user_roles_role_id', 'role_id'),
    )




class UserSession(db.Model):

    __tablename__ = "tbl_user_sessions"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("tbl_users.id"),
        nullable=False
    )

    jwt_token = db.Column(db.Text)

    device_info = db.Column(db.String(255))
    ip_address = db.Column(db.String(100))

    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    expired_at = db.Column(db.DateTime, nullable=True)
