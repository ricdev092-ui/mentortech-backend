import os
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import passlib.context
import jwt
import httpx

# Configurações gerais
DATABASE_URL = "sqlite:///./mentortech.db"
SECRET_KEY = os.getenv("JWT_SECRET", "super_secret_key_mentortech_2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Modelos do Banco de Dados
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)

class MentoringHistory(Base):
    __tablename__ = "mentoring_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MentorTech - Client Service", version="2.0.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utilitários
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user_id(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return int(user_id)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

# Schemas Pydantic
class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str | None = None

class MentoringRequest(BaseModel):
    message: str

# Endpoints
@app.post("/register")
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    
    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        full_name=user.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "email": new_user.email, "message": "Usuário criado com sucesso!"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/mentoring")
async def mentoring_session(
    payload: MentoringRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AI_SERVICE_URL}/generate",
                json={"prompt": payload.message},
                timeout=30.0
            )
            ai_data = response.json()
            ai_text = ai_data.get("response", "Sem resposta da IA")
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Erro ao chamar AI Service: {str(exc)}")

    # Salva no histórico
    history_entry = MentoringHistory(
        user_id=user_id,
        user_message=payload.message,
        ai_response=ai_text
    )
    db.add(history_entry)
    db.commit()

    return {"question": payload.message, "answer": ai_text}

# NOVO ENDPOINT: Buscar Histórico do Usuário
@app.get("/history")
def get_user_history(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    history = db.query(MentoringHistory).filter(MentoringHistory.user_id == user_id).all()
    return [
        {
            "id": item.id,
            "question": item.user_message,
            "answer": item.ai_response,
            "date": item.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for item in history
    ]
