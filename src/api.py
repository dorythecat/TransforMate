import json
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel

import utils
from config import BLOCKED_USERS, CACHE_PATH, SECRET_KEY
from cogs.transformation import transform_function

# Setting some basic things up
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256" # Algorith for JWT to use to encode tokens
ACCESS_TOKEN_EXPIRE_HOURS = 2 # After how many hours does the access token expire automatically

# DB stuff
def load_db(db_path: str) -> dict:
    db_path = db_path.split("/")
    if db_path[-1] not in os.listdir("/".join(db_path[:-1])):
        return {}
    with open("/".join(db_path)) as f:
        contents = f.read().strip()
        if contents == "":
            return {}
        return json.loads(contents)

fake_users_db = load_db(f"{CACHE_PATH}/accounts.json")

# Various utilities
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str
    linked_id: int
    in_servers: list[int]
    admin_servers: list[int]


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

# Login
@app.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """Login to an account."""
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password!",
            headers={"WWW-Authenticate": "Bearer"}
        )
    if user.linked_id in BLOCKED_USERS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are blocked from using this bot!",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")

# Get info
@app.get("/get/{server_id}")
def get_server(current_user: Annotated[User, Depends(get_current_active_user)],
               server_id: int) -> dict:
    """Returns the settings for a given server. If you're an administrator, you'll get the full file for said server."""
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

    return server if server_id in current_user.admin_servers else {
        "blocked_users": server['blocked_users'],
        "blocked_channels": server['blocked_channels'],
        "affixes": server['affixes']
    }

@app.get("/get/{server_id}/{user_id}")
def get_tfed_user(current_user: Annotated[User, Depends(get_current_active_user)],
                  server_id: int,
                  user_id: int) -> dict:
    """Returns the transformed data for a given user in a server."""
    if server_id not in current_user.in_servers:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not in this server!",
            headers={"WWW-Authenticate": "Bearer"}
        )

    server = utils.load_transformed(server_id)
    if server != {} and str(current_user.linked_id) in server['blocked_users']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This server has blocked you!",
            headers={"WWW-Authenticate": "Bearer"}
        )

    tf = utils.load_tf_by_id(str(user_id), server_id)
    if tf != {} and str(current_user.linked_id) in tf['blocked_users']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user has blocked you!",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return tf

# Transform other users
class TransformationData(BaseModel):
    into: str | None = None
    image_url: str | None = None
    channel_id: int | None = None
    brackets: list[str] | None = None
    copy_id: int | None = None
    merge: bool = False

