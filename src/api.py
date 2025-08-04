import json
import requests
from datetime import datetime, timedelta, timezone
from typing import Annotated, NamedTuple, Union

import jwt
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

import utils
from config import *

DATABASE_PATH = f"{CACHE_PATH}/accounts.json"

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
    version="1.6.1",
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:63342"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALGORITHM = "HS256" # Algorith for JWT to use to encode tokens
security = HTTPBearer()


# Discord API interactions
API_ENDPOINT = 'https://discord.com/api/v10' # Discord API endpoint


def exchange_code(code: str) -> dict:
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post('%s/oauth2/token' % API_ENDPOINT, data=data, headers=headers, auth=(CLIENT_ID, CLIENT_SECRET))
    r.raise_for_status()
    return r.json()


def refresh_token(refresh_token: str) -> dict:
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post('%s/oauth2/token' % API_ENDPOINT, data=data, headers=headers, auth=(CLIENT_ID, CLIENT_SECRET))
    r.raise_for_status()
    return r.json()


def revoke_access_token(access_token: str) -> None:
    data = {
        'token': access_token,
        'token_type_hint': 'access_token'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    requests.post('%s/oauth2/token/revoke' % API_ENDPOINT, data=data, headers=headers, auth=(CLIENT_ID, CLIENT_SECRET))


def get_user_info(access_token: str) -> dict:
    headers = {
        'Authorization': 'Bearer %s' % access_token
    }
    r = requests.get('%s/users/@me' % API_ENDPOINT, headers=headers)
    r.raise_for_status()
    return r.json()


def get_user_guilds(access_token: str) -> list[dict]:
    headers = {
        'Authorization': 'Bearer %s' % access_token
    }
    r = requests.get('%s/users/@me/guilds' % API_ENDPOINT, headers=headers)
    r.raise_for_status()
    return r.json()


# Various utilities
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str | HTTPException:
    """Get and validate the Authorization header token."""
    token = credentials.credentials if credentials else None
    if not token:
        return None
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return data
    except InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


class ErrorMessage(BaseModel):
    message: str


# Login
@app.get("/login",
         tags=["Security"],
         response_model=None,
         responses={
             403: { 'model': ErrorMessage },
             502: { 'model': ErrorMessage }
         })
async def login(code: str, redirect_url: str) -> RedirectResponse | JSONResponse:
    """Login to a Discord account."""
    data = exchange_code(code)
    user_data = get_user_info(data['access_token'])
    if not ('identify' in data['scope'] and 'guilds' in data['scope']):
        return JSONResponse(status_code=502,
                            content={ 'detail': 'Required Discord scopes were not granted' })
    if user_data['id'] in BLOCKED_USERS:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'That user is blocked from using the bot' })
    access_token = create_access_token(data={'access_token': data['access_token']},
                                       expires_delta=timedelta(seconds=int(data['expires_in'])))
    return RedirectResponse(url=redirect_url + '?token=' + access_token, status_code=303)


@app.post("/logout",
          tags=["Security"])
async def logout(token: Annotated[str, Depends(get_current_token)]) -> None:
    """Logout of a Discord account."""
    revoke_access_token(token)


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
             403: { 'model': ErrorMessage },
             404: { 'model': ErrorMessage }
         })
async def get_server(token: Annotated[str, Depends(get_current_token)],
                     server_id: int) -> ServerDataBasic | ServerData | JSONResponse:
    """Returns the settings for a given server. If you're an administrator, you'll get the full file for said server."""
    user_guilds = get_user_guilds(token)
    guild = None
    is_admin = False
    for g in user_guilds:
        if g['id'] == str(server_id):
            guild = g
            is_admin = int(g['permissions']) & 8 == 8
            break

    if guild is None:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'Current user is not on that server' })

    server = utils.load_transformed(server_id)
    if server == {}:
        return JSONResponse(status_code=404,
                            content={ 'detail': 'That server does not have TransforMate in it' })

    current_user_info = get_user_info(token)
    if current_user_info['id'] in server['blocked_users']:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'This server has blocked the current user' })

    return ServerData(
        blocked_users=server['blocked_users'],
        blocked_channels=server['blocked_channels'],
        logs_channels=server['logs'],
        clear_other_logs=server['clear_other_logs'],
        affixes=server['affixes'],
        transformed_users=server['transformed_users']
    ) if is_admin else ServerDataBasic(
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
             403: { 'model': ErrorMessage },
             404: { 'model': ErrorMessage }
         })
