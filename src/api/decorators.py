from functools import wraps
from http import HTTPStatus
from typing import Callable

from aiohttp.web import Request, Response


def ensure_qs(*params):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request) -> Response:
            for param in params:
                if param not in request.query:
                    return Response(
                        status=HTTPStatus.BAD_REQUEST,
                        text=f"API: Missing '{param}' query parameter",
                    )
            return await func(request)

        return wrapper

    return decorator
