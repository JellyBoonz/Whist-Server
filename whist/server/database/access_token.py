"""Wrapping the token string together with the type in one object."""
from pydantic import BaseModel


class AccessToken(BaseModel):
    """
    Wrapper of the access token.
    """
    token: str
    token_type: str
