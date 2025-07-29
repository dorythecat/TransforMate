import json
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, NamedTuple, Union

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel

import utils
from config import BLOCKED_USERS, CACHE_PATH, SECRET_KEY
from cogs.transformation import transform_function

# Setting some basic things up
app = FastAPI(
    title="TransforMate API",
    summary="A versatile API for the TransforMate Discord bot.",
    description="""
        The API for the TransforMate Discord bot allows you to do stuff like:
        - Transform users
        - Get information about users or servers
        - Modify a user's settings
        - See your own information
        All of this with proper security and more to come!
    """,
    version="1.5.5",
    terms_of_service="https://github.com/dorythecat/TransforMate/blob/main/legal/TERMS_OF_SERVICE.md",
    contact={
        "name": "Official TransforMate Discord Server",
        "url": "https://discord.gg/uGjWk2SRf6"
    },
    license_info={
        "name": "GNU Affero General Public License v3.0 or later",
        "identifier": "AGPL-3.0-or-later"
    },
    openapi_tags=[
        {
            "name": "Security",
            "description": "Security-related actions"
        },
        {
            "name": "Get",
            "description": "Get information about a user or server"
        },
        {
            "name": "Transformation",
            "description": "Transformation and modification"
        },
        {
            "name": "Your User",
            "description": "Get information about the current logged-in user"
        }
    ]
)
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

class ErrorMessage(BaseModel):
    message: str

# Login
@app.post("/token",
          tags=["Security"],
          response_model=Token,
          responses={
              403: { 'model': ErrorMessage }
          })
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token | JSONResponse:
    """Login to an account."""
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'Incorrect username or password' })
    if user.linked_id in BLOCKED_USERS:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'You are blocked from using the bot' })
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")

# Get info
class ServerDataBasic(BaseModel):
    blocked_users: list[int] = []
    blocked_channels: list[int] = []
    affixes: bool = False

class ServerLogChannels(NamedTuple):
    edit_logs: int | None = None
    delete_logs: int | None = None
    transform_logs: int | None = None
    claim_logs: int | None = None

class ServerData(BaseModel):
    blocked_users: list[int] = []
    blocked_channels: list[int] = []
    logs_channels: ServerLogChannels = ServerLogChannels()
    clear_other_logs: bool = False
    affixes: bool = False
    transformed_users: dict[str, list[str]] = {}

@app.get("/get/{server_id}",
         tags=["Get"],
         response_model=Union[ServerDataBasic, ServerData],
         responses={
             403: { 'model': ErrorMessage }
         })
def get_server(current_user: Annotated[User, Depends(get_current_active_user)],
               server_id: int) -> ServerDataBasic | ServerData | JSONResponse:
    """Returns the settings for a given server. If you're an administrator, you'll get the full file for said server."""
    if server_id not in current_user.in_servers:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'Current user is not on that server' })

    server = utils.load_transformed(server_id)
    if str(current_user.linked_id) in server['blocked_users']:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'This server has blocked the current user' })

    return ServerData(
        blocked_users=server['blocked_users'],
        blocked_channels=server['blocked_channels'],
        logs_channels=server['logs'],
        clear_other_logs=server['clear_other_logs'],
        affixes=server['affixes'],
        transformed_users=server['transformed_users']
    ) if server_id in current_user.admin_servers else ServerDataBasic(
        blocked_users=server['blocked_users'],
        blocked_channels=server['blocked_channels'],
        affixes=server['affixes']
    )

class Modifier(NamedTuple):
    active: bool = False
    contents: dict = {}

class UserTransformationData(BaseModel):
    transformed_by: int = 0
    into: str = ""
    image_url: str = ""
    claim: int | None = None
    eternal: bool = False
    prefix: Modifier = Modifier()
    suffix: Modifier = Modifier()
    big: bool = False
    small: bool = False
    hush: bool = False
    backwards: bool = False
    censor: Modifier = Modifier()
    sprinkle: Modifier = Modifier()
    muffle: Modifier = Modifier()
    alt_muffle: Modifier = Modifier()
    stutter: int = 0
    proxy_prefix: str | None = None
    proxy_suffix: str | None = None
    bio: str | None = None

class UserData(BaseModel):
    blocked_channels: list[int] = []
    blocked_users: list[int] = []
    all: UserTransformationData = UserTransformationData()

@app.get("/get/{server_id}/{user_id}",
         tags=["Get"],
         response_model=UserData,
         responses={
             403: { 'model': ErrorMessage }
         })
