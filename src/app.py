from aiohttp import web
from botbuilder.core.integration import aiohttp_error_middleware

from api.graph import *
from bots.adapter import messages
from config import DefaultConfig

CONFIG = DefaultConfig()

APP = web.Application(middlewares=[aiohttp_error_middleware])
APP.router.add_post("/api/messages", messages)

APP.router.add_get("/api/dump_token", dump_token)

APP.router.add_get("/api/chat_info", chat_info)

APP.router.add_get("/api/bots/add", add_bot)

APP.router.add_post("/api/subs/hook", get_notifications)
APP.router.add_post("/api/subs/lf", get_lifecycle_notifications)

APP.router.add_get("/api/subs/messages", list_chat_messages_subscription)
APP.router.add_get("/api/subs/messages/new", create_chat_messages_subscription)
APP.router.add_get("/api/subs/messages/delete", delete_chat_messages_subscription)

if __name__ == "__main__":
    try:
        web.run_app(APP, host="localhost", port=CONFIG.PORT)
    except Exception as error:
        raise error
