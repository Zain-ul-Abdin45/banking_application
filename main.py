from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import uvicorn, os
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import List, Optional
import logging #, logging.config

# Configuration
SECRET_KEY = "8f8855f27b2188b9d84b29f71b3ee58538ea1e4ca251a5bcebbf448ad736e033"  # Replace with your actual secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# log_folder = 'log'
# os.makedirs(log_folder, exist_ok=True)
# logging.config.fileConfig('logs/logger.ini')

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
# In-memory data storage
users_db = {
    "user1": {
        "username": "user1",
        "password": "$2b$12$iQEGRLyU1/UdhiQphwRMLuRpzPzbtI/zRQ8LCf5MhLjdE1/dgJ38q",  # Replace with the hashed password
    },
    "user2": {
        "username": "user2",
        "password": "$2b$12$4s1uThjyfzEBYQJzufyRjuYahonvWklPOQHCOOovssC.DW9GfsF2C",  # Replace with the hashed password
    },
}
transactions_db = []
app = FastAPI()


sample_transactions = [
    {"amount": 100.0, "description": "Groceries", "username": "user1"},
    {"amount": 50.0, "description": "Gas bill", "username": "user2"},
    {"amount": 200.0, "description": "Electronics", "username": "user1"},
]

transactions_db.extend(sample_transactions)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class User(BaseModel):
    username: str
    password: str

class UserInDB(User):
    hashed_password: str

class Transaction(BaseModel):
    amount: float
    description: str
    username: str  # Add username field to associate transactions with users

class TransactionInDB(Transaction):
    transaction_id: int

class TokenData(BaseModel):
    username: str  # Define TokenData model to hold token data

# Functions to manage users
def get_user(username: str):
    logger.info("Getting user. ")
    if username in users_db:
        user_dict = users_db[username]
        return UserInDB(**user_dict)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency to get the current user
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
        token_data = TokenData(username=username)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    return token_data

# Endpoints
@app.post("/register", response_model=User)
async def register(user: User):
    if user.username in users_db:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    hashed_password = pwd_context.hash(user.password)
    user_data = UserInDB(username=user.username, hashed_password=hashed_password)
    users_db[user.username] = user_data.dict()
    
    return user

@app.post("/login", response_model=dict)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # ... (authentication logic)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": form_data.username}, expires_delta=access_token_expires)
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/transactions", response_model=TransactionInDB)
async def create_transaction(transaction: Transaction, current_user: User = Depends(get_current_user)):
    transaction_id = len(transactions_db) + 1
    transaction_data = TransactionInDB(transaction_id=transaction_id, username=current_user.username, **transaction.dict())
    transactions_db.append(transaction_data)
    
    return transaction_data

@app.get("/transactions", response_model=List[TransactionInDB])
async def list_user_transactions(current_user: User = Depends(get_current_user)):
    user_transactions = [t for t in transactions_db if t.username == current_user.username]
    return user_transactions

@app.put("/transactions/{transaction_id}", response_model=TransactionInDB)
async def update_transaction(transaction_id: int, updated_transaction: Transaction, current_user: User = Depends(get_current_user)):
    transaction_index = None
    for i, transaction in enumerate(transactions_db):
        if transaction.transaction_id == transaction_id and transaction.username == current_user.username:
            transaction_index = i
            break
    
    if transaction_index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    
    transactions_db[transaction_index] = updated_transaction
    transactions_db[transaction_index].transaction_id = transaction_id
    
    return transactions_db[transaction_index]

@app.delete("/transactions/{transaction_id}", response_model=TransactionInDB)
async def delete_transaction(transaction_id: int, current_user: User = Depends(get_current_user)):
    transaction_index = None
    for i, transaction in enumerate(transactions_db):
        if transaction.transaction_id == transaction_id and transaction.username == current_user.username:
            transaction_index = i
            break
    
    if transaction_index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    
    deleted_transaction = transactions_db.pop(transaction_index)
    return deleted_transaction


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP Exception - Status Code: {exc.status_code}, Detail: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.exception("An error occurred")
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Internal Server Error"})


if __name__ == "__main__":

    uvicorn.run(app, host="127.0.0.1", port=8000)