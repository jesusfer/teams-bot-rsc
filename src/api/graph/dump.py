"""API endpoint to dump to console the access token for debugging purposes."""

from http import HTTPStatus

from aiohttp.web import Request, Response

from api.decorators import ensure_qs
from utils.graph import Graph


async def dump_token(req: Request) -> Response:
    graph: Graph = Graph()
    await graph.display_access_token()
    return Response(status=HTTPStatus.ACCEPTED)
