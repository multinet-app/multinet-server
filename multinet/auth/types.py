"""Types associated with authentication."""

from typing import Optional
from typing_extensions import TypedDict
from pydantic import BaseModel


class GoogleUserInfo(BaseModel):
    """
    Representation of raw User Info from a Google Account.

    Mostly unused by us, but is the data type of the decoded ID Token.
    Reference: https://developers.google.com/identity/protocols/oauth2/openid-connect#an-id-tokens-payload  # noqa
    """

    family_name: str
    given_name: str
    name: str
    picture: str
    locale: str
    sub: str  # Unique identifier
    email: str
    email_verified: bool

    # Time of token expiration in Unix Seconds
    exp: int

    # Time of token issue
    iat: int

    # Issuer
    iss: str

    azp: str
    aud: str
    at_hash: str
    nonce: str

    hd: Optional[str] = None


class LoginSessionDict(TypedDict):
    """Information on a user's current login session."""

    session: str
    iss: str
    iat: int
    exp: int
