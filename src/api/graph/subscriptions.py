"""
This module handles Microsoft Graph webhook subscriptions for chat messages.
"""

import functools
import html
import urllib
from http import HTTPStatus

from aiohttp.web import Request, Response

from api.decorators import ensure_qs
from config import DefaultConfig
from utils.graph import Graph

CONFIG = DefaultConfig()

"""
Relevant documentation:

https://learn.microsoft.com/en-us/graph/change-notifications-lifecycle-events
https://learn.microsoft.com/en-us/graph/change-notifications-delivery-webhooks?tabs=python
https://learn.microsoft.com/en-us/graph/change-notifications-with-resource-data
"""


def validate_token(func):
    """Decorator to validate the token when Graph sends a validation request."""

    @functools.wraps(func)
    async def wrapper(request, *args, **kwargs):
        validation_token = request.query.get("validationToken", None)
        if validation_token:
            print(f"Decoded URL: {validation_token}")
            validation_token = urllib.parse.unquote(validation_token)
            validation_token = html.escape(validation_token)
            return Response(
                status=HTTPStatus.OK, content_type="text/plain", text=validation_token
            )
        return await func(request, *args, **kwargs)

    return wrapper


def validate_notification(func):
    """Decorator to validate the notification's client state to ensure it's coming from Graph."""

    @functools.wraps(func)
    async def wrapper(notification, *args, **kwargs):
        if notification["clientState"] != CONFIG.GRAPH_WEBHOOK_STATE:
            print(f"Invalid client state: {notification['clientState']}")
            return Response(
                status=HTTPStatus.UNAUTHORIZED,
                text="Invalid client state",
            )
        return await func(notification, *args, **kwargs)

    return wrapper


@ensure_qs("chat_id")
async def create_chat_messages_subscription(req: Request) -> Response:
    """Create a subscription to receive updates when a chat has new messages."""
    chat_id = req.query.get("chat_id")
    print(f"\nAPI: Creating subscription for chat: {chat_id}")
    graph = Graph()
    await graph.create_chat_messages_subscription(chat_id)
    return Response(
        status=HTTPStatus.OK,
        content_type="text/plain",
        text=f"Created subscription for chat: {chat_id}",
    )


@ensure_qs("chat_id")
async def delete_chat_messages_subscription(req: Request) -> Response:
    """Delete a subscription to a chat's messages."""
    chat_id = req.query.get("chat_id")
    print(f"\nAPI: Deleting subscription for chat: {chat_id}")
    graph = Graph()
    ret = await graph.delete_chat_messages_subscription(chat_id)
    if ret:
        print(f"\nAPI: Deleted subscription for chat: {chat_id}")
        return Response(
            status=HTTPStatus.OK,
            content_type="text/plain",
            text=f"Deleted subscription for chat: {chat_id}",
        )
    else:
        print(f"\nAPI: No subscription found for chat: {chat_id}")
        return Response(
            status=HTTPStatus.NOT_FOUND,
            content_type="text/plain",
            text=f"No subscription found for chat: {chat_id}",
        )


@ensure_qs("chat_id")
async def list_chat_messages_subscription(req: Request) -> Response:
    """List all subscriptions (at most one IRL)."""
    chat_id = req.query.get("chat_id")
    graph = Graph()
    subscription = await graph.list_chat_messages_subscription(chat_id)
    if subscription:
        return Response(
            status=HTTPStatus.OK,
            content_type="application/json",
            text=f"Found a subscription with ID {subscription.id}",
        )
    else:
        return Response(
            status=HTTPStatus.NOT_FOUND,
            content_type="text/plain",
            text="No subscriptions found",
        )


@validate_token
async def get_notifications(req: Request) -> Response:
    """Handle Graph notifications."""
    body = await req.json()
    if not body:
        return Response(
            status=HTTPStatus.BAD_REQUEST, text="No notification data provided"
        )
    # Process the notification data
    if "value" in body:
        for notification in body["value"]:
            await _process_notification(notification)
    else:
        # If the body does not contain 'value', log the entire body
        # This is useful for debugging unexpected notification formats
        print(f"\nAPI: Received unexpected Graph notification format: {body}")

    return Response(status=HTTPStatus.OK)


@validate_notification
async def _process_notification(notification):
    """Process a single Graph notification."""
    # Here you can add logic to handle the notification
    # For example, you might want to queue it for processing
    # print(f"\nAPI: Processing notification: {notification}")
    data = notification["resourceData"]
    if (
        notification["changeType"] == "created"
        and data.get("@odata.type") == "#Microsoft.Graph.chatMessage"
    ):
        # Assuming resourceData contains the relevant data for the notification
        print(f"\nAPI: New message id: {data.get('id')}")
    else:
        print(f"\nAPI: Received Graph notification: {notification}")


@validate_token
async def get_lifecycle_notifications(req: Request) -> Response:
    """Handle Graph lifecycle notifications"""
    body = await req.json()
    if not body:
        return Response(
            status=HTTPStatus.BAD_REQUEST, text="No notification data provided"
        )
    # Process the notification data
    print(f"\nAPI: Received Graph notification: {body}")
    # Process the notification data
    if "value" in body:
        for notification in body["value"]:
            # Process each lifecycle notification
            await _process_lifecycle_notification(notification)
    else:
        # If the body does not contain 'value', log the entire body
        # This is useful for debugging unexpected notification formats
        print(f"\nAPI: Received unexpected Graph lifecycle notification format: {body}")
    return Response(status=HTTPStatus.ACCEPTED)


@validate_notification
async def _process_lifecycle_notification(notification):
    """Process a single Graph lifecycle notification."""
    # Here you can add logic to handle the lifecycle notification
    # For example, you might want to queue it for processing
    print(f"\nAPI: Processing lifecycle notification: {notification}")
    if notification["lifecycleEvent"] == "reauthorizationRequired":
        print(
            f"Reauthorization required for notification: {notification['subscriptionId']}"
        )
        graph = Graph()
        await graph.reauthorize_subscription(notification["subscriptionId"])
    else:
        print(f"\nAPI: Received Graph lifecycle notification: {notification}")
