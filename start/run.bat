@echo off
rem ============================================================
rem  Ponto de entrada chamado pelo Agendador de Tarefas (10 min)
rem  Ativa o venv e roda o orquestrador uma vez.
rem  (Implementacao real do main = Fase 5)
rem ============================================================

set "PROJECT_DIR=%~dp0.."
cd /d "%PROJECT_DIR%"

call "%PROJECT_DIR%\venv\Scripts\activate.bat"

python -m src.main

exit /b %ERRORLEVEL%
