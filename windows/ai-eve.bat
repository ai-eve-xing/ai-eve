@echo off
REM ai-eve.bat — AI 夏娃 启动入口
cd /d "%~dp0"
python -m cli.main %*
