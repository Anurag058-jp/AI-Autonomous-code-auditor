from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .service import AuditService

app = FastAPI(title="Zero-Cost Code Auditor", version="0.1.0")


class ScanRequest(BaseModel):
    path: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scans")
def create_scan(request: ScanRequest):
    try:
        return AuditService().scan(request.path)
    except ValueError as error:
        raise HTTPException(400, str(error)) from error


@app.get("/scans/{scan_id}")
def read_scan(scan_id: str):
    try:
        return AuditService().get_scan(scan_id)
    except ValueError as error:
        raise HTTPException(404, str(error)) from error


@app.post("/scans/{scan_id}/issues/{issue_id}/{action}")
def generate(scan_id: str, issue_id: str, action: str):
    if action not in {"fix", "test"}:
        raise HTTPException(400, "action must be fix or test")
    try:
        return {"draft": AuditService().generate(scan_id, issue_id, action)}
    except (ValueError, RuntimeError) as error:
        raise HTTPException(400, str(error)) from error


def run():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

