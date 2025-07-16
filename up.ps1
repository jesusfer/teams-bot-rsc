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


$env:NotificationKeyId = "dcedeb67698004357a499..."
$env:NotificationPublicKey = "MIIDFjCCAf6gAwIBAgIQE...""
$env:NotificationPrivateKey = "MIIEvwIBADANBgkqhkiG9..."
.\.venv\Scripts\Activate.ps1

python .\src\app.py
