import re
import token

from flask import request
from pygments import token
from werkzeug.security import generate_password_hash
from datetime import datetime
# from models.company import  Company
from datetime import datetime, timedelta
from models.customer_profile import CustomerProfile
from models.employee_profile import EmployeeProfile
from models.user import User,UserSession,UserRole,Role
from extensions import db
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, decode_token
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from utils.email import send_email

class AuthService:

   

    @staticmethod
    def signup(data):

        full_name = data.get("full_name")
        email = data.get("email")
        password = data.get("password").strip()
        company_name = data.get("company_name")
        company_email = data.get("company_email")
        company_phone = data.get("company_phone")
        company_address = data.get("company_address")
        personal_phone = data.get("personal_phone")
        

       
        existing_user = User.query.filter_by(
            email=email,
            del_flg=False
        ).first()

        if existing_user:
            return False, "User already exists"

      
        role = Role.query.filter_by(
            role_name="CUSTOMER",
            del_flg=False
        ).first()

        if not role:
            return False, "Default role not configured"

       
        user = User(
            email=email,
            auth_provider="email",
            is_active=True
        )
        user.set_password(password)

        db.session.add(user)
        db.session.flush()

        
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id
        )
        db.session.add(user_role)

      
        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else None

        # Create customer profile
        customer_profile = CustomerProfile(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            company_name=company_name,
            company_email=company_email,
            company_phone=company_phone,
            company_address=company_address,
            personal_phone=personal_phone,
   
            consent=True,
            customer_type="SELF"
        )

        db.session.add(customer_profile)

        db.session.commit()

        return True, "Account created successfully"
    
    @staticmethod
    def create_by_staff(data, staff_user_id):

        # Optional: check staff role
        user = User.query.get(staff_user_id)
        roles = [ur.role.role_name for ur in user.user_roles]

        if not any(r in roles for r in ["ADMIN", "ENGINEER", "SUPER_ADMIN"]):
            return False, "Unauthorized"

        full_name = data.get("full_name")
        email = data.get("email")
        password = data.get("password").strip()
        company_name = data.get("company_name")
        company_email = data.get("company_email")
        company_phone = data.get("company_phone")
        company_address = data.get("company_address")
        personal_phone = data.get("personal_phone")

        existing_user = User.query.filter_by(
        email=email,
        del_flg=False
    ).first()
        
        if existing_user:
            return False, "User already exists"
        
        new_user = User(
        email=email,
        auth_provider="email",
        is_active=True
    )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()

        role = Role.query.filter_by(
        role_name="CUSTOMER",
        del_flg=False
    ).first()
        
        if not role:
            return False, "Default role not configured"
        
        user_role = UserRole(
        user_id=new_user.id,
        role_id=role.id
    )
        db.session.add(user_role)

        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else None
        


        
        
        
        
            

        customer = CustomerProfile(
        user_id=new_user.id,   # 🔥 always linked now
        first_name=first_name,
        last_name=last_name,
        company_name=company_name,
        company_email=company_email,
        company_phone=company_phone,
        company_address=company_address,
        personal_phone=personal_phone,
        customer_type="STAFF",
        created_by_user_id=staff_user_id
        )

        db.session.add(customer)
        db.session.commit()

        return True, "Customer created successfully"
    
    @staticmethod
    def get_staff_customers(user_id, search=None):
        user = User.query.get(user_id)
        roles = [ur.role.role_name for ur in user.user_roles]
        if not any(r in roles for r in ["ADMIN", "ENGINEER", "SUPER_ADMIN"]):
            return False, "Unauthorized"
        
        query = CustomerProfile.query.filter(
        CustomerProfile.customer_type == "STAFF"
    )
        
        if search:
            query = query.filter(
            db.or_(
                CustomerProfile.first_name.ilike(f"%{search}%"),
                CustomerProfile.last_name.ilike(f"%{search}%")
            )
        )
        customers = query.order_by(CustomerProfile.created_at.desc()).all()
        result = [
        {
            "id": str(c.id),
            "name": f"{c.first_name} {c.last_name or ''}".strip(),
            "company_name": c.company_name
        }
        for c in customers
    ]
        return True, result

            
            

            
        
        
        

        
            
        
        

    

    
    


    @staticmethod
    def login(data, request, expected_role):

        email = data.get("email")
        password = data.get("password").strip()

        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

        if not re.match(email_pattern, email):
            return False, "Invalid email format", None
        
        user = User.query.filter_by(email=email, del_flg=False,is_active=True).first()
        if not user:
            return False, "User not found", None
        if not user.password_hash or not user.check_password(password):
            return False, "Invalid credentials", None
        
        
        roles = [ur.role.role_name for ur in user.user_roles]

        if not roles:
            return False, "User has no assigned role", None
        
        is_customer = "CUSTOMER" in roles
        is_internal = any(r in roles for r in ["ENGINEER", "ADMIN", "SUPER_ADMIN"])
        


        if expected_role == "CUSTOMER" and not is_customer:
            return False, "Not a customer account", None
        
            
        if expected_role == "STAFF" and not is_internal:
            return False, "Not a staff account", None
        
        profile_data = {}
        name = ""

        if is_customer and user.customer_profile:
            profile = user.customer_profile
            name = f"{profile.first_name} {profile.last_name or ''}".strip()

            profile_data = {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "company_name": profile.company_name,
            "company_email": profile.company_email,
            "company_phone": profile.company_phone,
            "personal_phone": profile.personal_phone,
            "consent": profile.consent
        }
        
        elif is_internal and user.employee_profile:
            profile = user.employee_profile
            name = f"{profile.first_name} {profile.last_name or ''}".strip()

            profile_data = {
            "employee_id": profile.employee_id,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "department": profile.department,
            "designation": profile.designation

        }
            
        else:
            return False, "Invalid role configuration", None
        
        access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "email": user.email,
            "roles": roles
        }
    )
        session = UserSession(
        user_id=user.id,
        jwt_token=access_token,
        device_info=request.headers.get("User-Agent"),
        ip_address=request.remote_addr,
        expired_at=datetime.utcnow() + timedelta(days=7)
    )
        db.session.add(session)
        db.session.commit()

        response = {
        "status": True,
        "msg": "Login successful",
        "access_token": access_token,
        "user": {
            "id": str(user.id),
            "name": name,
            "email": user.email,
            "roles": roles,
            "type": "CUSTOMER" if is_customer else "STAFF",
            "profile": profile_data
        }
    }
        return True, "Login successful", response
        
            

        
        
        access_token = create_access_token(identity=str(user.id))
        response = {
        "status": True,
        "msg": "Login successful",
        "access_token": access_token,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "roles": roles
        }
    }
        return True, "Login successful", response
            
        
        
        

        

     
    


    @staticmethod
    def internal_signup(data):

        full_name = data.get("full_name")
        email = data.get("email")
        password = data.get("password").strip()
        role_name = data.get("role")  


        existing_user = User.query.filter_by(
            email=email,
            del_flg=False
        ).first()

        if existing_user:
            return False, "User already exists"

        allowed_roles = ["ENGINEER", "ADMIN"]

        if role_name not in allowed_roles:
            return False, "Invalid role for internal user"

        role = Role.query.filter_by(
            role_name=role_name,
            del_flg=False
        ).first()

        if not role:
            return False, "Role not configured"


        user = User(
            email=email,
            auth_provider="email",
            is_active=True
        )
        user.set_password(password)

        db.session.add(user)
        db.session.flush()

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id
        )
        db.session.add(user_role)

        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else None
        employee_id = data.get("employee_id")
        existing_employee = EmployeeProfile.query.filter_by(
    employee_id=employee_id
).first()
        
        if existing_employee:
            return False, "Employee ID already exists"
    


        employee_profile = EmployeeProfile(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            employee_id=data.get("employee_id"),
            department=data.get("department"),
            designation=data.get("designation")
        )

        db.session.add(employee_profile)

        db.session.commit()

        return True, "Internal user created successfully"
    

    @staticmethod
    def google_login(data, request):

        token = data.get("id_token")
        CLIENT_ID = "523116617752-71nb0p2fbmqtalsklpq4621u41uksvmn.apps.googleusercontent.com"

        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                CLIENT_ID
                # audience="YOUR_GOOGLE_CLIENT_ID"
            )

            email = idinfo.get("email")
            full_name = idinfo.get("name")

        except Exception:
            return False, "Invalid Google token", None

        # ---------------------------
        # Check existing user
        # ---------------------------
        user = User.query.filter_by(
            email=email,
            del_flg=False
        ).first()

        # ---------------------------
        # Create new user if not exists
        # ---------------------------
        if not user:

            role = Role.query.filter_by(
                role_name="CUSTOMER",
                del_flg=False
            ).first()

            if not role:
                return False, "Default role not configured", None

            user = User(
                email=email,
                auth_provider="google",
                is_active=True
            )

            db.session.add(user)
            db.session.flush()

            # Assign role
            user_role = UserRole(
                user_id=user.id,
                role_id=role.id
            )
            db.session.add(user_role)

            # Create profile
            name_parts = full_name.split(" ", 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else None

            customer_profile = CustomerProfile(
                user_id=user.id,
                first_name=first_name,
                last_name=last_name,
                consent=True
            )

            db.session.add(customer_profile)
            db.session.commit()

        # ---------------------------
        # Generate token
        # ---------------------------
        roles = [role.role_name for role in user.roles]

        token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "email": user.email,
                "roles": roles
            }
        )

        # ---------------------------
        # Create session
        # ---------------------------
        session = UserSession(
            user_id=user.id,
            jwt_token=token,
            device_info=request.headers.get("User-Agent"),
            ip_address=request.remote_addr,
            expired_at=datetime.utcnow() + timedelta(days=7)
        )

        db.session.add(session)
        db.session.commit()

        # ---------------------------
        # Profile data
        # ---------------------------
        profile = user.customer_profile

        response = {
            "status": True,
            "access_token": token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": f"{profile.first_name} {profile.last_name or ''}".strip(),
                "roles": roles,
                "type": "CUSTOMER",
                "profile": {
                    "first_name": profile.first_name,
                    "last_name": profile.last_name,
                    "company_name": profile.company_name,
                    "consent": profile.consent
                }
            }
        }

        return True, None, response

    @staticmethod
    def get_me(user_id):
        
        user = User.query.filter_by(
            id = user_id,
            is_active=True,
            del_flg=False
        ).first()

        if not user:
            return False, "User not found", None
        roles = [ur.role.role_name for ur in user.user_roles]

        if not roles:
            return False, "User has no assigned role", None
        
        if "CUSTOMER" in roles:
            profile = user.customer_profile
            name = f"{profile.first_name} {profile.last_name or ''}".strip()
            profile_data ={
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "company_name": profile.company_name,
                "consent": profile.consent
            }
            user_type = "CUSTOMER"
        else:
            profile = user.employee_profile
            name = f"{profile.first_name} {profile.last_name or ''}".strip()
            profile_data = {
                "employee_id": profile.employee_id,
                "department": profile.department,
                "designation": profile.designation
            }
            user_type = "INTERNAL"

        response = {
            "status": True,
            "user": {
                "id": str(user.id),
                "name": name,
                "email": user.email,
                "roles": roles,
                "type": user_type,
                "profile": profile_data
            }
        }
        return True, "User fetched successfully", response
    
    @staticmethod
    def forgot_password(data):
        email = data.get("email")

        user = User.query.filter_by(
            email = email,
            is_active=True,
            del_flg=False
        ).first()

        if not user:
            return False, "User not found"
        
        reset_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(minutes=15),
            additional_claims={
                "type": "reset"
            }
        )
        
        # reset_link = f"http://localhost:5001/api/reset-password?token={reset_token}"
        # print("RESET LINK:", reset_link)

        reset_link = f"http://76.13.245.134:3000/auth/reset-password?token={reset_token}"
        html_body = f"""
<div style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
    
    <div style="max-width: 600px; margin: auto; background: white; border-radius: 8px; overflow: hidden;">
        
        <!-- Header -->
        <div style="background: linear-gradient(to right, #1e90ff, #007bff); padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">Password Reset Request</h2>
        </div>

        <!-- Body -->
        <div style="padding: 20px; color: #333;">
            <p>Hi,</p>

            <p>
                We received a request to reset your password. If you did not request this,
                please ignore this email. Otherwise, click the button below to reset your password:
            </p>

            <!-- Button -->
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" target="_blank" 
                   style="
                        background-color: #007bff;
                        color: white;
                        padding: 12px 25px;
                        text-decoration: none;
                        border-radius: 5px;
                        font-weight: bold;
                        display: inline-block;
                   ">
                   Reset Password
                </a>
            </div>

            <p>
                If the button doesn't work, you can also reset your password by copying and pasting
                the link below into your browser:
            </p>

            <p>
    <a href="{reset_link}" style="color:#007bff; text-decoration:underline;"word-break: break-all;">
        Click here to reset your password
    </a>
</p>

            <p style="margin-top: 30px;">
                This link will expire in 15 minutes.
            </p>

            <p>Thanks,<br>Your Team</p>
        </div>

    </div>

</div>
"""

        send_email(
            to=email,
            subject="Password Reset Request",
            html_body=html_body
        )
        return True, "Reset password email sent"
    


    @staticmethod
    def reset_password(data):

        new_password = data.get("new_password")

        # ---------------------------
        # Get Token from Header
        # ---------------------------
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return False, "Authorization header missing"

        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            return False, "Invalid Authorization header format"

        # ---------------------------
        # Decode Token
        # ---------------------------
        try:
            decoded = decode_token(token)

            if decoded.get("type") != "reset":
                return False, "Invalid token type"

            user_id = decoded.get("sub")

        except Exception:
            return False, "Invalid or expired token"

        # ---------------------------
        # Get User
        # ---------------------------
        user = User.query.filter_by(
            id=user_id,
            del_flg=False,
            is_active=True
        ).first()

        if not user:
            return False, "User not found"

        # ---------------------------
        # Update Password
        # ---------------------------
        user.password_hash = generate_password_hash(new_password)

        db.session.commit()

        return True, "Password reset successful"
            



        


        
        
        

        
        

        
