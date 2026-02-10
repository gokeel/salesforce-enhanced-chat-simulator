"""
Authentication Module

This module handles JWT generation and access token management
for Salesforce Enhanced Chat API authentication.
"""

import jwt
import uuid
import time
import json
import requests
from datetime import datetime, timedelta
from jwt.algorithms import RSAAlgorithm


def load_private_key_from_jwk(jwk_path):
    """Load private key from JWK JSON file"""
    try:
        with open(jwk_path, 'r') as f:
            jwk_data = json.load(f)
        
        # Convert JWK to private key object using PyJWT's RSAAlgorithm
        private_key = RSAAlgorithm.from_jwk(json.dumps(jwk_data))
        
        return private_key
    except FileNotFoundError:
        raise Exception(f"JWK file not found at {jwk_path}. Please add your JWK file.")
    except Exception as e:
        raise Exception(f"Error loading JWK: {str(e)}")


def generate_jwt(scrt_url, kid, jwk_path, subject="user123"):
    """
    Generate JWT token for Salesforce authentication using JWK
    
    Args:
        scrt_url: Salesforce SCRT URL
        kid: Key ID for JWT header
        jwk_path: Path to JWK file (JSON format)
        subject: Subject identifier (default: "user123")
        
    Returns:
        str: Generated JWT token
    """
    try:
        # Load private key from JWK
        private_key = load_private_key_from_jwk(jwk_path)
        
        # JWT payload
        # Use current time for timestamps
        now = datetime.utcnow()
        current_timestamp = int(time.time())
        
        # Set IAT (issued at) to current time
        iat_timestamp = current_timestamp
        
        # Set EXP (expiration) to 5 minutes from now
        exp_timestamp = current_timestamp + 300
        
        payload = {
            "sub": subject,  # Subject - user identifier
            "aud": scrt_url,   # Audience - SCRT URL (not Org ID)
            "iss": kid,  # Issuer - use KID as issuer
            "iat": iat_timestamp,  # Issued at
            "nbf": iat_timestamp,  # Not before (same as iat)
            "exp": exp_timestamp,  # Expiration
            "name": "Test User",  # User display name
        }
        
        print(f"Current time: {now}")
        print(f"JWT Payload: {payload}")
        
        # Generate JWT with kid in header
        token = jwt.encode(
            payload, 
            private_key, 
            algorithm="RS256",
            headers={"kid": kid}  # Include Key ID in JWT header
        )
        return token
    except Exception as e:
        raise Exception(f"Error generating JWT: {str(e)}")


def generate_access_token(scrt_url, org_id, es_developer_name, kid, jwk_path, subject="user123"):
    """
    Generate Salesforce access token using JWT with JWK
    
    Args:
        scrt_url: Salesforce SCRT URL
        org_id: Salesforce Organization ID
        es_developer_name: Enhanced Service Developer Name
        kid: Key ID for JWT header
        jwk_path: Path to JWK file (JSON format)
        subject: Subject identifier (default: "user123")
        
    Returns:
        tuple: (success bool, response dict, status code)
    """
    try:
        # Generate JWT
        customer_identity_token = generate_jwt(scrt_url, kid, jwk_path, subject=subject)
        
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
