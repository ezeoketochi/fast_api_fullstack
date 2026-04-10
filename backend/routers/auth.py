from typing import Annotated
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, ValidationError
from fastapi import APIRouter, Depends, HTTPException, Request, status, FastAPI , Security

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes, HTTPBasic, HTTPBasicCredentials

from models import TokenData, User, UserInDB, Token
from database import fake_users_db
from pwdlib import PasswordHash

import jwt
import secrets
import httpx




SECRET_KEY = "fb8948f4e4b32168d8b19f16440a23b11a529e4b1e71902994e98eecf6343730"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token/",
    scopes={"me": "Read information about the current user.", "items": "Read items."},
)

password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("dummypassword")

security = HTTPBasic()



def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)


@router.get("items/gethash/")
def get_immediate_hash(password: str) -> str:
    return password_hash.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.get("/ip/address")
async def read_ip_address(request: Request):
    # 1. Get the raw client IP
    client_ip = request.client.host
    
    # 2. Check if behind a proxy (like Nginx or Cloudflare) 
    # Use 'x-forwarded-for' to get the REAL user IP if applicable
    real_ip = request.headers.get("x-forwarded-for")
    if real_ip:
        client_ip = real_ip.split(",")[0]

    # Handle local testing (localhost IP won't have geo-data)
    if client_ip in ("127.0.0.1", "::1"):
        return {"error": "Localhost IP detected. Geolocation requires a public IP."}

    # 3. Fetch geolocation data
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://ip-api.com{client_ip}")
        geo_data = response.json()

    return {
        "ip": client_ip,
        "port": request.client.port,
        "location": {
            "country": geo_data.get("country"),
            "region": geo_data.get("regionName"),
            "city": geo_data.get("city"),
            "zip": geo_data.get("zip"),
            "lat": geo_data.get("lat"),
            "lon": geo_data.get("lon"),
        },
        "network": {
            "isp": geo_data.get("isp"),
            "org": geo_data.get("org"),
            "as": geo_data.get("as"),
        }
    }

@router.get("/items/")
def read_root(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}

def fake_decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    return User(
        username=token + "fakedecoded", email="email@gexample.com", full_name="John Doe", disabled=False
    )

async def get_current_user( security_scopes: SecurityScopes, token: Annotated[str, Depends(oauth2_scheme)]):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = f"Bearer"

    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        scope: str = payload.get("scope", "")
        token_scopes = scope.split(" ")
        token_data = TokenData( scopes = token_scopes, username=username)
    except jwt.InvalidTokenError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user



@router.get("/users/me")
async def read_user_me(current_user: Annotated[User, Depends(get_current_user)]):
    frontend_user = User(username=current_user.username, email=current_user.email, full_name=current_user.full_name, disabled=current_user.disabled)
    return frontend_user



@router.get("/users/me")
async def read_current_user(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    return {"username": credentials.username, "password": credentials.password}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


async def get_current_active_user(
    current_user: Annotated[User, Security(get_current_user, scopes=["me"])],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/token/")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scope": " ".join(form_data.scopes)},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")



def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    print("verification sucessful")
    return user


@router.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Security(get_current_active_user, scopes=["items"])],
):
    return [{"item_id": "Foo", "owner": current_user.username}]
