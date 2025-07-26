from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel

import utils
from config import SECRET_KEY

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# to get a string like this run:
# openssl rand -hex 32
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "email": "johndoe@example.com",
        "linked_id": "770662556456976415",
        "in_servers": ["1270819474571923517"],
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    linked_id: int
    in_servers: list[int]
    admin_servers: list[int] | None = None


class UserInDB(User):
    hashed_password: str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user(db, username: str) -> UserInDB | None:
    if username not in db:
        return None
    user_dict = db[username]
    return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str) -> UserInDB | None:
    user = get_user(fake_db, username)
    if not (user and verify_password(password, user.hashed_password)):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserInDB | None:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials!",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user

@app.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """Login to an account"""
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password!",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


@app.get("/get/{server_id}")
def get_server(current_user: Annotated[User, Depends(get_current_active_user)],
               server_id: int) -> dict:
    """Returns the settings for a given server"""
    if server_id not in current_user.in_servers:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not in this server!",
            headers={"WWW-Authenticate": "Bearer"}
        )

    server = utils.load_transformed(server_id)
    if str(current_user.linked_id) in server['blocked_users']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This server has blocked you!",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "server_id": server_id,
        "blocked_users": server['blocked_users'],
        "blocked_channels": server['blocked_channels'],
        "affixes": server['affixes']
    }

@app.get("/get/{server_id}/{user_id}")
def get_tfed_user(current_user: Annotated[User, Depends(get_current_active_user)],
                  server_id: int,
                  user_id: int) -> dict:
    """Returns the transformed data for a given user in a server"""
    if server_id not in current_user.in_servers:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not in this server!",
            headers={"WWW-Authenticate": "Bearer"}
        )

    server = utils.load_transformed(server_id)
    if str(current_user.linked_id) in server['blocked_users']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This server has blocked you!",
            headers={"WWW-Authenticate": "Bearer"}
        )

    tf = utils.load_tf_by_id(str(user_id), server_id)
    if str(current_user.linked_id) in tf['blocked_users']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user has blocked you!",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {"server_id": server_id, "user_id": user_id, "tf": tf}

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    """Return the current user's stored information"""
    return current_user

@app.get("/users/me/file")
async def read_users_file_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> dict:
    """Returns the current user's complete file"""
    return utils.load_tf_by_id(str(current_user.linked_id))