from fastapi import APIRouter, status

from app.models.user import User
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int) -> UserResponse:
    return await UserService.get_user_by_id(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdateRequest) -> UserResponse:
    return await UserService.update_user(user_id, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int) -> None:
    await UserService.delete_user(user_id)
    return None
