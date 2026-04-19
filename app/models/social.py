from typing import TYPE_CHECKING

from tortoise import fields

from app.models.commonmodel import CommonModel

if TYPE_CHECKING:
    from app.models import User


class AuthProvider(CommonModel):
    id: int = fields.SmallIntField(primary_key=True)
    code: str = fields.CharField(max_length=10, unique=True)

    class Meta:
        table = "auth_providers"


class SocialAccount(CommonModel):
    id: int = fields.BigIntField(primary_key=True)
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User",
        related_name="social_accounts",
        on_delete=fields.CASCADE)
    provider: fields.ForeignKeyRelation[AuthProvider] = fields.ForeignKeyField(
        "models.AuthProvider",
        related_name="social_accounts",
        on_delete=fields.CASCADE)
    external_id: str = fields.CharField(max_length=255)

    user_id: int
    provider_id: int

    class Meta:
        table = "social_accounts"
        unique_together = (
            ("user", "provider"),  # 소셜당 한 개만
            ("provider", "external_id"),  # provider 당 unique
        )
