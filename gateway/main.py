import os
import httpx
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="MentorTech - API Gateway", version="2.0.0")

CLIENT_SERVICE_URL = os.getenv("CLIENT_SERVICE_URL", "http://localhost:8002")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")

security = HTTPBearer()

class UserRegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str | None = None

class UserLoginRequest(BaseModel):
    username: str
    password: str

class MentoringGatewayRequest(BaseModel):
    message: str

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "api_gateway",
        "targets": {
            "client_service": CLIENT_SERVICE_URL,
            "ai_service": AI_SERVICE_URL
        }
    }

# 1. Registro
@app.post("/api/v1/auth/register")
async def proxy_register(payload: UserRegisterRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{CLIENT_SERVICE_URL}/register",
                json=payload.model_dump(),
                timeout=15.0
            )
            try:
                content = response.json()
            except Exception:
                content = {"detail": response.text}
            return JSONResponse(status_code=response.status_code, content=content)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação: {str(exc)}")

# 2. Login
@app.post("/api/v1/auth/login")
async def proxy_login(payload: UserLoginRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{CLIENT_SERVICE_URL}/login",
                data={"username": payload.username, "password": payload.password},
                timeout=15.0
            )
            try:
                content = response.json()
            except Exception:
                content = {"detail": response.text}
            return JSONResponse(status_code=response.status_code, content=content)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação: {str(exc)}")

# 3. Mentoria
@app.post("/api/v1/mentoring")
async def proxy_mentoring(
    payload: MentoringGatewayRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    headers = {"Authorization": f"Bearer {credentials.credentials}"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{CLIENT_SERVICE_URL}/mentoring",
                json=payload.model_dump(),
                headers=headers,
                timeout=35.0
            )
            try:
                content = response.json()
            except Exception:
                content = {"detail": response.text}
            return JSONResponse(status_code=response.status_code, content=content)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação: {str(exc)}")

# 4. Histórico (Protegido)
@app.get("/api/v1/mentoring/history")
async def proxy_history(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    headers = {"Authorization": f"Bearer {credentials.credentials}"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{CLIENT_SERVICE_URL}/history",
                headers=headers,
                timeout=15.0
            )
            try:
                content = response.json()
            except Exception:
                content = {"detail": response.text}
            return JSONResponse(status_code=response.status_code, content=content)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro de comunicação: {str(exc)}")
