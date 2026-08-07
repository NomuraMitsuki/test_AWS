"""共通 Error JSON とアプリケーション例外。"""


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def error_body(code: str, message: str, request_id: str) -> dict:
    return {"code": code, "message": message, "request_id": request_id}
