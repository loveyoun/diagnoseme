from enum import StrEnum

from tortoise import fields

from app.models.common import Common


class Gender(StrEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    UNKNOWN = "UNKNOWN"


class User(Common):
    user_id = fields.BigIntField(primary_key=True)
    nickname = fields.CharField(max_length=10)
    email = fields.CharField(max_length=40, null=True)
    gender = fields.CharEnumField(enum_type=Gender, default=Gender.UNKNOWN)

    # 네이버 식별자
    naver_id = fields.CharField(max_length=100, unique=True)

    # 네이버 제공 정보
    name = fields.CharField(max_length=100, null=True)  # 회원 이름
    email = fields.CharField(max_length=255, null=True)  # 연락처 이메일
    nickname = fields.CharField(max_length=100, null=True)  # 별명
    gender = fields.CharField(max_length=1, null=True)  # 성별 (M/F/U)
    birthday = fields.CharField(max_length=5, null=True)  # 생일 (MM-DD)
    birthyear = fields.CharField(max_length=4, null=True)  # 출생연도 (YYYY)
    profile_image = fields.CharField(max_length=500, null=True)  # 프로필 사진 URL

    class Meta:
        table = "users"
