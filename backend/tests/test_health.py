import json

from handler import handler


def test_health_returns_200_and_ok():
    response = handler({}, None)

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"status": "ok"}
