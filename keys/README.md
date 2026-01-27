# Private Key Storage

## Instruksi

Taruh private key Anda di folder ini dengan nama file:

```
private_key.pem
```

## Format

Private key harus dalam format PEM (Privacy-Enhanced Mail).

Contoh isi file:
```
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
...
-----END PRIVATE KEY-----
```

atau

```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
...
-----END RSA PRIVATE KEY-----
```

## Security Warning

⚠️ **PENTING**: Private key ini bersifat rahasia. Jangan pernah commit file ini ke Git atau share ke orang lain!
