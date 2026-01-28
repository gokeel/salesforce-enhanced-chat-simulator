"""
Conversation History Module - OAuth Client Credentials Version

This module handles sending chatbot conversation history to Salesforce Enhanced Chat
using OAuth 2.0 Client Credentials authentication and the Interaction Service API.
"""

import uuid
import time
import json
import requests


def generate_oauth_token(oauth_config):
    """
    Generate OAuth 2.0 access token using Client Credentials flow
    
    Args:
        oauth_config: Dictionary with token_url, client_id, client_secret
        
    Returns:
        dict: Response with success status and token data
    """
    try:
        # Prepare request data (form-urlencoded format)
        data = {
            'grant_type': 'client_credentials',
            'client_id': oauth_config['client_id'],
            'client_secret': oauth_config['client_secret']
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        print(f"Requesting OAuth token from: {oauth_config['token_url']}")
        print(f"Client ID: {oauth_config['client_id'][:20]}...")
        
        # Request token
        response = requests.post(oauth_config['token_url'], data=data, headers=headers)
        
        print(f"OAuth Response Status: {response.status_code}")
        print(f"OAuth Response Body: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            return {
                'success': True,
                'access_token': token_data.get('access_token'),
                'token_type': token_data.get('token_type', 'Bearer'),
                'instance_url': token_data.get('instance_url'),
                'scope': token_data.get('scope', '')
            }
        else:
            return {
                'success': False,
                'error': f'OAuth failed with status {response.status_code}',
                'details': response.text
            }, response.status_code
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }, 500


def establish_conversation(access_token, channel_address, participants, org_id, es_developer_name, scrt_url):
    """
    Establish a conversation with Interaction Service API
    
    Args:
        access_token: OAuth access token
        channel_address: Channel address identifier
        participants: List of participant objects
        org_id: Organization ID
        es_developer_name: ES Developer Name
        scrt_url: Salesforce SCRT URL
        
    Returns:
        tuple: (success bool, conversationIdentifier, messagingSessionId, error message)
    """
    try:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Call Salesforce establish conversation API
        url = f"{scrt_url}/api/v1/conversation"
        
        # Build participants for establish conversation
        conversation_participants = []
        for p in participants:
            role = p.get("role", "EndUser")
            # Use custom appType for all participants in establish conversation
            app_type = p.get("appType", "custom")
            
            conversation_participants.append({
                "subject": p.get("subject", ""),
                "role": role,
                "appType": app_type
            })
        
        payload = {
            "channelAddressIdentifier": channel_address,
            "participants": conversation_participants
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "OrgId": org_id,
            "RequestId": request_id,
            "AuthorizationContext": "Infobip_Chatbot"
        }
        
        print(f"Establishing conversation at: {url}")
        print(f"Headers: {headers}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Establish Conversation Response Status: {response.status_code}")
        print(f"Establish Conversation Response Body: {response.text}")
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            conversation_identifier = response_data.get("conversationIdentifier")
            messaging_session_id = response_data.get("messagingSessionId")
            
            return True, conversation_identifier, messaging_session_id, None
        else:
            return False, None, None, f"Establish conversation failed with status {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, None, None, str(e)


def transform_conversation_to_salesforce_format(data, scrt_url, org_id, es_developer_name, app_state):
    """
    Transform simple conversation format to Salesforce API format
    
    Args:
        data: Conversation data with participants and messages
        scrt_url: Salesforce SCRT URL
        org_id: Organization ID
        es_developer_name: ES Developer Name
        app_state: Application state dict
        
    Returns:
        tuple: (payload dict, error message or None)
    """
    try:
        # Get channel address
        # When using OAuth flow, conversation_id might be None
        channel_address = app_state.get("channel_address_identifier")
        if not channel_address:
            conversation_id = app_state.get("conversation_id")
            if conversation_id:
                channel_address = conversation_id.lower()
            else:
                # Generate a random channel address for OAuth flow
                channel_address = f"{uuid.uuid4()}"
        
        # Build participants
        participants_data = data.get("participants", [])
        conversation_participants = []
        for p in participants_data:
            role = p.get("role", "EndUser")
            # Set appType to iamessage for EndUser, custom for others
            app_type = "iamessage" if role == "EndUser" else p.get("appType", "custom")
            
            conversation_participants.append({
                "displayName": p.get("displayName", "Unknown"),
                "participant": {
                    "subject": p.get("subject", ""),
                    "role": role,
                    "appType": app_type
                },
                "joinedTime": str(int(time.time() * 1000))  # Use current timestamp
            })
        
        # Build conversation entries (reverse order - newest first)
        messages = data.get("messages", [])
        conversation_entries = []
        
        # Take only first 5 messages (API limit)
        messages_to_send = messages[:5]
        
        # Reverse order for API (newest first)
        messages_to_send.reverse()
        
        # Use current timestamp for all messages to avoid validation errors
        current_timestamp = int(time.time() * 1000)
        
        for msg in messages_to_send:
            # Determine sender
            sender_role = "EndUser"
            sender_subject = ""
            sender_app_type = "custom"
            
            if msg.get("sender") == "bot":
                sender_role = "Chatbot"
                # Find chatbot participant
                for p in participants_data:
                    if p.get("role") == "Chatbot":
                        sender_subject = p.get("subject", "")
                        sender_app_type = p.get("appType", "custom")
                        break
            else:
                # Find user participant - set appType to iamessage for EndUser
                sender_app_type = "iamessage"
                for p in participants_data:
                    if p.get("role") == "EndUser":
                        sender_subject = p.get("subject", "")
                        break
            
            # Generate unique message ID
            msg_id = str(uuid.uuid4())
            
            entry = {
                "clientTimestamp": str(current_timestamp),  # Use current timestamp to avoid validation errors
                "entryPayload": {
                    "entryType": "Message",
                    "id": msg_id,
                    "abstractMessage": {
                        "messageType": "StaticContentMessage",
                        "id": msg_id,
                        "staticContent": {
                            "formatType": "Text",
                            "text": msg.get("text", "")
                        }
                    }
                },
                "sender": {
                    "subject": sender_subject,
                    "role": sender_role,
                    "appType": sender_app_type
                }
            }
            conversation_entries.append(entry)
        
        # Build messaging session
        current_time = int(time.time() * 1000)  # Use current timestamp
        messaging_session = {
            "messagingSessionRequestType": "EstablishMessagingSession",
            "payload": {
                "startTime": str(current_time)
            }
        }
        
        # Build final payload
        payload = {
            "channelAddressIdentifier": channel_address,
            "conversationParticipants": conversation_participants,
            "conversationEntries": conversation_entries,
            "messagingSession": messaging_session
        }
        
        return payload, None
        
    except Exception as e:
        return None, str(e)


