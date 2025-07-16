"""
This module provides a class to interact with the Microsoft Graph API using app-only authentication.
It includes methods for managing subscriptions, listing chat members and bots, and handling chat messages.
"""

from datetime import datetime, timedelta, timezone

from azure.identity.aio import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.chats.chats_request_builder import ChatsRequestBuilder
from msgraph.generated.models.subscription import Subscription
from msgraph.generated.models.teams_app_installation import TeamsAppInstallation
from msgraph.generated.models.teams_app_permission_set import TeamsAppPermissionSet
from msgraph.generated.models.teams_app_resource_specific_permission import (
    TeamsAppResourceSpecificPermission,
)
from msgraph.generated.models.teams_app_resource_specific_permission_type import (
    TeamsAppResourceSpecificPermissionType,
)

from config import DefaultConfig

CONFIG = DefaultConfig()

"""
Relevant documentation:
https://learn.microsoft.com/en-us/microsoftteams/platform/graph-api/rsc/resource-specific-consent
https://learn.microsoft.com/en-us/microsoftteams/platform/graph-api/rsc/grant-resource-specific-consent
https://learn.microsoft.com/en-us/graph/api/resources/teams-api-overview?view=graph-rest-1.0

https://learn.microsoft.com/en-us/graph/change-notifications-lifecycle-events
https://learn.microsoft.com/en-us/graph/teams-changenotifications-chatmessage#subscribe-to-messages-in-a-chat
https://learn.microsoft.com/en-us/graph/api/chat-post-installedapps?view=graph-rest-1.0&tabs=python

"""


