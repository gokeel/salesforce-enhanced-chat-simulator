"""
Authentication Module

This module handles JWT generation and access token management
for Salesforce Enhanced Chat API authentication.
"""

import jwt
import uuid
import time
import requests
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


def load_private_key(private_key_path):
    """Load private key from file"""
    try:
        with open(private_key_path, 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        return private_key
    except FileNotFoundError:
        raise Exception(f"Private key not found at {private_key_path}. Please add your private key file.")
    except Exception as e:
        raise Exception(f"Error loading private key: {str(e)}")


def generate_jwt(scrt_url, kid, private_key_path, subject="user123"):
    """
    Generate JWT token for Salesforce authentication
    
    Args:
        scrt_url: Salesforce SCRT URL
        kid: Key ID for JWT header
        private_key_path: Path to private key file
        subject: Subject identifier (default: "user123")
        
    Returns:
        str: Generated JWT token
    """
    try:
        private_key = load_private_key(private_key_path)
        
        # Get private key in PEM format for PyJWT
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # JWT payload
        # Add buffer for clock skew between servers
        now = datetime.utcnow()
        iat_time = now - timedelta(seconds=60)  # Set issued time 60 seconds in the past
        exp_time = now + timedelta(minutes=5)   # Token valid for 5 minutes
        
        payload = {
            "sub": subject,  # Subject - user identifier
            "aud": scrt_url,   # Audience - SCRT URL (not Org ID)
            "iss": kid,  # Issuer - use KID as issuer
            "iat": int(iat_time.timestamp()),  # Issued at (in the past to handle clock skew)
            "nbf": int(iat_time.timestamp()),  # Not before (same as iat)
            "exp": int(exp_time.timestamp()),  # Expiration (5 minutes from now)
            "name": "Test User",  # User display name
        }
        
        print(f"JWT Payload: {payload}")
        print(f"IAT: {iat_time} | EXP: {exp_time}")
        
        # Generate JWT with kid in header
        token = jwt.encode(
            payload, 
            pem, 
            algorithm="RS256",
            headers={"kid": kid}  # Include Key ID in JWT header
        )
        return token
    except Exception as e:
        raise Exception(f"Error generating JWT: {str(e)}")


def generate_access_token(scrt_url, org_id, es_developer_name, kid, private_key_path, subject="user123"):
    """
    Generate Salesforce access token using JWT
    
    Args:
        scrt_url: Salesforce SCRT URL
        org_id: Salesforce Organization ID
        es_developer_name: Enhanced Service Developer Name
        kid: Key ID for JWT header
        private_key_path: Path to private key file
        subject: Subject identifier (default: "user123")
        
    Returns:
        tuple: (success bool, response dict, status code)
    """
    try:
        # Generate JWT
        customer_identity_token = generate_jwt(scrt_url, kid, private_key_path, subject)
        
        # Prepare request payload for Salesforce
        payload = {
            "orgId": org_id,
            "esDeveloperName": es_developer_name,
            "capabilitiesVersion": "1",
            "platform": "Web",
            "context": {
                "appName": "EnhancedChatSimulator",
                "clientVersion": "1.0"
            },
            "authorizationType": "JWT",
            "customerIdentityToken": customer_identity_token
        }
        
        # Call Salesforce API
        url = f"{scrt_url}/iamessage/api/v2/authorization/authenticated/access-token"
        headers = {
            "Content-Type": "application/json"
        }
        
        print(f"Calling Salesforce API: {url}")
        print(f"Payload: {payload}")
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            return True, {
                "success": True,
                "data": data,
                "jwt_generated": customer_identity_token[:50] + "..."
            }, 200
        else:
            return False, {
                "success": False,
                "error": f"API returned status {response.status_code}",
                "details": response.text
            }, response.status_code
            
    except Exception as e:
        return False, {
            "success": False,
            "error": str(e)
        }, 500


def validate_access_token(access_token):
    """
    Validate if access token exists
    
    Args:
        access_token: Token to validate
        
    Returns:
        tuple: (is_valid bool, error_message str or None)
    """
    if not access_token:
        return False, "No access token available. Please generate access token first."
    return True, None
