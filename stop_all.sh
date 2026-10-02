#!/bin/bash

echo "🛑 A desligar todos os microsserviços..."
pkill -f uvicorn
echo "✅ Todos os serviços foram desligados!"
