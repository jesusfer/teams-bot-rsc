import jwt

from config import DefaultConfig

CONFIG = DefaultConfig()


def validate_token(token: str) -> bool:
    """Validates the JWT token signature and checks the appid."""
    # https://learn.microsoft.com/en-us/graph/change-notifications-with-resource-data#how-to-validate

    discovery_url = f"https://login.microsoftonline.com/common/discovery/keys"
    jwks_client = jwt.PyJWKClient(discovery_url)
    key = jwks_client.get_signing_key_from_jwt(token)

    try:
        payload = jwt.decode(
            token,
            key=key,
            algorithms=["RS256"],
            audience=CONFIG.APP_ID,
            verify=True,
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iat": True,
                "verify_nbf": True,
                "verify_exp": True,
            },
        )
        # 0bf30f3b-4a52-48df-9a82-234910c4a086 represents the Microsoft Graph change notification publisher
        if payload.get("appid") != "0bf30f3b-4a52-48df-9a82-234910c4a086":
            print(f"Invalid appid in token: {payload.get('appid')}")
            return False
        return True
    except Exception as e:
        print(f"Error validating token: {e}")
        return False
