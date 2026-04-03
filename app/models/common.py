from datetime import datetime

from tortoise import fields, models


class Common(models.Model):
    created_at: datetime = fields.DatetimeField(auto_now_add=True)
    updated_at: datetime = fields.DatetimeField(auto_now=True)
    deleted_at: datetime | None = fields.DatetimeField(null=True)  # soft delete 대비용

    class Meta:
        abstract = True
        ordering = ['-created_at']