def get_tfed_user(current_user: Annotated[User, Depends(get_current_active_user)],
                  server_id: int,
                  user_id: int) -> UserData | JSONResponse:
    """Returns the transformed data for a given user in a server."""
    if server_id not in current_user.in_servers:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'Current user is not on that server' })

    if user_id in BLOCKED_USERS:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'That user is blocked from using the bot' })

    server = utils.load_transformed(server_id)
    if server != {}:
        if str(current_user.linked_id) in server['blocked_users']:
            return JSONResponse(status_code=403,
                                content={ 'detail': 'This server has blocked the current user' })

        if str(user_id) in server['blocked_users']:
            return JSONResponse(status_code=403,
                                content={ 'detail': 'This server has blocked that user' })

    tf = utils.load_tf(user_id, server_id)
    if tf != {} and str(current_user.linked_id) in tf['blocked_users']:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'This user has blocked the current user' })

    return UserData(
        blocked_users=tf['blocked_users'],
        blocked_channels=tf['blocked_channels'],
        all=UserTransformationData(
            transformed_by=tf['all']['transformed_by'],
            into=tf['all']['into'],
            image_url=tf['all']['image_url'],
            claim=tf['all']['claim'],
            eternal=tf['all']['eternal'],
            prefix=Modifier(
                tf['all']['prefix']['active'],
                tf['all']['prefix']['contents']
            ),
            suffix=Modifier(
                tf['all']['prefix']['active'],
                tf['all']['prefix']['contents'],
            ),
            big=tf['all']['big'],
            small=tf['all']['small'],
            hush=tf['all']['hush'],
            backwards=tf['all']['backwards'],
            censor=Modifier(
                tf['all']['censor']['active'],
                tf['all']['censor']['contents']
            ),
            sprinkle=Modifier(
                tf['all']['sprinkle']['active'],
                tf['all']['sprinkle']['contents']
            ),
            muffle=Modifier(
                tf['all']['muffle']['active'],
                tf['all']['muffle']['contents']
            ),
            alt_muffle=Modifier(
                tf['all']['alt_muffle']['active'],
                tf['all']['alt_muffle']['contents']
            ),
            stutter=tf['all']['stutter'],
            proxy_prefix=tf['all']['proxy_prefix'],
            proxy_suffix=tf['all']['proxy_suffix'],
            bio=tf['all']['bio']
        )
    )

# Transform other users
class TransformData(BaseModel):
    into: str | None = None
    image_url: str | None = None
    channel_id: int | None = None
    brackets: list[str] | None = None
    copy_id: int | None = None
    merge: bool = False

@app.put("/tf/{server_id}/{user_id}",
         tags=["Transformation"],
         response_model=UserTransformationData,
         responses={
             400: { 'model': ErrorMessage },
             403: { 'model': ErrorMessage },
             409: { 'model': ErrorMessage }
         })
