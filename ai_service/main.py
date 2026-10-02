import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="MentorTech - AI Service")

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class GeneratePayload(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_response(payload: GeneratePayload):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY não encontrada no arquivo .env")
        
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Você é um mentor especialista em tecnologia e programação. Responda de forma clara, prática e motivadora em português."
                },
                {
                    "role": "user",
                    "content": payload.prompt
                }
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        
        answer = completion.choices[0].message.content
        return {"response": answer}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na Groq API: {str(e)}")
