from pydantic import BaseModel


class ReportRequest(BaseModel):
    simulation_id: int


class ReportResponse(BaseModel):
    task_id: str
    status: str = "queued"
