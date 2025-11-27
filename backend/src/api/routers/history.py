from fastapi import APIRouter, Depends, Query, HTTPException

from api.dependencies.users import get_current_user
from core.history.history_service import HistoryService
from db.models.user_model import UserModel
from schemas.history import SimHistoryDetail, PaginatedSimHistoryList

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/", response_model=PaginatedSimHistoryList)
async def get_sim_history_list(
    user: UserModel = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Returns paginated short list of simulations for the user"""
    return await HistoryService.get_sim_history_list(user.id, page, page_size)


@router.get("/{simulation_id}", response_model=SimHistoryDetail)
async def get_simulation_history(simulation_id: int, user: UserModel = Depends(get_current_user)):
    """Returns simulation detail by simulation_id for the user"""
    try:
        return await HistoryService.get_sim_history_detail(user.id, simulation_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
