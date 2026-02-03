# Salesforce Enhanced Chat API Simulator

Aplikasi simulasi untuk testing Salesforce Enhanced Chat API dengan Python Flask.

## Features

- ✅ Generate Access Token menggunakan JWT authentication
- ✅ Create Conversation dengan Salesforce Enhanced Chat API
- ✅ Simple web interface untuk testing
- ✅ Real-time response display

## Configuration

This application uses environment variables for secure configuration. All sensitive credentials are stored in a `.env` file.

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the `.env.example` file to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Salesforce credentials:

```env
# Salesforce Configuration
SCRT_URL=https://your-domain.salesforce-scrt.com
ORG_ID=your_org_id
ES_DEVELOPER_NAME=your_es_developer_name
KID=your_key_id
PRIVATE_KEY_PATH=keys/private_key.key

# OAuth 2.0 Client Credentials (for Conversation History API)
OAUTH_TOKEN_URL=https://your-domain.salesforce.com/services/oauth2/token
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret
```

⚠️ **IMPORTANT**: The `.env` file contains sensitive credentials and is already in `.gitignore`. Never commit this file to Git!

### 3. Add Private Key

Taruh private key Anda di folder `keys/` dengan nama file `private_key.key` (atau sesuai dengan `PRIVATE_KEY_PATH` di `.env`):

```
keys/private_key.key
```

Private key harus dalam format PEM. Contoh:

```
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
...
-----END PRIVATE KEY-----
```

### 3. Run the Application

```bash
python app.py
```

Server akan berjalan di: **http://localhost:5000**

## Usage

### Step 1: Generate Access Token

1. Buka browser ke `http://localhost:5000`
2. Klik tombol **"Generate Access Token"**
3. Access token akan ditampilkan di response area
4. Token ini akan disimpan di server untuk digunakan di step berikutnya

### Step 2: Create Conversation

1. Setelah mendapatkan access token, tombol **"Create Conversation"** akan aktif
2. Klik tombol tersebut untuk membuat conversation baru
3. Conversation ID dan response akan ditampilkan

## API Endpoints

### POST /api/generate-token

Generate Salesforce access token menggunakan JWT.

**Response:**
```json
{
  "success": true,
  "data": {
    "accessToken": "...",
    "lastEventId": "..."
  },
  "jwt_generated": "..."
}
```

### POST /api/create-conversation

Create new conversation (memerlukan access token dari step sebelumnya).

**Request Body (optional):**
```json
{
  "language": "en_US"
}
```

**Response:**
```json
{
  "success": true,
  "conversationId": "...",
  "message": "Conversation created successfully"
}
```

### GET /api/status

Get current application state.

**Response:**
```json
{
  "has_access_token": true,
  "has_conversation": true,
  "conversation_id": "..."
}
```

## Project Structure

```
salesforce-enhanced-chat-simulator/
├── app.py                  # Main Flask application
├── auth.py                 # Authentication module
├── conversation_history.py # Conversation history module
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (NOT in git)
├── .env.example            # Environment variables template
├── keys/
│   ├── README.md          # Instructions for private key
│   └── private_key.key    # Your private key (not in git)
├── templates/
│   └── index.html         # Web interface
├── .gitignore
└── README.md
```

## Security Notes

⚠️ **IMPORTANT**: 
- `.env` file contains all sensitive credentials and is in `.gitignore`
- `keys/private_key.pem` (or `private_key.key`) is also in `.gitignore`
- Never commit `.env` or private keys to Git
- The `.env.example` file is provided as a template (safe to commit)
- Aplikasi ini untuk development/testing only
- Tidak ada authentication layer karena hanya untuk local testing

## Troubleshooting

### Error: Private key not found

Pastikan Anda sudah menaruh private key di `keys/private_key.pem`

### Error: Invalid private key format

Pastikan format private key adalah PEM (dimulai dengan `-----BEGIN PRIVATE KEY-----` atau `-----BEGIN RSA PRIVATE KEY-----`)

### API Error Responses

Check console output (`python app.py`) untuk melihat detail request dan response dari Salesforce API.
