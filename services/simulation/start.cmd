@echo off
py -3.12 "%~dp0run.py" %*
exit /b %errorlevel%
