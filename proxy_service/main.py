from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import httpx

app = FastAPI()
USER_SERVICE_URL = "http://user_service:8001"

# JWT {
SECRET_KEY = "JOPAAAAAAAA"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# }

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login: str = payload.get("sub")
        if login is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/{login}")
    
    if response.status_code != 200:
        raise credentials_exception
    
    return response.json()

@app.post("/register")
async def register_proxy(user_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{USER_SERVICE_URL}/register",
            json=user_data
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", "Registration failed")
        )
    return response.json()

@app.post("/login")
async def login_proxy(credentials: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{USER_SERVICE_URL}/login",
            json=credentials
        )
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = create_access_token(data={"sub": credentials["login"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profile")
async def get_profile_proxy(current_user: dict = Depends(get_current_user)):
    return current_user

@app.put("/profile")
async def update_profile_proxy(
    update_data: dict,
    current_user: dict = Depends(get_current_user)
):
    if "login" in update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change login"
        )

    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{USER_SERVICE_URL}/users/{current_user['login']}",
            json=update_data
        )
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", "Update failed")
        )
    
    return response.json()

@app.get("/health")
async def health_check():
    return {"status": "ok"}
