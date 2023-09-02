from passlib.context import CryptContext

# Create a CryptContext instance
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Your plain text password
plain_password = "Decrypt_me"

# Hash the password
hashed_password = pwd_context.hash(plain_password)

print("Hashed Password:", hashed_password)
