from fastapi import APIRouter, Depends, HTTPException

from api.dependencies.users import get_current_user
from core.report.report_service import ReportService
from db.models.user_model import UserModel
from schemas.report import ReportRequest, ReportResponse

router = APIRouter(prefix="/report", tags=["Report"])


@router.post("/", response_model=ReportResponse)
async def create_report(request: ReportRequest, user: UserModel = Depends(get_current_user)):
    """Creates a report task and submits it for processing"""
    try:
        return await ReportService.create_report(request.simulation_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
