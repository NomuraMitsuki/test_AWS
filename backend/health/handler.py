import json


def handler(event, context):
    """API Gateway HTTP API (payload 2.0) health check. No auth."""
    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": json.dumps({"status": "ok"}),
    }
