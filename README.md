# Salesforce Enhanced Chat API Simulator

Aplikasi simulasi untuk testing Salesforce Enhanced Chat API dengan Python Flask.

## Features

- ✅ Generate Access Token menggunakan JWT authentication dengan JWK (JSON Web Key)
- ✅ Create Conversation dengan Salesforce Enhanced Chat API
- ✅ Send messages, files, dan typing indicators
- ✅ SSE (Server-Sent Events) untuk real-time updates
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
JWK_PATH=keys/infobip-private.json

# OAuth 2.0 Client Credentials (for Conversation History API)
OAUTH_TOKEN_URL=https://your-domain.salesforce.com/services/oauth2/token
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret
```

⚠️ **IMPORTANT**: The `.env` file contains sensitive credentials and is already in `.gitignore`. Never commit this file to Git!

### 3. Add JWK Private Key

Taruh JWK (JSON Web Key) private key Anda di folder `keys/`:

```
keys/infobip-private.json
```

Format JWK contoh:

```json
{
  "kty": "RSA",
  "kid": "your-key-id",
  "n": "...",
  "e": "AQAB",
  "d": "...",
  "p": "...",
  "q": "...",
  "dp": "...",
  "dq": "...",
  "qi": "...",
  "use": "sig"
}
```

⚠️ **PENTING**: 
- File JWK harus berisi private key dalam format JSON
- `kid` di dalam JWK harus sama dengan `KID` di `.env`
- Pastikan semua field required (`kty`, `n`, `e`, `d`, `p`, `q`, `dp`, `dq`, `qi`) ada

### 3. Run the Application

```bash
python app.py
```

Server akan berjalan di: **http://localhost:5001**

## Usage

### Step 1: Generate Access Token

1. Buka browser ke `http://localhost:5001`
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
├── app.py                     # Main Flask application
├── auth.py                    # Authentication module (JWK only)
├── conversation_history.py    # Conversation history module
├── test_jwt.py               # JWT testing utility
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (NOT in git)
├── .env.example               # Environment variables template
├── keys/
│   ├── README.md             # Instructions for JWK file
│   └── infobip-private.json  # JWK private key (not in git)
├── templates/
│   └── index.html            # Web interface
├── .gitignore
└── README.md
```

## Security Notes

⚠️ **IMPORTANT**: 
- `.env` file contains all sensitive credentials and is in `.gitignore`
- `keys/infobip-private.json` (JWK file) is also in `.gitignore`
- Never commit `.env` or JWK private keys to Git
- The `.env.example` file is provided as a template (safe to commit)
- Aplikasi ini untuk development/testing only
- Tidak ada authentication layer karena hanya untuk local testing

## Troubleshooting

### Error: JWK file not found

Pastikan Anda sudah menaruh JWK private key di `keys/infobip-private.json` (atau sesuai `JWK_PATH` di `.env`)

### Error: Invalid JWK format

Pastikan file JWK adalah valid JSON dengan field yang diperlukan: `kty`, `n`, `e`, `d`, `p`, `q`, `dp`, `dq`, `qi`

### Error: The customer identity token or JWT expired

Jika Anda mendapat error ini, kemungkinan penyebabnya:
1. **Clock skew**: Waktu sistem Anda berbeda dengan waktu server Salesforce (seharusnya sudah di-handle)
2. **Key ID mismatch**: Pastikan `KID` di `.env` sesuai dengan `kid` di JWK file
3. **Invalid signature**: Pastikan JWK private key yang digunakan sesuai dengan public key yang ter-register di Salesforce

### Testing JWT Generation

Untuk debug JWT, jalankan:

```bash
python3 test_jwt.py
```

Script ini akan menampilkan JWT payload dan timestamp analysis untuk membantu troubleshooting.

### API Error Responses

Check console output (`python app.py`) untuk melihat detail request dan response dari Salesforce API.