class Graph:
    """A class to interact with Microsoft Graph API using app-only authentication."""

    client_credential: ClientSecretCredential
    app_client: GraphServiceClient

    def __init__(self):
        tenant_id = CONFIG.TENANT_ID
        client_id = CONFIG.APP_ID
        client_secret = CONFIG.APP_PASSWORD

        self.client_credential = ClientSecretCredential(
            tenant_id, client_id, client_secret
        )
        self.app_client = GraphServiceClient(self.client_credential)

    async def get_app_only_token(self):
        graph_scope = "https://graph.microsoft.com/.default"
        access_token = await self.client_credential.get_token(graph_scope)
        return access_token.token

    async def display_access_token(self):
        token = await self.get_app_only_token()
        print(f"Graph: App-only token: {token}\n")

    async def display_chat_permissions(self, chat_id: str):
        permissions = await self.app_client.chats.by_chat_id(
            chat_id=chat_id
        ).permission_grants.get()
        for permission in permissions.value:
            print(
                f"Graph: Permission: {permission.permission}, Scope: {permission.permission_type}"
            )

    async def list_chat_members(self, chat_id: str):
        # Members don't include bots/agents
        members = await self.app_client.chats.by_chat_id(chat_id=chat_id).members.get()
        for member in members.value:
            print(f"Graph: Member: {member.odata_type}, Name: {member.display_name}")

    async def list_chat_bots(self, chat_id: str):
        params = ChatsRequestBuilder.ChatsRequestBuilderGetQueryParameters(
            expand=["teamsAppDefinition($expand=bot)"],  # Expand to include bot details
        )
        request = ChatsRequestBuilder.ChatsRequestBuilderGetRequestConfiguration(
            query_parameters=params
        )
        apps = await self.app_client.chats.by_chat_id(
            chat_id=chat_id
        ).installed_apps.get(request_configuration=request)
        for app in apps.value:
            definition = app.teams_app_definition
            if app.teams_app_definition.bot:
                bot = app.teams_app_definition.bot
                print(
                    f"Graph: App: {definition.display_name}, ID: {definition.id}, "
                    f"Version: {definition.version} "
                    f"Bot ID: {bot.id}"
                )

    async def list_chat_messages(self, chat_id: str):
        params = ChatsRequestBuilder.ChatsRequestBuilderGetQueryParameters(
            top=10,  # Adjust as needed
            filter=None,  # Add any filter if required
            orderby=None,  # Add any ordering if required
        )
        request = ChatsRequestBuilder.ChatsRequestBuilderGetRequestConfiguration(
            query_parameters=params
        )
        messages = await self.app_client.chats.by_chat_id(chat_id=chat_id).messages.get(
            request_configuration=request
        )
        for message in messages.value:
            print(f"Graph: Message: {message.id}, Content: {message.body.content}")
            for mention in message.mentions:
                if mention.mentioned.application:
                    print(
                        f"Graph: Mentioned: {mention.mentioned.application.display_name} ({mention.mentioned.application.id})"
                    )
                if mention.mentioned.user:
                    print(f"Graph: Mentioned: {mention.mentioned.user.display_name}")

    async def subscription_create(
        self,
        resource: str,
        change_type: str,
        notification_url: str = CONFIG.WEBHOOK_URL + "/api/subs/hook",
        lifecycle_url: str = CONFIG.WEBHOOK_URL + "/api/subs/lf",
        expiration_in_seconds: int = CONFIG.GRAPH_NOTIFICATION_EXPIRATION,
    ) -> Subscription:
        subscriptions = await self.app_client.subscriptions.get()
        for subscription in subscriptions.value:
            if subscription.resource == resource:
                print(f"Graph: Subscription already exists: {subscription.id}")
                return subscription

        expiration = datetime.now(tz=timezone.utc) + timedelta(
            seconds=expiration_in_seconds
        )
        subscription = Subscription(
            change_type=change_type,
            notification_url=notification_url,
            lifecycle_notification_url=lifecycle_url,
            resource=resource,
            expiration_date_time=expiration.isoformat(),
            client_state=CONFIG.GRAPH_WEBHOOK_STATE,
            include_resource_data=True,
            encryption_certificate=CONFIG.NOTIFICATION_PUBLIC_KEY,
            encryption_certificate_id=CONFIG.NOTIFICATION_KEY_ID,
        )
        created_subscription = await self.app_client.subscriptions.post(subscription)
        print(
            f"Graph: Created subscription {created_subscription.id} until {created_subscription.expiration_date_time}"
        )
        return created_subscription

    async def subscription_delete(self, resource: str) -> Subscription | None:
        subscriptions = await self.app_client.subscriptions.get()
        for subscription in subscriptions.value:
            if subscription.resource == resource:
                await self.app_client.subscriptions.by_subscription_id(
                    subscription.id
                ).delete()
                print(f"Graph: Deleted subscription: {subscription.id}")
                return subscription
        print(f"Graph: No matching subscription found to delete.")

    async def subscription_reauthorize(
        self,
        subscription_id: str,
        expiration_in_seconds: int = CONFIG.GRAPH_NOTIFICATION_EXPIRATION,
    ) -> Subscription | None:
        subscription = await self.app_client.subscriptions.by_subscription_id(
            subscription_id
        ).get()
        if subscription:
            print(f"Graph: Reauthorizing subscription: {subscription.id}")
            expiration = datetime.now(tz=timezone.utc) + timedelta(
                seconds=expiration_in_seconds
            )
            renew_subscription = Subscription(
                expiration_date_time=expiration.isoformat()
            )
            updated_subscription = (
                await self.app_client.subscriptions.by_subscription_id(
                    subscription.id
                ).patch(renew_subscription)
            )
            print(
                f"Graph: Reauthorized subscription {subscription.id} "
                f"until {updated_subscription.expiration_date_time}"
            )
        else:
            print(f"Graph: No subscription found with ID: {subscription_id}")

    async def create_chat_messages_subscription(self, chat_id: str):
        resource = f"/chats/{chat_id}/messages"
        change_type = "created"
        return await self.subscription_create(resource, change_type)

    async def delete_chat_messages_subscription(self, chat_id: str):
        resource = f"/chats/{chat_id}/messages"
        return await self.subscription_delete(resource)

    async def list_chat_messages_subscription(self, chat_id: str) -> None:
        resource = f"/chats/{chat_id}/messages"
        subscriptions = await self.app_client.subscriptions.get()
        for subscription in subscriptions.value:
            if subscription.resource == resource:
                print(
                    f"Graph: Found subscription: {subscription.id} until {subscription.expiration_date_time}"
                )
                return subscription
        print(f"Graph: No matching subscription found.")

    async def add_bot_to_chat(self, chat_id: str) -> None:
        """Add a bot to a chat that requests resource specific permissions."""
        # Works with RSC Chat.Manage.Chat permission and Graph's TeamsAppInstallation.ManageSelectedForChat.All.
        # Not sure how to select which apps can be managed.
        # Copilot suggests that the managing app should be the one in the webApplicationInfo in the
        # managed app manifest, but that'd break SSO in the managed app if it were true.

        teams_app_id = CONFIG.MENTION_BOT_TEAMS_APP_ID

        request_body = TeamsAppInstallation(
            consented_permission_set=TeamsAppPermissionSet(
                resource_specific_permissions=[
                    # Permisions from the bot's manifest
                    TeamsAppResourceSpecificPermission(
                        permission_value="Chat.Manage.Chat",
                        permission_type=TeamsAppResourceSpecificPermissionType.Application,
                    ),
                    TeamsAppResourceSpecificPermission(
                        permission_value="TeamsAppInstallation.Read.Chat",
                        permission_type=TeamsAppResourceSpecificPermissionType.Application,
                    ),
                    TeamsAppResourceSpecificPermission(
                        permission_value="ChatMember.Read.Chat",
                        permission_type=TeamsAppResourceSpecificPermissionType.Application,
                    ),
                    TeamsAppResourceSpecificPermission(
                        permission_value="ChatMessage.Read.Chat",
                        permission_type=TeamsAppResourceSpecificPermissionType.Application,
                    ),
                ],
            ),
            additional_data={
                "teamsApp@odata.bind": f"https://graph.microsoft.com/v1.0/appCatalogs/teamsApps/{teams_app_id}",
            },
        )

        await self.app_client.chats.by_chat_id(chat_id).installed_apps.post(
            request_body
        )
