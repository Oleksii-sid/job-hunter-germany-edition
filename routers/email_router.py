from fastapi import APIRouter
from pydantic import BaseModel
from services.email_service import send_email

router = APIRouter(prefix="/email", tags=["email"])


class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str


@router.post("/send-test")
async def send_test_email(data: EmailRequest):
    await send_email(data.to, data.subject, data.body)
    return {"status": "email sent"}