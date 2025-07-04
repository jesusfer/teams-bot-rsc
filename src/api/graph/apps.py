"""API endpoint to add a bot to a chat."""

from http import HTTPStatus

from aiohttp.web import Request, Response

from api.decorators import ensure_qs
from utils.graph import Graph


@ensure_qs("chat_id")
async def add_bot(req: Request) -> Response:
    """Add a bot to a chat."""
    chat_id = req.query.get("chat_id")
    print(f"\nAPI: Add bot in chat ID: {chat_id}")

    graph: Graph = Graph()
    await graph.add_bot_to_chat(chat_id)
    return Response(status=HTTPStatus.OK)
