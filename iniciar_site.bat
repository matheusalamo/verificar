@echo off
title Site - Verificação Discord
cd /d "%~dp0"
echo ========================================
echo  Iniciando servidor do site...
echo  Acesse: http://localhost:8000
echo  Pressione CTRL+C para parar
echo ========================================
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
pause