@app.put("/tf/{server_id}/{user_id}")
def tf_user(current_user: Annotated[User, Depends(get_current_active_user)],
            server_id: int,
            user_id: int,
            tf_data: Annotated[TransformationData, Depends()]) -> dict:
    if server_id not in current_user.in_servers:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not in this server!",
            headers={"WWW-Authenticate": "Bearer"}
        )

    server = utils.load_transformed(server_id)
    if server != {}:
        if str(current_user.linked_id) in server['blocked_users']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This server has blocked you!",
                headers={"WWW-Authenticate": "Bearer"}
            )

        if str(user_id) in server['blocked_users']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This server has blocked the user!",
                headers={"WWW-Authenticate": "Bearer"}
            )

        if str(tf_data.channel_id) in server['blocked_channels']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This server has blocked this channel!",
                headers={"WWW-Authenticate": "Bearer"}
            )

    tf = utils.load_tf_by_id(str(user_id), server_id)
    if tf != {}:
        if str(current_user.linked_id) in tf['blocked_users']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This user has blocked you!",
                headers={"WWW-Authenticate": "Bearer"}
            )
        if str(user_id) in tf['blocked_users']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This user has blocked you!",
                headers={"WWW-Authenticate": "Bearer"}
            )

    if utils.is_transformed(user_id, server_id):
        if str(tf_data.channel_id) in tf:
            tf = tf[str(tf_data.channel_id)]
        elif 'all' in tf:
            tf = tf['all']
        elif server != {} and server['affixes']:
            tf = {'claim': None}  # Empty data so we can do multiple tfs
        elif tf == {}:
            # This is to avoid https://github.com/dorythecat/TransforMate/issues/25
            tf = {'claim': None}
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This user is already transformed on this server!",
                headers={"WWW-Authenticate": "Bearer"}
            )
        if tf['claim'] is not None and int(tf['claim']) != current_user.linked_id and tf['eternal']:
            if current_user.linked_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This user is claimed, and you aren't their owner!",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are claimed, and can't transform yourself!",
                headers={"WWW-Authenticate": "Bearer"}
            )

    if server != {} and server['affixes']:
        if not tf_data.brackets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You need to provide brackets in this server!",
                headers={"WWW-Authenticate": "Bearer"}
            )
        if len(tf_data.brackets) > 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provided brackets are improperly formed!",
                headers={"WWW-Authenticate": "Bearer"}
            )
    else:
        if tf_data.brackets is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You can't provide brackets on this server!",
                headers={"WWW-Authenticate": "Bearer"}
            )

    if tf_data.copy_id is not None:
        new_data = utils.load_tf_by_id(str(tf_data.copy_id), server_id)
        if new_data == {} or new_data['all'] == {}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This user is no transformed on this server!",
                headers={"WWW-Authenticate": "Bearer"}
            )
        if tf_data.merge in [False, None]:
            new_data['all']['into'] += "឵឵ᅟ"
        if tf_data.into:
            # Webhook username cannot contain "discord", or it will return a 400 error
            # TODO: Find a better fix, perhaps?
            if tf_data.into.lower().__contains__("discord"):
                tf_data.into = tf_data.into.lower().replace("discord", "Disc0rd")
            new_data['all']['into'] = tf_data.into
        if tf_data.image_url:
            tf_data.image_url = tf_data.image_url.strip()
            if tf_data.image_url[:4] != "http":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image URL must start with http!",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            if "?" in tf_data.image_url:  # Prune url, if possible, to preserve space
                tf_data.image_url = tf_data.image_url[:tf_data.image_url.index("?")]
            new_data['all']['image_url'] = tf_data.image_url
        utils.write_tf(user_id, server_id, new_data=new_data)
        utils.write_transformed(server_id, user_id)
        return utils.load_tf_by_id(str(user_id), server_id)

    if tf_data.into:
        if len(tf_data.into) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name needs to be at least wo characters long!",
            )
        if not tf_data.image_url:
            tf_data.image_url = "https://cdn.discordapp.com/embed/avatars/1.png"
        else:
            tf_data.image_url = tf_data.image_url.strip()
            if tf_data.image_url[:4] != "http":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Image URL! Please provide a valid image URL!",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            if "?" in tf_data.image_url:  # Prune url, if possible, to preserve space
                tf_data.image_url = tf_data.image_url[:tf_data.image_url.index("?")]

        # Webhook username cannot contain "discord", or it will return a 400 error
        # TODO: Find a better fix, perhaps?
        if tf_data.into.lower().__contains__("discord"):
            tf_data.into = tf_data.into.lower().replace("discord", "Disc0rd")

        utils.write_tf(user_id,
                       server_id,
                       tf_data.channel_id,
                       transformed_by=str(current_user.linked_id),
                       into=tf_data.into.strip(),
                       image_url=tf_data.image_url,
                       proxy_prefix=tf_data.brackets[0] if tf_data.brackets is not None else None,
                       proxy_suffix=tf_data.brackets[1] if tf_data.brackets is not None else None)
        utils.write_transformed(server_id, user_id, tf_data.channel_id)

    return utils.load_tf_by_id(str(user_id), server_id)

# User-related features
@app.get("/users/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    """Return the current user's stored information."""
    return current_user

@app.get("/users/me/file")
async def read_users_file_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> dict:
    """Returns the current user's complete file."""
    return utils.load_tf_by_id(str(current_user.linked_id))