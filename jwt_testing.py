import jwt

# Encode (Create a JWT)
payload = {'user_id': 123}
secret_key = 'your-secret-key'
token = jwt.encode(payload, secret_key, algorithm='HS256')

# Decode (Verify and decode a JWT)
try:
    decoded_payload = jwt.decode(token, secret_key, algorithms=['HS256'])
    # Access the decoded payload
    print(decoded_payload)
except jwt.ExpiredSignatureError:
    # Token has expired
    print("Token has expired.")
except jwt.DecodeError:
    # Token is invalid or has tampered data
    print("Token is invalid.")
