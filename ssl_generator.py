import ssl
import secrets

context = ssl.create_default_context()

# Generate 32 random bytes
random_bytes = secrets.token_bytes(32)

# Convert the bytes to a hexadecimal string
hex_string = random_bytes.hex()

print(hex_string)