"""Types associated with authentication."""

from typing import Optional
from dataclasses import dataclass


@dataclass
class GoogleUserInfo:
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
