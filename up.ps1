param(
    $botId
)

switch ($botId) {
    Default {
        $env:Port = "3978"
        $env:MicrosoftAppTenantId = ""
        $env:MicrosoftAppId = ""
        $env:MicrosoftAppPassword = ""

        $env:WebhookUrl = ""
        $env:GraphNotificationExpiration = ""
        $env:GraphWebhookState = ""

        $env:MentionBotTeamsAppId = ""
        $env:MentionBotId = ""
        $env:MentionBotName = ""
    }
}

.\.venv\Scripts\Activate.ps1

python .\src\app.py
