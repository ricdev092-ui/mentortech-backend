#!/bin/bash

echo "🚀 A iniciar os microsserviços do MentorTech..."

# 1. Iniciar AI Service (Porta 8001)
echo "🤖 A ligar AI Service (Porta 8001)..."
cd ~/mentortech-backend/ai_service
source .venv/bin/activate
nohup uvicorn main:app --port 8001 > ai_service.log 2>&1 &

# 2. Iniciar Client Service (Porta 8002)
echo "💾 A ligar Client Service (Porta 8002)..."
cd ~/mentortech-backend/client_service
source .venv/bin/activate
nohup uvicorn main:app --port 8002 > client_service.log 2>&1 &

# 3. Iniciar Gateway (Porta 8000)
echo "🌐 A ligar API Gateway (Porta 8000)..."
cd ~/mentortech-backend/gateway
source .venv/bin/activate
nohup uvicorn main:app --port 8000 > gateway.log 2>&1 &

cd ~/mentortech-backend
echo "✅ Todos os serviços estão a rodar em segundo plano!"
echo "📍 Acede ao Swagger em: http://localhost:8000/docs"
