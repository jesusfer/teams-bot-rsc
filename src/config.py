import os

""" Bot Configuration """


class DefaultConfig:
    """Bot Configuration"""

    PORT = int(os.environ.get("Port", "3978"))

    TENANT_ID = os.environ.get("MicrosoftAppTenantId")
    APP_ID = os.environ.get("MicrosoftAppId")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword")
    SCOPES = ["https://graph.microsoft.com/.default"]

    WEBHOOK_URL = os.environ.get("WebhookUrl")
    GRAPH_NOTIFICATION_EXPIRATION = int(
        os.environ.get("GraphNotificationExpiration", "1800")
    )  # 30 minutes in seconds

    # Should be static and secret. Used to validate the notification is coming from Graph
    GRAPH_WEBHOOK_STATE = os.environ.get("GraphWebhookState")

    # This is the application id from the Teams app catalog. Not the ID of the app in the manifest.
    MENTION_BOT_TEAMS_APP_ID = os.environ.get("MentionBotTeamsAppId")
    METION_BOT_ID = os.environ.get("MentionBotId")
    METION_BOT_NAME = os.environ.get("MentionBotName")
