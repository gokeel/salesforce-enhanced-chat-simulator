#!/usr/bin/env python3
"""
Test script to decode and inspect the generated JWT
"""
import sys
sys.path.insert(0, '.')

from auth import generate_jwt
from dotenv import load_dotenv
import os
import jwt
import json

load_dotenv()

SCRT_URL = os.getenv("SCRT_URL")
KID = os.getenv("KID")
JWK_PATH = os.getenv("JWK_PATH", "keys/infobip-private.json")

print("=" * 60)
print("Testing JWT Generation and Decoding")
print("=" * 60)

# Generate JWT
try:
    token = generate_jwt(SCRT_URL, KID, jwk_path=JWK_PATH, subject="test_user")
    print(f"\n✅ JWT Generated successfully!")
    print(f"Token (first 100 chars): {token[:100]}...")
    
    # Decode without verification to inspect payload
    decoded = jwt.decode(token, options={"verify_signature": False})
    print(f"\n📋 JWT Payload:")
    print(json.dumps(decoded, indent=2))
    
    # Check timestamps
    import time
    current_time = int(time.time())
    
    print(f"\n⏰ Timestamp Analysis:")
    print(f"Current system timestamp: {current_time}")
    print(f"JWT iat (issued at):      {decoded.get('iat')}")
    print(f"JWT nbf (not before):     {decoded.get('nbf')}")
    print(f"JWT exp (expires):        {decoded.get('exp')}")
    
    iat_diff = current_time - decoded.get('iat', 0)
    exp_diff = decoded.get('exp', 0) - current_time
    
    print(f"\nTime differences:")
    print(f"Token was issued {iat_diff} seconds ago (should be small positive number)")
    print(f"Token expires in {exp_diff} seconds (should be ~300 seconds)")
    
    if iat_diff < -60:
        print("⚠️  WARNING: Token issued in the future! Clock skew issue.")
    elif iat_diff > 600:
        print("⚠️  WARNING: Token issued too long ago!")
    else:
        print("✅ IAT timestamp looks good")
    
    if exp_diff < 0:
        print("❌ ERROR: Token already expired!")
    elif exp_diff < 60:
        print("⚠️  WARNING: Token expires very soon!")
    else:
        print("✅ EXP timestamp looks good")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