def tf_user(current_user: Annotated[User, Depends(get_current_active_user)],
            server_id: int,
            user_id: int,
            tf_data: Annotated[TransformData, Depends()]) -> UserTransformationData | JSONResponse:
    if server_id not in current_user.in_servers:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'Current user is not on that server' })

    if user_id in BLOCKED_USERS:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'That user is blocked from using the bot' })

    server = utils.load_transformed(server_id)
    if server != {}:
        if str(current_user.linked_id) in server['blocked_users']:
            return JSONResponse(status_code=403,
                                content={ 'detail': 'This server has blocked the current user' })

        if str(user_id) in server['blocked_users']:
            return JSONResponse(status_code=403,
                                content={ 'detail': 'This server has blocked that user' })

        if str(tf_data.channel_id) in server['blocked_channels']:
            return JSONResponse(status_code=403,
                                content={ 'detail': 'This server has blocked that channel' })

    tf = utils.load_tf(user_id, server_id)
    if tf != {} and str(current_user.linked_id) in tf['blocked_users']:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'That user has blocked the current user' })

    if utils.is_transformed(user_id, server_id):
        if str(tf_data.channel_id) in tf:
            tf = tf[str(tf_data.channel_id)]
        elif 'all' in tf:
            tf = tf['all']
        elif server != {} and server['affixes']:
            tf = { 'claim': None }  # Empty data so we can do multiple tfs
        elif tf == {}:
            # This is to avoid https://github.com/dorythecat/TransforMate/issues/25
            tf = { 'claim': None }
        else:
            return JSONResponse(status_code=409,
                                content={ 'detail': 'That user is already transformed on this server' })

        if tf['claim'] is not None and int(tf['claim']) != current_user.linked_id and tf['eternal']:
            if current_user.linked_id != user_id:
                return JSONResponse(status_code=409,
                                    content={ 'detail': 'That user is claimed, and you are not their owner' })
            return JSONResponse(status_code=409,
                                content={'detail': 'You are claimed, and can not transform yourself' })

    if server != {} and server['affixes']:
        if not tf_data.brackets:
            return JSONResponse(status_code=400,
                                content={ 'detail': 'You need to provide brackets on this server' })
        if len(tf_data.brackets) > 2:
            return JSONResponse(status_code=400,
                                content={ 'detail': 'The provided brackets are improperly formed' })
    else:
        if tf_data.brackets is not None:
            return JSONResponse(status_code=400,
                                content={ 'detail': 'You must not provide brackets on this server' })

    if tf_data.copy_id:
        new_data = utils.load_tf(tf_data.copy_id, server_id)
        if new_data == {} or new_data['all'] == {}:
            return JSONResponse(status_code=409,
                                content={ 'detail': 'That user is not transformed on this server' })
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
                return JSONResponse(status_code=400,
                                    content={ 'detail': 'The image URL must start with "http"' })
            if "?" in tf_data.image_url:  # Prune url, if possible, to preserve space
                tf_data.image_url = tf_data.image_url[:tf_data.image_url.index("?")]
            new_data['all']['image_url'] = tf_data.image_url
        utils.write_tf(user_id,
                       server_id,
                       tf_data.channel_id,
                       transformed_by=str(current_user.linked_id),
                       new_data=new_data)

    elif tf_data.into:
        if len(tf_data.into) <= 1:
            return JSONResponse(status_code=400,
                                content={ 'detail': 'Name must be at least two characters long' })
        if not tf_data.image_url:
            tf_data.image_url = "https://cdn.discordapp.com/embed/avatars/1.png"
        else:
            tf_data.image_url = tf_data.image_url.strip()
            if tf_data.image_url[:4] != "http":
                return JSONResponse(status_code=400,
                                    content={ 'detail': 'The image URL must start with "http"' })
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
    tf = utils.load_tf(user_id, server_id)
    channel_id = tf_data.channel_id if tf_data.channel_id else 'all'
    return UserTransformationData(
        transformed_by=tf[channel_id]['transformed_by'],
        into=tf[channel_id]['into'],
        image_url=tf[channel_id]['image_url'],
        claim=tf[channel_id]['claim'],
        eternal=tf[channel_id]['eternal'],
        prefix=Modifier(
            tf[channel_id]['prefix']['active'],
            tf[channel_id]['prefix']['contents']
        ),
        suffix=Modifier(
            tf[channel_id]['prefix']['active'],
            tf[channel_id]['prefix']['contents'],
        ),
        big=tf[channel_id]['big'],
        small=tf[channel_id]['small'],
        hush=tf[channel_id]['hush'],
        backwards=tf[channel_id]['backwards'],
        censor=Modifier(
            tf[channel_id]['censor']['active'],
            tf[channel_id]['censor']['contents']
        ),
        sprinkle=Modifier(
            tf[channel_id]['sprinkle']['active'],
            tf[channel_id]['sprinkle']['contents']
        ),
        muffle=Modifier(
            tf['all']['muffle']['active'],
            tf['all']['muffle']['contents']
        ),
        alt_muffle=Modifier(
            tf[channel_id]['alt_muffle']['active'],
            tf[channel_id]['alt_muffle']['contents']
        ),
        stutter=tf[channel_id]['stutter'],
        proxy_prefix=tf[channel_id]['proxy_prefix'],
        proxy_suffix=tf[channel_id]['proxy_suffix'],
        bio=tf[channel_id]['bio']
    )


# Mod-related features
class ModData(BaseModel):
    channel_id: int | None = None
    claim: int | None = None
    eternal: bool | None = None
    prefix: str | None = None
    suffix: str | None = None
    big: bool | None = None
    small: bool | None = None
    hush: bool | None = None
    backwards: bool | None = None
    censor: dict | None = None
    sprinkle: dict | None = None
    muffle: dict | None = None
    alt_muffle: dict | None = None
    stutter: int | None = None
    bio: str | None = None
    chance: int | None = None

@app.put("/mod/{server_id}/{user_id}",
         tags=["Transformation"],
         response_model=UserTransformationData,
         responses={
             400: { 'model': ErrorMessage },
             403: { 'model': ErrorMessage },
             409: { 'model': ErrorMessage }
         })
