from tortoise import fields, models
from app.models.common import Common


class AuthProvider(models.Model):
    id = fields.SmallIntField(primary_key=True)
    code = fields.CharField(max_length=20, unique=True)

    class Meta:
        table = "auth_providers"


class SocialAccount(Common):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="social_accounts", on_delete=fields.CASCADE)
    provider = fields.ForeignKeyField("models.AuthProvider", on_delete=fields.CASCADE)
    external_id = fields.CharField(max_length=255)

    class Meta:
        table = "social_accounts"
        unique_together = (("user", "provider"),)  # 동일 소셜계정 중복 방지
