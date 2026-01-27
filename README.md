# Salesforce Enhanced Chat API Simulator

Aplikasi simulasi untuk testing Salesforce Enhanced Chat API dengan Python Flask.

## Features

- ✅ Generate Access Token menggunakan JWT authentication
- ✅ Create Conversation dengan Salesforce Enhanced Chat API
- ✅ Simple web interface untuk testing
- ✅ Real-time response display

## Configuration

Aplikasi ini sudah dikonfigurasi dengan:
- **SCRT URL**: `https://indosat--miawdev.sandbox.my.salesforce-scrt.com`
- **Org ID**: `00DMR000001JY5Z`
- **ES Developer Name**: `Chatbot_Channel`

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Add Private Key

Taruh private key Anda di folder `keys/` dengan nama file `private_key.pem`:

```
keys/private_key.pem
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
├── requirements.txt        # Python dependencies
├── keys/
│   ├── README.md          # Instructions for private key
│   └── private_key.pem    # Your private key (not in git)
├── templates/
│   └── index.html         # Web interface
├── .gitignore
└── README.md
```

## Security Notes

⚠️ **IMPORTANT**: 
- `keys/private_key.pem` sudah ada di `.gitignore`
- Jangan pernah commit private key ke Git
- Aplikasi ini untuk development/testing only
- Tidak ada authentication layer karena hanya untuk local testing

## Troubleshooting

### Error: Private key not found

Pastikan Anda sudah menaruh private key di `keys/private_key.pem`

### Error: Invalid private key format

Pastikan format private key adalah PEM (dimulai dengan `-----BEGIN PRIVATE KEY-----` atau `-----BEGIN RSA PRIVATE KEY-----`)

### API Error Responses

Check console output (`python app.py`) untuk melihat detail request dan response dari Salesforce API.
