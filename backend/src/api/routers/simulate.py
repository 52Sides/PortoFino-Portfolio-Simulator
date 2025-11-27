from fastapi import APIRouter, Depends, HTTPException

from api.dependencies.users import get_current_user
from core.simulation.simulation_service import SimulationService
from db.models.user_model import UserModel
from schemas.simulation import SimulateRequest, SimulateResponse

router = APIRouter(prefix="/simulate", tags=["Simulation"])


@router.post("/", response_model=SimulateResponse)
async def simulate(request: SimulateRequest, user: UserModel = Depends(get_current_user)):
    """Creates a simulation task and submits it for processing"""
    try:
        return await SimulationService.create_simulation(request.command, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
