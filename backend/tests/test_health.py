import json

from lambda_loader import import_lambda


def test_health_returns_200_and_ok():
    handler = import_lambda("health").handler
    response = handler({}, None)

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"status": "ok"}
