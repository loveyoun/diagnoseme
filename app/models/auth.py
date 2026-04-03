from tortoise import fields, models

from app.models.common import Common


class AuthProvider(models.Model):
    id: int = fields.SmallIntField(primary_key=True)
    code: str = fields.CharField(max_length=20, unique=True)

    class Meta:
        table = "auth_providers"


class SocialAccount(Common):
    id: int = fields.BigIntField(primary_key=True)
    user:int= fields.ForeignKeyField("models.User", related_name="social_accounts", on_delete=fields.CASCADE)
    provider: int = fields.ForeignKeyField("models.AuthProvider", related_name="social_accounts", on_delete=fields.CASCADE)
    external_id: str = fields.CharField(max_length=255)

    class Meta:
        table = "social_accounts"
        unique_together = (
            ("user", "provider"),
            ("provider", "external_id"),
        )

