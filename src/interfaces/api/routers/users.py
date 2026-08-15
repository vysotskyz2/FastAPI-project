from fastapi import APIRouter, Body, Depends, Path, Query, status

from src.application.services.user_service import UserService
from src.infrastructure.schemas import UserBrief, UserCreate, UserRead, UserUpdate
from src.interfaces.api.deps import get_user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead], status_code=status.HTTP_200_OK)
async def list_users(
    user_id: int | None = Query(default=None),
    email: str | None = Query(default=None),
    user_status: str | None = Query(default=None, alias="user_status"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    service: UserService = Depends(get_user_service),
) -> list[UserRead]:
    users = await service.list_users(user_id, email, user_status, limit, offset)
    return [UserRead.model_validate(user) for user in users]


@router.post("", response_model=UserBrief, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate = Body(...),
    service: UserService = Depends(get_user_service),
) -> UserBrief:
    user = await service.register(payload.email)
    return UserBrief.model_validate(user)


@router.patch("/{user_id}", response_model=UserBrief, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int = Path(gt=0),
    payload: UserUpdate = Body(...),
    service: UserService = Depends(get_user_service),
) -> UserBrief:
    user = await service.update_status(user_id, payload.status)
    return UserBrief.model_validate(user)
