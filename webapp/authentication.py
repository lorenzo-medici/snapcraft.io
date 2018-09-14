import os
from webapp.api import sso
from pymacaroons import Macaroon
from urllib.parse import urlparse

LOGIN_URL = os.getenv("LOGIN_URL", "https://login.ubuntu.com")


def get_authorization_header(root, discharge):
    """
    Bind root and discharge macaroons and return the authorization header.
    """

    bound = Macaroon.deserialize(root).prepare_for_request(
        Macaroon.deserialize(discharge)
    )

    return "Macaroon root={}, discharge={}".format(root, bound.serialize())


def is_authenticated(session):
    """
    Checks if the user is authenticated from the session
    Returns True if the user is authenticated
    """
    return (
        "openid" in session
        and "macaroon_discharge" in session
        and "macaroon_root" in session
    )


def empty_session(session):
    """
    Empty the session, used to logout.
    """
    session.pop("macaroon_root", None)
    session.pop("macaroon_discharge", None)
    session.pop("openid", None)


def get_caveat_id(root):
    """
    Returns the caveat_id generated by the SSO
    """
    location = urlparse(LOGIN_URL).hostname
    caveat, = [
        c
        for c in Macaroon.deserialize(root).third_party_caveats()
        if c.location == location
    ]

    return caveat.caveat_id


def request_macaroon():
    """
    Request a macaroon from dashboard.
    Returns the macaroon.
    """
    response = sso.post_macaroon(
        {"permissions": ["package_access", "package_upload", "edit_account"]}
    )

    return response["macaroon"]


def get_refreshed_discharge(discharge):
    """
    Get a refresh macaroon if the macaroon is not valid anymore.
    Returns the new discharge macaroon.
    """
    response = sso.get_refreshed_discharge({"discharge_macaroon": discharge})

    return response["discharge_macaroon"]


def is_macaroon_expired(headers):
    """
    Returns True if the macaroon needs to be refreshed from
    the header response.
    """
    return headers.get("WWW-Authenticate") == ("Macaroon needs_refresh=1")
