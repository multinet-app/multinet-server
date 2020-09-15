"""Test that application CORS behaves as we expect."""
import pytest
from flask_cors import CORS
from multinet.util import regex_allowed_origins


@pytest.mark.parametrize(
    "allowed,origin,expected",
    [
        ({"*"}, "thing.com", "thing.com"),
        ({"*", "thing.com"}, "thing.com", "thing.com"),
        ({"thing.com"}, "thing.com", "thing.com"),
        ({"thing.com"}, "notthing.com", None),
        ({"thing.com"}, "subdomain.thing.com", None),
        ({"*.thing.com"}, "subdomain.thing.com", "subdomain.thing.com"),
        (
            {"fixed*more-fixed.thing.com"},
            "fixed-something-more-fixed.thing.com",
            "fixed-something-more-fixed.thing.com",
        ),
        ({"fixed*more-fixed.thing.com"}, "other-fixed*other.thing.com", None),
        ({"anything", "thing.com", "thing", "*thing", "thing*"}, "anything.com", None),
        ({"*thing*"}, "anything.com", "anything.com"),
    ],
)
def test_cors_matching(app, server, managed_workspace, allowed, origin, expected):
    """Test the `require_reader` decorator."""
    # Instruct app to use new allowed origins
    CORS(app, origins=regex_allowed_origins(allowed))

    # Make request and check header
    resp = server.get(
        f"/api/workspaces/{managed_workspace}", headers={"Origin": origin}
    )
    assert resp.headers.get("Access-Control-Allow-Origin") == expected
