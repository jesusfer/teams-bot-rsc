"""API handler to print out some information about a chat."""

from http import HTTPStatus

from aiohttp.web import Request, Response

from api.decorators import ensure_qs
from utils.graph import Graph


@ensure_qs("chat_id")
async def chat_info(req: Request) -> Response:
    chat_id = req.query.get("chat_id")
    print(f"Info for chat ID: {chat_id}")

    graph: Graph = Graph()
    await graph.display_chat_permissions(chat_id)
    await graph.list_chat_members(chat_id)
    await graph.list_chat_bots(chat_id)
    await graph.list_chat_messages(chat_id)
    return Response(status=HTTPStatus.OK)
