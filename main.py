import io
from fastapi import FastAPI,Depends,BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from db import get_db
from model import Menu_hours, Store_status, Timezone,Report
from utils import store_csv_to_db,generate_report
from datetime import datetime, timedelta
import uuid
app= FastAPI()
# Allow CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/jii")
def read_root(id: str, start: datetime, end: datetime, db=Depends(get_db)):
    query = db.query(Store_status).filter(
        Store_status.store_id == id,
        Store_status.timestamp_utc >= start,
        Store_status.timestamp_utc <= end
    ).all()
    return query

@app.get("/trigger")
def trigger_report(db=Depends(get_db), background_tasks: BackgroundTasks = None):
    report_id=uuid.uuid4()
    background_tasks.add_task(generate_report, report_id=report_id, db=db)
    return {"report_id": str(report_id)}

@app.get("/report/{report_id}")
def get_report(report_id: uuid.UUID, db=Depends(get_db)):
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if report.status == 'Running':
        return {"message": "Report is still being generated."}
    elif report.status == 'Completed':
        return StreamingResponse(io.BytesIO(report.file), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=report_{report_id}.csv"})