def send_history_to_salesforce(payload, access_token, scrt_url, org_id, es_developer_name):
    """
    Send conversation history to Salesforce API
    
    Args:
        payload: Formatted conversation history payload
        access_token: OAuth access token
        scrt_url: Salesforce SCRT URL
        org_id: Organization ID
        es_developer_name: ES Developer Name
        
    Returns:
        tuple: (success bool, response data dict, status code)
    """
    try:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Call Salesforce API
        url = f"{scrt_url}/api/v1/conversationHistory"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "OrgId": org_id,
            "AuthorizationContext": "Infobip_Chatbot",
            "AuthorizationContextType": "EmbeddedMessagingChannel",
            "RequestId": request_id
        }
        
        print(f"Calling Salesforce API: {url}")
        print(f"Headers: {headers}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            return True, {
                "success": True,
                "messagingSessionId": response_data.get("messagingSessionId"),
                "message": f"Successfully sent {len(payload['conversationEntries'])} conversation entries",
                "entriesSent": len(payload['conversationEntries']),
                "response": response_data
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


def handle_send_conversation_history(request_obj, app_state, scrt_url, org_id, es_developer_name):
    """
    Main handler for sending conversation history
    Combines OAuth token checking, establish conversation, data transformation, and API call
    
    Args:
        request_obj: Flask request object
        app_state: Application state dict
        scrt_url: Salesforce SCRT URL
        org_id: Organization ID
        es_developer_name: ES Developer Name
        
    Returns:
        tuple: (response dict, status code)
    """
    # Check for OAuth token in custom header (from history page)
    oauth_token = request_obj.headers.get('X-OAuth-Token')
    
    # Fallback to app_state token if no OAuth token provided (backward compatibility)
    if not oauth_token:
        if not app_state.get("access_token"):
            return {
                "success": False,
                "error": "No access token available. Please generate access token first."
            }, 400
        access_token = app_state["access_token"]
    else:
        access_token = oauth_token
    
    # For conversation ID, we can make it optional when using OAuth
    conversation_id = app_state.get("conversation_id")
    if not conversation_id and not oauth_token:
        return {
            "success": False,
            "error": "No conversation available. Please create a conversation first."
        }, 400
    
    # Get request data
    data = request_obj.get_json()
    if not data:
        return {
            "success": False,
            "error": "No conversation history data provided"
        }, 400
    
    # Extract participants and channel address for establishing conversation
    participants_data = data.get("participants", [])
    if not participants_data:
        return {
            "success": False,
            "error": "No participants provided in conversation data"
        }, 400
    
    # Get or generate channel address
    channel_address = app_state.get("channel_address_identifier")
    if not channel_address:
        conversation_id = app_state.get("conversation_id")
        if conversation_id:
            channel_address = conversation_id.lower()
        else:
            # Generate a random channel address for OAuth flow
            channel_address = f"{uuid.uuid4()}"
    
    print(f"📍 Using channelAddressIdentifier: {channel_address}")
    print(f"   - From app_state['channel_address_identifier']: {app_state.get('channel_address_identifier')}")
    print(f"   - From app_state['conversation_id']: {app_state.get('conversation_id')}")
    
    
    # STEP 1: Establish conversation first
    print("=" * 60)
    print("STEP 1: Establishing conversation...")
    print("=" * 60)
    
    success_establish, conversation_identifier, messaging_session_id, error = establish_conversation(
        access_token, channel_address, participants_data, org_id, es_developer_name, scrt_url
    )
    
    if not success_establish:
        return {
            "success": False,
            "error": f"Failed to establish conversation: {error}"
        }, 400
    
    print(f"✓ Conversation established successfully!")
    print(f"  - conversationIdentifier: {conversation_identifier}")
    print(f"  - messagingSessionId: {messaging_session_id}")
    
    # STEP 2: Transform data to Salesforce format
    print("=" * 60)
    print("STEP 2: Transforming conversation data...")
    print("=" * 60)
    
    payload, error = transform_conversation_to_salesforce_format(
        data, scrt_url, org_id, es_developer_name, app_state
    )
    
    if error:
        return {
            "success": False,
            "error": f"Failed to transform data: {error}"
        }, 400
    
    # STEP 3: Send conversation history to Salesforce
    print("=" * 60)
    print("STEP 3: Sending conversation history...")
    print("=" * 60)
    
    success, response_data, status_code = send_history_to_salesforce(
        payload, access_token, scrt_url, org_id, es_developer_name
    )
    
    # Add conversation IDs to response
    if success and response_data.get("success"):
        response_data["conversationIdentifier"] = conversation_identifier
        response_data["establishedMessagingSessionId"] = messaging_session_id
    
    return response_data, status_code
