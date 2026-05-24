@echo off
title Resetar Banco - Verificação
cd /d "%~dp0"
echo ========================================
echo  Resetando banco de dados...
echo ========================================
curl -s -X POST https://verificar-gi0k.onrender.com/api/reset
echo.
echo  Pronto! Banco resetado.
echo  Pode testar de novo.
echo ========================================
pause