async def get_tfed_user(token: Annotated[str, Depends(get_current_token)],
                        server_id: int,
                        user_id: int) -> UserData | JSONResponse:
    """Returns the transformed data for a given user in a server."""
    user_guilds = get_user_guilds(token)
    guild = None
    for g in user_guilds:
        if g['id'] == str(server_id):
            guild = g
            break

    if guild is None:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'Current user is not on that server' })

    if user_id in BLOCKED_USERS:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'That user is blocked from using the bot' })

    server = utils.load_transformed(server_id)
    if server == {}:
        return JSONResponse(status_code=404,
                            content={ 'detail': 'That server does not have TransforMate in it' })

    current_user_info = get_user_info(token)
    current_user_id = current_user_info['id']
    if current_user_id in server['blocked_users']:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'This server has blocked the current user' })

    if str(user_id) in server['blocked_users']:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'This server has blocked that user' })

    tf = utils.load_tf(user_id, server_id)
    if tf != {} and current_user_id in tf['blocked_users']:
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
             404: { 'model': ErrorMessage },
             409: { 'model': ErrorMessage }
         })
async def tf_user(token: Annotated[str, Depends(get_current_token)],
                  server_id: int,
                  user_id: int,
                  tf_data: Annotated[TransformData, Depends()]) -> UserTransformationData | JSONResponse:
    """Transforms a given user."""
    user_guilds = get_user_guilds(token)
    guild = None
    for g in user_guilds:
        if g['id'] == str(server_id):
            guild = g
            break

    if guild is None:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'Current user is not on that server' })

    if user_id in BLOCKED_USERS:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'That user is blocked from using the bot' })

    server = utils.load_transformed(server_id)
    if server == {}:
        # TODO: Add a way to check if the bot is in this server
        return JSONResponse(status_code=404,
                            content={ 'detail': 'That server does not have TransforMate in it' })

    current_user_info = get_user_info(token)
    current_user_id = current_user_info['id']
    if current_user_id in server['blocked_users']:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'This server has blocked the current user' })

    if str(user_id) in server['blocked_users']:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'This server has blocked that user' })

    if str(tf_data.channel_id) in server['blocked_channels']:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'This server has blocked that channel' })

    tf = utils.load_tf(user_id, server_id)
    if tf != {} and current_user_id in tf['blocked_users']:
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

        if tf['claim'] is not None and tf['claim'] != current_user_id and tf['eternal']:
            if int(current_user_id) != user_id:
                return JSONResponse(status_code=409,
                                    content={ 'detail': 'That user is claimed, and you are not their owner' })
            return JSONResponse(status_code=409,
                                content={'detail': 'You are claimed, and can not transform yourself' })

    if server['affixes']:
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
                       transformed_by=current_user_id,
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
                       transformed_by=current_user_id,
                       into=tf_data.into.strip(),
                       image_url=tf_data.image_url,
                       proxy_prefix=tf_data.brackets[0] if tf_data.brackets is not None else None,
                       proxy_suffix=tf_data.brackets[1] if tf_data.brackets is not None else None)

    utils.write_transformed(server_id, user_id, tf_data.channel_id)
    tf = utils.load_tf(user_id, server_id)
    channel_id = tf_data.channel_id if tf_data.channel_id else 'all'
    tf = tf[channel_id] if channel_id in tf else tf['all']
    return UserTransformationData(
        transformed_by=tf['transformed_by'],
        into=tf['into'],
        image_url=tf['image_url'],
        claim=tf['claim'],
        eternal=tf['eternal'],
        prefix=Modifier(
            tf['prefix']['active'],
            tf['prefix']['contents']
        ),
        suffix=Modifier(
            tf['prefix']['active'],
            tf['prefix']['contents'],
        ),
        big=tf['big'],
        small=tf['small'],
        hush=tf['hush'],
        backwards=tf['backwards'],
        censor=Modifier(
            tf['censor']['active'],
            tf['censor']['contents']
        ),
        sprinkle=Modifier(
            tf['sprinkle']['active'],
            tf['sprinkle']['contents']
        ),
        muffle=Modifier(
            tf['muffle']['active'],
            tf['muffle']['contents']
        ),
        alt_muffle=Modifier(
            tf['alt_muffle']['active'],
            tf['alt_muffle']['contents']
        ),
        stutter=tf['stutter'],
        proxy_prefix=tf['proxy_prefix'],
        proxy_suffix=tf['proxy_suffix'],
        bio=tf['bio']
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
    censor: str | None = None
    censor_replacement: str | None = None
    sprinkle: str | None = None
    muffle: str | None = None
    alt_muffle: str | None = None
    stutter: int | None = None
    bio: str | None = None
    chance: int | None = None


@app.put("/mod/{server_id}/{user_id}",
         tags=["Transformation"],
         response_model=UserTransformationData,
         responses={
             400: { 'model': ErrorMessage },
             403: { 'model': ErrorMessage },
             404: { 'model': ErrorMessage },
             409: { 'model': ErrorMessage }
         })
async def modifier_user(token: Annotated[str, Depends(get_current_token)],
                        server_id: int,
                        user_id: int,
                        mod_data: Annotated[ModData, Depends()]) -> UserTransformationData | JSONResponse:
    """Modifies a given user's settings."""
    user_guilds = get_user_guilds(token)
    guild = None
    for g in user_guilds:
        if g['id'] == str(server_id):
            guild = g
            break

    if guild is None:
        return JSONResponse(status_code=403,
                            content={'detail': 'Current user is not on that server'})

    if user_id in BLOCKED_USERS:
        return JSONResponse(status_code=403,
                            content={ 'detail': 'That user is blocked from using the bot' })

    server = utils.load_transformed(server_id)
    if server == {}:
        return JSONResponse(status_code=404,
                            content={'detail': 'That server does not have TransforMate in it'})

    current_user_info = get_user_info(token)
    current_user_id = current_user_info['id']
    if current_user_id in server['blocked_users']:
        return JSONResponse(status_code=403,
                            content={'detail': 'This server has blocked the current user'})

    if str(user_id) in server['blocked_users']:
        return JSONResponse(status_code=403,
                            content={'detail': 'This server has blocked that user'})

    if str(mod_data.channel_id) in server['blocked_channels']:
        return JSONResponse(status_code=403,
                            content={'detail': 'This server has blocked that channel'})

    tf = utils.load_tf(user_id, server_id)
    if tf != {} and current_user_id in tf['blocked_users']:
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

        if tf['claim'] is not None and tf['claim'] != current_user_id and tf['eternal']:
            if int(current_user_id) != user_id:
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
                   censor=mod_data.censor,
                   censor_replacement=mod_data.censor_replacement,
                   sprinkle=mod_data.sprinkle,
                   muffle=mod_data.muffle,
                   alt_muffle=mod_data.alt_muffle,
                   stutter=mod_data.stutter,
                   bio=mod_data.bio,
                   chance=mod_data.chance)

    tf = utils.load_tf(user_id, server_id)
    channel_id = mod_data.channel_id if mod_data.channel_id else 'all'
    tf = tf[channel_id] if channel_id in tf else tf['all']
    return UserTransformationData(
        transformed_by=tf['transformed_by'],
        into=tf['into'],
        image_url=tf['image_url'],
        claim=tf['claim'],
        eternal=tf['eternal'],
        prefix=Modifier(
            tf['prefix']['active'],
            tf['prefix']['contents']
        ),
        suffix=Modifier(
            tf['prefix']['active'],
            tf['prefix']['contents'],
        ),
        big=tf['big'],
        small=tf['small'],
        hush=tf['hush'],
        backwards=tf['backwards'],
        censor=Modifier(
            tf['censor']['active'],
            tf['censor']['contents']
        ),
        sprinkle=Modifier(
            tf['sprinkle']['active'],
            tf['sprinkle']['contents']
        ),
        muffle=Modifier(
            tf['muffle']['active'],
            tf['muffle']['contents']
        ),
        alt_muffle=Modifier(
            tf['alt_muffle']['active'],
            tf['alt_muffle']['contents']
        ),
        stutter=tf['stutter'],
        proxy_prefix=tf['proxy_prefix'],
        proxy_suffix=tf['proxy_suffix'],
        bio=tf['bio']
    )


