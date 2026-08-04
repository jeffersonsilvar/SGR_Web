@echo off
title SGR Web - Servidor Local
cd /d "C:\Users\Jefferson Silva\Documents\SGR Web"
call .venv\Scripts\activate
echo Iniciando SGR Web...
echo Acesse: http://127.0.0.1:8080
python app.py
pause