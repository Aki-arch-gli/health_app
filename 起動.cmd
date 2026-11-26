@echo off
setlocal
cd /d "%~dp0"
set "KURASHI_PYTHON=python"
set "KURASHI_BUNDLED=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
set "KURASHI_RUNTIME=%LOCALAPPDATA%\Temp\kurashi-streamlit-167-py313"
if exist "%KURASHI_BUNDLED%" set "KURASHI_PYTHON=%KURASHI_BUNDLED%"
if exist "%KURASHI_RUNTIME%\streamlit\__init__.py" set "PYTHONPATH=%KURASHI_RUNTIME%;%PYTHONPATH%"
if exist ".streamlit-qa\streamlit\__init__.py" set "PYTHONPATH=%CD%\.streamlit-qa;%PYTHONPATH%"
"%KURASHI_PYTHON%" -c "import streamlit; assert tuple(int(x) for x in streamlit.__version__.split('.')[:2]) >= (1,67)" >nul 2>&1
if errorlevel 1 (
  echo Installing the packages in requirements.txt.
  "%KURASHI_PYTHON%" -m pip install -r requirements.txt --target "%KURASHI_RUNTIME%"
  if errorlevel 1 goto :error
  set "PYTHONPATH=%KURASHI_RUNTIME%;%PYTHONPATH%"
)
"%KURASHI_PYTHON%" -m streamlit run app.py --server.address 127.0.0.1
if errorlevel 1 goto :error
exit /b 0
:error
echo Could not start the app. See README.md for the manual start command.
pause
exit /b 1