@app.put("/tsf/{server_id}/{user_id}",
         tags=["Transformation"],
         response_model=UserTransformationData,
         responses={
             400: { 'model': ErrorMessage },
             403: { 'model': ErrorMessage },
             404: { 'model': ErrorMessage },
             409: { 'model': ErrorMessage }
         })
async def tsf_user(token: Annotated[str, Depends(get_current_token)],
                   server_id: int,
                   user_id: int,
                   tsf_string: str) -> UserTransformationData | JSONResponse:
    """Modifies a user's settings using a TSF-compliant string."""
    user_guilds = get_user_guilds(token)
    guild = None
    for g in user_guilds:
        if g['id'] == str(server_id):
            guild = g
            break

    if guild is None:
        return JSONResponse(status_code=403,
                            content={'detail': 'Current user is not on that server'})

    if user_id in BLOCKED_USERS:
        return JSONResponse(status_code=403,
                            content={'detail': 'That user is blocked from using the bot'})

    server = utils.load_transformed(server_id)
    if server == {}:
        return JSONResponse(status_code=404,
                            content={'detail': 'That server does not have TransforMate in it'})

    current_user_info = get_user_info(token)
    current_user_id = current_user_info['id']
    if current_user_id in server['blocked_users']:
        return JSONResponse(status_code=403,
                            content={'detail': 'This server has blocked the current user'})

    if str(user_id) in server['blocked_users']:
        return JSONResponse(status_code=403,
                            content={'detail': 'This server has blocked that user'})

    tf = utils.load_tf(user_id, server_id)
    if tf != {} and current_user_id in tf['blocked_users']:
        return JSONResponse(status_code=403,
                            content={'detail': 'That user has blocked the current user'})

    if utils.is_transformed(user_id, server_id):
        if str(mod_data.channel_id) in tf:
            tf = tf[str(mod_data.channel_id)]
        elif 'all' in tf:
            tf = tf['all']
        elif server != {} and server['affixes']:
            tf = {'claim': None}  # Empty data so we can do multiple tfs
        elif tf == {}:
            # This is to avoid https://github.com/dorythecat/TransforMate/issues/25
            tf = {'claim': None}
        else:
            return JSONResponse(status_code=409,
                                content={'detail': 'That user is already transformed on this server'})

        if tf['claim'] is not None and tf['claim'] != current_user_id and tf['eternal']:
            if int(current_user_id) != user_id:
                return JSONResponse(status_code=409,
                                    content={'detail': 'That user is claimed, and you are not their owner'})
            return JSONResponse(status_code=409,
                                content={'detail': 'You are claimed, and can not transform yourself'})

    try:
        new_data = utils.decode_tsf(tsf_string)
    except ValueError as e:
        return JSONResponse(status_code=400,
                            content={'detail': str(e)})

    new_data['transformed_by'] = user_id
    new_data['claim'] = None
    new_data['eternal'] = False

    data = utils.load_tf(user_id, server_id)
    data['all'] = new_data
    utils.write_tf(user_id, server_id, None, data)

    return UserTransformationData(
        transformed_by=new_data['transformed_by'],
        into=new_data['into'],
        image_url=new_data['image_url'],
        claim=new_data['claim'],
        eternal=new_data['eternal'],
        prefix=Modifier(
            new_data['prefix']['active'],
            new_data['prefix']['contents']
        ),
        suffix=Modifier(
            new_data['prefix']['active'],
            new_data['prefix']['contents'],
        ),
        big=new_data['big'],
        small=new_data['small'],
        hush=new_data['hush'],
        backwards=new_data['backwards'],
        censor=Modifier(
            new_data['censor']['active'],
            new_data['censor']['contents']
        ),
        sprinkle=Modifier(
            new_data['sprinkle']['active'],
            new_data['sprinkle']['contents']
        ),
        muffle=Modifier(
            new_data['muffle']['active'],
            new_data['muffle']['contents']
        ),
        alt_muffle=Modifier(
            new_data['alt_muffle']['active'],
            new_data['alt_muffle']['contents']
        ),
        stutter=new_data['stutter'],
        proxy_prefix=new_data['proxy_prefix'],
        proxy_suffix=new_data['proxy_suffix'],
        bio=new_data['bio']
    )


