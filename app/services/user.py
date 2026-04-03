from fastapi import HTTPException

from app.models.user import User
from app.schemas.user import UserUpdateRequest


class UserService:
    @staticmethod
    async def get_user_by_id(user_id: int) -> User:
        user: User | None = await User.get_or_none(id=user_id).select_related("role")
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @staticmethod
    async def update_user(user_id: int, user_data: UserUpdateRequest | User) -> User:
        user: User = await UserService.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if isinstance(user_data, User):
            update_data = {
                "name": user_data.name,
                "email": user_data.email,
                "nickname": user_data.nickname,
                "gender": user_data.gender,
                "birthday": user_data.birthday,
                "birthyear": user_data.birthyear,
                "profile_image": user_data.profile_image,
            }
        else:
            update_data = user_data.model_dump(exclude_unset=True)
            
        for field, value in update_data.items():
            setattr(user, field, value)
        await user.save()
        return user

    @staticmethod
    async def delete_user(user_id: int) -> None:
        user: User = await UserService.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await user.delete()