def modifier_user(current_user: Annotated[User, Depends(get_current_active_user)],
                  server_id: int,
                  user_id: int,
                  mod_data: Annotated[ModData, Depends()]) -> UserTransformationData | JSONResponse:
    if server_id not in current_user.in_servers:
        return JSONResponse(status_code=403,
                            content={'detail': 'Current user is not on that server'})

    if user_id in BLOCKED_USERS:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'That user is blocked from using the bot' })

    server = utils.load_transformed(server_id)
    if server != {}:
        if str(current_user.linked_id) in server['blocked_users']:
            return JSONResponse(status_code=403,
                                content={'detail': 'This server has blocked the current user'})

        if str(user_id) in server['blocked_users']:
            return JSONResponse(status_code=403,
                                content={'detail': 'This server has blocked that user'})

        if str(mod_data.channel_id) in server['blocked_channels']:
            return JSONResponse(status_code=403,
                                content={'detail': 'This server has blocked that channel'})

    tf = utils.load_tf(user_id, server_id)
    if tf != {} and str(current_user.linked_id) in tf['blocked_users']:
            return JSONResponse(status_code=403,
                                content={'detail': 'That user has blocked the current user'})

    if utils.is_transformed(user_id, server_id):
        if str(mod_data.channel_id) in tf:
            tf = tf[str(mod_data.channel_id)]
        elif 'all' in tf:
            tf = tf['all']
        elif server != {} and server['affixes']:
            tf = { 'claim': None }  # Empty data so we can do multiple tfs
        elif tf == {}:
            # This is to avoid https://github.com/dorythecat/TransforMate/issues/25
            tf = { 'claim': None }
        else:
            return JSONResponse(status_code=409,
                                content={'detail': 'That user is already transformed on this server'})

        if tf['claim'] is not None and int(tf['claim']) != current_user.linked_id and tf['eternal']:
            if current_user.linked_id != user_id:
                return JSONResponse(status_code=409,
                                    content={'detail': 'That user is claimed, and you are not their owner'})
            return JSONResponse(status_code=409,
                                content={'detail': 'You are claimed, and can not transform yourself'})

    utils.write_tf(user_id,
                   server_id,
                   mod_data.channel_id,
                   claim_user=mod_data.claim,
                   eternal=mod_data.eternal,
                   prefix=mod_data.prefix,
                   suffix=mod_data.suffix,
                   big=mod_data.big,
                   small=mod_data.small,
                   hush=mod_data.hush,
                   backwards=mod_data.backwards,
                   sprinkle=mod_data.sprinkle,
                   muffle=mod_data.muffle,
                   alt_muffle=mod_data.alt_muffle,
                   stutter=mod_data.stutter,
                   bio=mod_data.bio,
                   chance=mod_data.chance)

    if mod_data.censor:
        for censor in mod_data.censor:
            utils.write_tf(user_id,
                           server_id,
                           mod_data.channel_id,
                           censor=censor,
                           censor_replacement=mod_data.censor[censor])

    tf = utils.load_tf(user_id, server_id)
    channel_id = mod_data.channel_id if mod_data.channel_id else 'all'
    return UserTransformationData(
        transformed_by=tf[channel_id]['transformed_by'],
        into=tf[channel_id]['into'],
        image_url=tf[channel_id]['image_url'],
        claim=tf[channel_id]['claim'],
        eternal=tf[channel_id]['eternal'],
        prefix=Modifier(
            tf[channel_id]['prefix']['active'],
            tf[channel_id]['prefix']['contents']
        ),
        suffix=Modifier(
            tf[channel_id]['prefix']['active'],
            tf[channel_id]['prefix']['contents'],
        ),
        big=tf[channel_id]['big'],
        small=tf[channel_id]['small'],
        hush=tf[channel_id]['hush'],
        backwards=tf[channel_id]['backwards'],
        censor=Modifier(
            tf[channel_id]['censor']['active'],
            tf[channel_id]['censor']['contents']
        ),
        sprinkle=Modifier(
            tf[channel_id]['sprinkle']['active'],
            tf[channel_id]['sprinkle']['contents']
        ),
        muffle=Modifier(
            tf['all']['muffle']['active'],
            tf['all']['muffle']['contents']
        ),
        alt_muffle=Modifier(
            tf[channel_id]['alt_muffle']['active'],
            tf[channel_id]['alt_muffle']['contents']
        ),
        stutter=tf[channel_id]['stutter'],
        proxy_prefix=tf[channel_id]['proxy_prefix'],
        proxy_suffix=tf[channel_id]['proxy_suffix'],
        bio=tf[channel_id]['bio']
    )

# User-related features
@app.get("/users/me",
         tags=["Your User"],
         response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    """Return the current user's stored information."""
    return current_user

@app.get("/users/me/file",
         tags=["Your User"],
         response_model=dict)
async def read_users_file_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> dict:
    """Returns the current user's complete file."""
    return utils.load_tf(current_user.linked_id)