# User-related features
@app.get("/users/me",
         tags=["Your User"],
         response_model=dict)
async def read_users_file_me(token: Annotated[str, Depends(get_current_token)]) -> dict:
    """Returns the current user's complete file."""
    return utils.load_tf(int(get_user_info(token)))


class DiscordUser(BaseModel):
    id: int
    username: str
    avatar: str
    global_name: str


@app.get("/users/me/discord",
         tags=["Your User"],
         response_model=DiscordUser)
async def read_users_discord_me(token: Annotated[str, Depends(get_current_token)]) -> DiscordUser:
    """Returns the current user's Discord data."""
    user = get_user_info(token)
    return DiscordUser(
        id=int(user['id']),
        username=user['username'],
        avatar=user['avatar'],
        global_name=user['global_name']
    )


class DiscordServer(BaseModel):
    id: int
    name: str
    owner: bool
    admin: bool


@app.get("/users/me/discord/servers",
         tags=["Your User"],
         response_model=list[DiscordServer])
async def read_users_discord_servers_me(token: Annotated[str, Depends(get_current_token)]) -> list[DiscordServer]:
    """Returns the current user's Discord servers on which the bot is at the current moment."""
    user_guilds = get_user_guilds(token)
    bot_servers = []
    
    for guild in user_guilds:
        guild_data = utils.load_transformed(int(guild['id']))
        if guild_data != {}:  # Bot is present on this server
            bot_servers.append(DiscordServer(
                id=int(guild['id']),
                name=guild['name'],
                owner=guild['owner'],
                admin=int(guild['permissions']) & 8 == 8
            ))
    return bot_servers
    


