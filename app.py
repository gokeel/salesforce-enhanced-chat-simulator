from flask import Flask, render_template, request, jsonify
import uuid
import time
import os
import requests
import json
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import custom modules
from auth import generate_jwt, generate_access_token as generate_token_with_jwt, validate_access_token
from conversation_history import (
    generate_oauth_token as get_oauth_token,
    handle_send_conversation_history
)

app = Flask(__name__)

# Salesforce Configuration - Load from environment variables
SCRT_URL = os.getenv("SCRT_URL")
ORG_ID = os.getenv("ORG_ID")
ES_DEVELOPER_NAME = os.getenv("ES_DEVELOPER_NAME")
KID = os.getenv("KID")
PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH", "keys/private_key.key")
JWK_PATH = os.getenv("JWK_PATH", "keys/infobip-private.json")

# OAuth 2.0 Client Credentials (for Conversation History API)
OAUTH_TOKEN_URL = os.getenv("OAUTH_TOKEN_URL")
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")


# In-memory storage for access token (untuk development)
app_state = {
    "access_token": None,
    "last_event_id": None,
    "conversation_id": None,
    "channel_address_identifier": None
}


def load_private_key():
    """Load private key from file"""
    try:
        with open(PRIVATE_KEY_PATH, 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        return private_key
    except FileNotFoundError:
        raise Exception(f"Private key not found at {PRIVATE_KEY_PATH}. Please add your private key file.")
    except Exception as e:
        raise Exception(f"Error loading private key: {str(e)}")


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/generate-token', methods=['POST'])
def generate_access_token_endpoint():
    """Generate Salesforce access token using JWT"""
    try:
        # Call auth module function using JWK file
        success, response_data, status_code = generate_token_with_jwt(
            SCRT_URL, ORG_ID, ES_DEVELOPER_NAME, KID, jwk_path=JWK_PATH
        )
        
        if success:
            # Store access token for later use
            app_state["access_token"] = response_data.get("data", {}).get("accessToken")
            app_state["last_event_id"] = response_data.get("data", {}).get("lastEventId")
            return jsonify(response_data)
        else:
            return jsonify(response_data), status_code
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/generate-token-unauthenticated', methods=['POST'])
def generate_access_token_unauthenticated():
    """Generate Salesforce access token for unauthenticated users"""
    try:
        # Prepare request payload for Salesforce (unauthenticated flow)
        # Note: deviceId should be omitted for web apps
        payload = {
            "orgId": ORG_ID,
            "esDeveloperName": ES_DEVELOPER_NAME,
            "capabilitiesVersion": "1",
            "platform": "Web",
            "context": {
                "appName": "EnhancedChatSimulator",
                "clientVersion": "1.0"
            }
        }
        
        # Call Salesforce API (unauthenticated endpoint)
        url = f"{SCRT_URL}/iamessage/api/v2/authorization/unauthenticated/access-token"
        headers = {
            "Content-Type": "application/json"
        }
        
        print(f"Calling Salesforce API (Unauthenticated): {url}")
        print(f"Payload: {payload}")
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            # Store access token for later use
            app_state["access_token"] = data.get("accessToken")
            app_state["last_event_id"] = data.get("lastEventId")
            
            return jsonify({
                "success": True,
                "data": data
            })
        else:
            return jsonify({
                "success": False,
                "error": f"API returned status {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/create-conversation', methods=['POST'])
def create_conversation():
    """Create a new conversation"""
    try:
        # Check if we have an access token
        if not app_state["access_token"]:
            return jsonify({
                "success": False,
                "error": "No access token available. Please generate access token first."
            }), 400
        
        # Get optional parameters from request
        data = request.get_json() or {}
        language = data.get("language", "en_US")
        routing_attributes = data.get("routingAttributes", {})
        
        # Generate conversation ID
        conversation_id = str(uuid.uuid4())
        app_state["conversation_id"] = conversation_id
        
        # Prepare request payload
        payload = {
            "conversationId": conversation_id,
            "esDeveloperName": ES_DEVELOPER_NAME,
            "language": language
        }
        
        # Add routing attributes if provided
        if routing_attributes:
            payload["routingAttributes"] = routing_attributes
        
        # Call Salesforce API
        url = f"{SCRT_URL}/iamessage/api/v2/conversation"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {app_state['access_token']}"
        }
        
        print(f"Calling Salesforce API: {url}")
        print(f"Payload: {payload}")
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code in [200, 201]:
            # Extract channelAddressIdentifier from response if available
            try:
                response_data = response.json()
                if "channelAddressIdentifier" in response_data:
                    app_state["channel_address_identifier"] = response_data["channelAddressIdentifier"]
            except:
                pass
            
            return jsonify({
                "success": True,
                "conversationId": conversation_id,
                "message": "Conversation created successfully",
                "status_code": response.status_code,
                "response": response.text if response.text else "Created"
            })
        else:
            return jsonify({
                "success": False,
                "error": f"API returned status {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/send-typing-indicator', methods=['POST'])
def send_typing_indicator():
    """Send typing indicator to a conversation"""
    try:
        # Check if we have an access token
        if not app_state["access_token"]:
            return jsonify({
                "success": False,
                "error": "No access token available. Please generate access token first."
            }), 400
        
        # Check if we have a conversation ID
        if not app_state["conversation_id"]:
            return jsonify({
                "success": False,
                "error": "No conversation available. Please create a conversation first."
            }), 400
        
        # Get entry type from request
        data = request.get_json() or {}
        entry_type = data.get("entryType")
        
        # Validate entry type
        if entry_type not in ["TypingStartedIndicator", "TypingStoppedIndicator"]:
            return jsonify({
                "success": False,
                "error": "Invalid entryType. Must be 'TypingStartedIndicator' or 'TypingStoppedIndicator'."
            }), 400
        
        # Generate unique ID for this typing indicator event
        indicator_id = str(uuid.uuid4())
        
        # Prepare request payload
        payload = {
            "entryType": entry_type,
            "id": indicator_id
        }
        
        # Call Salesforce API (conversationId must be lowercase)
        conversation_id_lower = app_state["conversation_id"].lower()
        url = f"{SCRT_URL}/iamessage/api/v2/conversation/{conversation_id_lower}/entry"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {app_state['access_token']}"
        }
        
        print(f"Calling Salesforce API: {url}")
        print(f"Payload: {payload}")
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            return jsonify({
                "success": True,
                "message": f"Typing indicator sent: {entry_type}",
                "entryType": entry_type,
                "indicatorId": indicator_id
            })
        else:
            return jsonify({
                "success": False,
                "error": f"API returned status {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/send-message', methods=['POST'])
def send_message():
    """Send a text message to a conversation"""
    try:
        # Check if we have an access token
        if not app_state["access_token"]:
            return jsonify({
                "success": False,
                "error": "No access token available. Please generate access token first."
            }), 400
        
        # Check if we have a conversation ID
        if not app_state["conversation_id"]:
            return jsonify({
                "success": False,
                "error": "No conversation available. Please create a conversation first."
            }), 400
        
        # Get message text from request
        data = request.get_json() or {}
        message_text = data.get("text", "").strip()
        
        # Validate message is not empty
        if not message_text:
            return jsonify({
                "success": False,
                "error": "Message text cannot be empty."
            }), 400
        
        # Generate unique ID for this message
        message_id = str(uuid.uuid4())
        
        # Prepare request payload with StaticContentMessage
        payload = {
            "message": {
                "id": message_id,
                "messageType": "StaticContentMessage",
                "staticContent": {
                    "formatType": "Text",
                    "text": message_text
                }
            },
            "esDeveloperName": ES_DEVELOPER_NAME,
            "language": "en_US"
        }
        
        # Call Salesforce API (conversationId must be lowercase)
        conversation_id_lower = app_state["conversation_id"].lower()
        url = f"{SCRT_URL}/iamessage/api/v2/conversation/{conversation_id_lower}/message"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {app_state['access_token']}"
        }
        
        print(f"Calling Salesforce API: {url}")
        print(f"Payload: {payload}")
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 202:
            response_data = response.json() if response.text else {}
            return jsonify({
                "success": True,
                "message": "Message sent successfully",
                "messageId": message_id,
                "responseData": response_data
            })
        else:
            return jsonify({
                "success": False,
                "error": f"API returned status {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/send-file', methods=['POST'])
def send_file():
    """Send a file to a conversation"""
    try:
        # Check if we have an access token
        if not app_state["access_token"]:
            return jsonify({
                "success": False,
                "error": "No access token available. Please generate access token first."
            }), 400
        
        # Check if we have a conversation ID
        if not app_state["conversation_id"]:
            return jsonify({
                "success": False,
                "error": "No conversation available. Please create a conversation first."
            }), 400
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file uploaded."
            }), 400
        
        file = request.files['file']
        caption = request.form.get('caption', '')
        
        # Check if file is empty
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No file selected."
            }), 400
        
        # Read file data
        file_data = file.read()
        file_size = len(file_data)
        
        # Validate file size (max 5MB)
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                "success": False,
                "error": f"File too large. Maximum size is 5MB. Your file is {file_size / 1024 / 1024:.2f}MB."
            }), 400
        
        # Generate unique IDs
        message_id = str(uuid.uuid4())
        file_id = str(uuid.uuid4())
        
        # Prepare messageEntry JSON part
        message_entry = {
            "esDeveloperName": ES_DEVELOPER_NAME,
            "message": {
                "id": message_id,
                "fileId": file_id,
            },
            "language": "en_US"
        }
        
        # Add caption if provided
        if caption:
            message_entry["message"]["text"] = caption
        
        # Call Salesforce API (conversationId must be lowercase)
        conversation_id_lower = app_state["conversation_id"].lower()
        url = f"{SCRT_URL}/iamessage/api/v2/conversation/{conversation_id_lower}/file"
        
        headers = {
            "Authorization": f"Bearer {app_state['access_token']}"
        }
        
        # Prepare multipart form data
        # The requests library handles multipart/form-data automatically when using 'files' parameter
        files = {
            'messageEntry': (None, json.dumps(message_entry), 'application/json'),
            'fileData': (file.filename, file_data, file.content_type or 'application/octet-stream')
        }
        
        print(f"Calling Salesforce API: {url}")
        print(f"Message Entry: {message_entry}")
        print(f"File: {file.filename}, Size: {file_size} bytes, Type: {file.content_type}")
        
        response = requests.post(url, headers=headers, files=files)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 202:
            response_data = response.json() if response.text else {}
            return jsonify({
                "success": True,
                "message": "File sent successfully",
                "messageId": message_id,
                "fileId": file_id,
                "filename": file.filename,
                "fileSize": file_size,
                "responseData": response_data
            })
        else:
            return jsonify({
                "success": False,
                "error": f"API returned status {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/close-conversation', methods=['POST'])
def close_conversation():
    """Close a conversation permanently"""
    try:
        # Check if we have an access token
        if not app_state["access_token"]:
            return jsonify({
                "success": False,
                "error": "No access token available. Please generate access token first."
            }), 400
        
        # Check if we have a conversation ID
        if not app_state["conversation_id"]:
            return jsonify({
                "success": False,
                "error": "No conversation available. Please create a conversation first."
            }), 400
        
        # Call Salesforce API (conversationId must be lowercase)
        conversation_id_lower = app_state["conversation_id"].lower()
        url = f"{SCRT_URL}/iamessage/api/v2/conversation/{conversation_id_lower}?esDeveloperName={ES_DEVELOPER_NAME}"
        headers = {
            "Authorization": f"Bearer {app_state['access_token']}"
        }
        
        print(f"Calling Salesforce API: {url}")
        
        response = requests.delete(url, headers=headers)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 204:
            # Clear conversation state since conversation is closed
            app_state["conversation_id"] = None
            return jsonify({
                "success": True,
                "message": "Conversation closed successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": f"API returned status {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/end-session', methods=['POST'])
def end_messaging_session():
    """End the current messaging session (conversation remains open)"""
    try:
        # Check if we have an access token
        if not app_state["access_token"]:
            return jsonify({
                "success": False,
                "error": "No access token available. Please generate access token first."
            }), 400
        
        # Check if we have a conversation ID
        if not app_state["conversation_id"]:
            return jsonify({
                "success": False,
                "error": "No conversation available. Please create a conversation first."
            }), 400
        
        # Call Salesforce API (conversationId must be lowercase)
        conversation_id_lower = app_state["conversation_id"].lower()
        url = f"{SCRT_URL}/iamessage/api/v2/conversation/{conversation_id_lower}/session?esDeveloperName={ES_DEVELOPER_NAME}"
        headers = {
            "Authorization": f"Bearer {app_state['access_token']}"
        }
        
        print(f"Calling Salesforce API: {url}")
        
        response = requests.delete(url, headers=headers)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 204:
            # Keep conversation state since conversation is still open
            return jsonify({
                "success": True,
                "message": "Messaging session ended successfully. Conversation remains open."
            })
        else:
            return jsonify({
                "success": False,
                "error": f"API returned status {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/list-conversations', methods=['GET'])
def list_conversations():
    """List all conversations for the current user"""
    try:
        # Check if we have an access token
        if not app_state["access_token"]:
            return jsonify({
                "success": False,
                "error": "No access token available. Please generate access token first."
            }), 400
        
        # Get query parameters
        incl_closed = request.args.get('inclClosedConvs', 'false').lower() == 'true'
        limit = request.args.get('limit', '20')
        
        # Call Salesforce API
        url = f"{SCRT_URL}/iamessage/api/v2/conversation/list"
        params = {
            'inclClosedConvs': str(incl_closed).lower(),
            'limit': limit
        }
        headers = {
            "Authorization": f"Bearer {app_state['access_token']}"
        }
        
        print(f"Calling Salesforce API: {url}")
        print(f"Params: {params}")
        
        response = requests.get(url, headers=headers, params=params)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                "success": True,
                "data": data
            })
        else:
            return jsonify({
                "success": False,
                "error": f"API returned status {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/list-conversation-entries/<conversation_id>', methods=['GET'])
def list_conversation_entries(conversation_id):
    """List entries for a specific conversation"""
    try:
        # Check if we have an access token
        if not app_state["access_token"]:
            return jsonify({
                "success": False,
                "error": "No access token available. Please generate access token first."
            }), 400
        
        # Get query parameters
        limit = request.args.get('limit', '20')
        direction = request.args.get('direction', 'FromEnd')
        
        # Call Salesforce API (conversationId must be lowercase)
        conversation_id_lower = conversation_id.lower()
        url = f"{SCRT_URL}/iamessage/api/v2/conversation/{conversation_id_lower}/entries"
        params = {
            'limit': limit,
            'direction': direction
        }
        headers = {
            "Authorization": f"Bearer {app_state['access_token']}"
        }
        
        print(f"Calling Salesforce API: {url}")
        print(f"Params: {params}")
        
        response = requests.get(url, headers=headers, params=params)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                "success": True,
                "data": data
            })
        else:
            return jsonify({
                "success": False,
                "error": f"API returned status {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/sse-config', methods=['GET'])
def get_sse_config():
    """Get SSE connection configuration"""
    try:
        # Check if we have an access token
        if not app_state["access_token"]:
            return jsonify({
                "success": False,
                "error": "No access token available. Please generate access token first."
            }), 400
        
        # Check if we have a conversation ID
        if not app_state["conversation_id"]:
            return jsonify({
                "success": False,
                "error": "No conversation available. Please create a conversation first."
            }), 400
        
        # Prepare SSE configuration
        sse_url = f"{SCRT_URL}/eventrouter/v1/sse"
        conversation_id_lower = app_state["conversation_id"].lower()
        
        # Use channel_address_identifier if available, otherwise use conversation_id
        channel_address = app_state.get("channel_address_identifier") or conversation_id_lower
        
        config = {
            "success": True,
            "sse_url": sse_url,
            "access_token": app_state["access_token"],
            "org_id": ORG_ID,
            "query_params": {
                "channelType": "embedded_messaging",
                "channelAddressIdentifier": channel_address,
                "conversationId": conversation_id_lower,
                "channelPlatformKey": "web-simulator"  # Can be any identifier
            }
        }
        
        return jsonify(config)
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/generate-oauth-token', methods=['POST'])
def generate_oauth_token_endpoint():
    """Generate OAuth 2.0 access token using Client Credentials flow"""
    oauth_config = {
        'token_url': OAUTH_TOKEN_URL,
        'client_id': OAUTH_CLIENT_ID,
        'client_secret': OAUTH_CLIENT_SECRET
    }
    
    result = get_oauth_token(oauth_config)
    
    if isinstance(result, tuple):
        # Error case
        return jsonify(result[0]), result[1]
    else:
        # Success case
        return jsonify(result)


@app.route('/api/send-conversation-history', methods=['POST'])
def send_conversation_history_endpoint():
    """Send chatbot conversation history to Enhanced Chat"""
    response_data, status_code = handle_send_conversation_history(
        request, app_state, SCRT_URL, ORG_ID, ES_DEVELOPER_NAME
    )
    return jsonify(response_data), status_code


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current application state"""
    return jsonify({
        "has_access_token": app_state["access_token"] is not None,
        "has_conversation": app_state["conversation_id"] is not None,
        "conversation_id": app_state["conversation_id"]
    })


@app.route('/api/load-dummy-conversation', methods=['GET'])
def load_dummy_conversation():
    """Load dummy IM3 conversation for testing"""
    try:
        # Read dummy conversation file
        with open('dummy_im3_network_conversation.json', 'r', encoding='utf-8') as f:
            conversation_data = json.load(f)
        
        return jsonify({
            "success": True,
            "conversation": conversation_data
        })
    except FileNotFoundError:
        return jsonify({
            "success": False,
            "error": "Dummy conversation file not found"
        }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/history')
def history_page():
    """Serve the chatbot history page with OAuth auth"""
    return render_template('history.html')


@app.route('/conversations')
def conversations_page():
    """Serve the conversations viewer page"""
    return render_template('conversations.html')


if __name__ == '__main__':
    print("=" * 60)
    print("Salesforce Enhanced Chat API Simulator")
    print("=" * 60)
    print(f"SCRT URL: {SCRT_URL}")
    print(f"Org ID: {ORG_ID}")
    print(f"ES Developer Name: {ES_DEVELOPER_NAME}")
    print(f"Private Key: {PRIVATE_KEY_PATH}")
    print("=" * 60)
    print("\nStarting server on http://localhost:5001")
    print("\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
