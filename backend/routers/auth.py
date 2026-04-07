from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



@router.get("/items/")
def read_root(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}