@app.put("/users/me/tsf",
         tags=["Your User"],
         response_model=UserTransformationData,
         responses={
             400: { 'model': ErrorMessage },
             403: { 'model': ErrorMessage },
             404: { 'model': ErrorMessage },
             409: { 'model': ErrorMessage }
         })
async def tsf_user_me(token: Annotated[str, Depends(get_current_token)],
                      server_id: int,
                      tsf_string: str) -> UserTransformationData | JSONResponse:
    """Modifies the current user's settings using a TSF-compliant string."""
    user_id = int(get_user_info(token))
    user_guilds = get_user_guilds(token)
    guild = None
    for g in user_guilds:
        if g['id'] == str(server_id):
            guild = g
            break

    if guild is None:
        return JSONResponse(status_code=403,
                            content={'detail': 'Current user is not on that server'})

    if user_id in BLOCKED_USERS:
        return JSONResponse(status_code=403,
                            content={'detail': 'That user is blocked from using the bot'})

    server = utils.load_transformed(server_id)
    if server == {}:
        return JSONResponse(status_code=404,
                            content={'detail': 'That server does not have TransforMate in it'})

    current_user_info = get_user_info(token)
    current_user_id = current_user_info['id']
    if current_user_id in server['blocked_users']:
        return JSONResponse(status_code=403,
                            content={'detail': 'This server has blocked the current user'})

    if str(user_id) in server['blocked_users']:
        return JSONResponse(status_code=403,
                            content={'detail': 'This server has blocked that user'})

    tf = utils.load_tf(user_id, server_id)
    if tf != {} and current_user_id in tf['blocked_users']:
        return JSONResponse(status_code=403,
                            content={'detail': 'That user has blocked the current user'})

    if utils.is_transformed(user_id, server_id):
        if str(mod_data.channel_id) in tf:
            tf = tf[str(mod_data.channel_id)]
        elif 'all' in tf:
            tf = tf['all']
        elif server != {} and server['affixes']:
            tf = {'claim': None}  # Empty data so we can do multiple tfs
        elif tf == {}:
            # This is to avoid https://github.com/dorythecat/TransforMate/issues/25
            tf = {'claim': None}
        else:
            return JSONResponse(status_code=409,
                                content={'detail': 'That user is already transformed on this server'})

        if tf['claim'] is not None and tf['claim'] != current_user_id and tf['eternal']:
            if int(current_user_id) != user_id:
                return JSONResponse(status_code=409,
                                    content={'detail': 'That user is claimed, and you are not their owner'})
            return JSONResponse(status_code=409,
                                content={'detail': 'You are claimed, and can not transform yourself'})

    try:
        new_data = utils.decode_tsf(tsf_string)
    except ValueError as e:
        return JSONResponse(status_code=400,
                            content={'detail': str(e)})

    new_data['transformed_by'] = user_id
    new_data['claim'] = None
    new_data['eternal'] = False

    data = utils.load_tf(user_id, server_id)
    data['all'] = new_data
    utils.write_tf(user_id, server_id, None, data)

    return UserTransformationData(
        transformed_by=new_data['transformed_by'],
        into=new_data['into'],
        image_url=new_data['image_url'],
        claim=new_data['claim'],
        eternal=new_data['eternal'],
        prefix=Modifier(
            new_data['prefix']['active'],
            new_data['prefix']['contents']
        ),
        suffix=Modifier(
            new_data['prefix']['active'],
            new_data['prefix']['contents'],
        ),
        big=new_data['big'],
        small=new_data['small'],
        hush=new_data['hush'],
        backwards=new_data['backwards'],
        censor=Modifier(
            new_data['censor']['active'],
            new_data['censor']['contents']
        ),
        sprinkle=Modifier(
            new_data['sprinkle']['active'],
            new_data['sprinkle']['contents']
        ),
        muffle=Modifier(
            new_data['muffle']['active'],
            new_data['muffle']['contents']
        ),
        alt_muffle=Modifier(
            new_data['alt_muffle']['active'],
            new_data['alt_muffle']['contents']
        ),
        stutter=new_data['stutter'],
        proxy_prefix=new_data['proxy_prefix'],
        proxy_suffix=new_data['proxy_suffix'],
        bio=new_data['bio']
    )