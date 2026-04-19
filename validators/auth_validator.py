
import re
from google.auth.transport import requests as google_requests
from flask import request
from rich import print

from models import user

class AuthValidator:

    @staticmethod
    def validate_signup(data):

        if not data:
            return False, ["Request body missing"]
       

        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[@#$%^&]).{8,}$"

        full_name = data.get("full_name")
        email = data.get("email")
        password = data.get("password")
        confirm_password = data.get("confirm_password")
        terms_accepted = data.get("terms_accepted")

        if not full_name and not email and not password:
            return False, "Full name, email and password required"
        
        
        if not full_name:
            return False, "Full name required"

        if not email:
            return False, "Email required"
        elif not re.match(email_pattern, email):
            return False, "Invalid email format"

        if not password:
            return False, "Password required"
        elif not re.match(password_pattern, password):
            return False, "Password must be at least 8 characters long, include 1 uppercase, 1 lowercase, and 1 special character (@#$%^&)"

        if password != confirm_password:
            return False, "Passwords do not match"

        if not terms_accepted:
            return False, "Terms must be accepted"

        return True, None
    

    @staticmethod
    def validate_create_by_staff(data):

        if not data:
            return False, "Request body missing"

        required_fields = ["first_name", "last_name"]

        for field in required_fields:
            if not data.get(field):
                return False, f"{field} is required"
            
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if password or confirm_password:
            if not password:
                return False, "Password required"
            if not confirm_password:
                return False, "Confirm password required"
            if password != confirm_password:
                return False, "Passwords do not match"
            
        

        return True, None
    


    @staticmethod
    def validate_login(data):

        if not data:
            return False, "Request body missing"

        email = data.get("email")
        password = data.get("password")
        

        if not email or not password:
            return False, "Email and Password required"
        
        

        return True, None
    

    @staticmethod
    def validate_internal_signup(data):

        if not data:
            return False, "Request body missing"

        required_fields = [
            "full_name",
            "email",
            "password",
            "confirm_password",
            "role", 
            "employee_id" 
        ]

        for field in required_fields:
            if not data.get(field):
                return False, f"{field} is required"
            
        email = data.get("email")
        password = data.get("password")

        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

        if not re.match(email_pattern, email):
            return False, "Invalid email format"
        
        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[@#$%^&]).{8,}$"

        if not re.match(password_pattern, password):
            return False, (
            "Password must be at least 8 characters long, include "
            "1 uppercase, 1 lowercase, and 1 special character (@#$%^&)"
        )

        if password != data.get("confirm_password"):
            return False, "Passwords do not match"
        



        return True, None
    

    @staticmethod
    def validate_google_login(data):
        if not data:
            return False, "Request body missing"
        
        if not data.get("id_token"):
            return False, "Google token missing"
        
        return True, None
    
    @staticmethod
    def validate_get_me(user_id):
        if not user_id:
            return False,"Invalid token or user identity missing"
        return True, None
    
    @staticmethod
    def validate_forgot_password(data):
        if not data:
            return False, "Request body missing"
        
        email = data.get("email")

        if not email:
            return False, "Email required"
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_pattern, email):
            return False, "Invalid email format"
        return True, None
    
    @staticmethod
    def validate_reset_password(data):

        if not data:
            return False, "Request body missing"

 
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return False, "Authorization header missing"

        if not auth_header.startswith("Bearer "):
            return False, "Invalid Authorization format"

        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if not new_password:
            return False, "New password required"

        if not confirm_password:
            return False, "Confirm password required"

        if new_password != confirm_password:
            return False, "Passwords do not match"

     
        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[@#$%^&]).{8,}$"

        if not re.match(password_pattern, new_password):
            return False, (
                "Password must be at least 8 characters long, include "
                "1 uppercase, 1 lowercase, and 1 special character (@#$%^&)"
            )

        return True, None

    
        

    
        

    
    


    

