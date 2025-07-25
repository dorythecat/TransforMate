from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

import utils

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/get/{server_id}/{user_id}")
def get_user(server_id: int, user_id: int):
    """Returns the transformed data for a given user in a server"""
    tf = utils.load_tf_by_id(str(user_id), server_id)
    return {"server_id": server_id, "user_id": user_id, "tf": tf}

@app.get("/get/{server_id}")
def get_server(server_id: int):
    """Returns the setings for a given server"""
    tf = utils.load_transformed(server_id)
    return {
        "server_id": server_id,
        "blocked_users": tf['blocked_users'],
        "blocked_channels": tf['blocked_channels'],
        "affixes": tf['affixes']
    }

users_db = {
    "johndoe": {
        "username": "johndoe",
        "hashed_password": "fakehashedsecret",
        "linked_id": "770662556456976415"
    },
    "alice": {
        "username": "alice",
        "hashed_password": "fakehashedsecret2",
        "inked_id": "536561781691383809"
    },
}



def hash_password(password: str):
    return "fakehashed" + password

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = get_user(users_db, token)
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user
