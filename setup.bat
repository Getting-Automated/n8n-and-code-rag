@echo off
ECHO Setting up n8n RAG example environment...

:: Check for Python
python --version > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Python is not installed or not in PATH. Please install Python 3.9+.
    EXIT /B 1
)

:: Create virtual environment
IF NOT EXIST venv (
    ECHO Creating virtual environment...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        ECHO Failed to create virtual environment.
        EXIT /B 1
    )
)

:: Activate virtual environment
ECHO Activating virtual environment...
CALL venv\Scripts\activate

:: Install requirements
ECHO Installing dependencies...
pip install -U pip setuptools wheel
pip install -r requirements.txt

:: Create config directory if it doesn't exist
IF NOT EXIST config (
    mkdir config
)

:: Create .env file if it doesn't exist
IF NOT EXIST .env (
    ECHO Creating .env file from template...
    COPY .env.example .env
    ECHO Please edit .env with your API keys and credentials.
)

ECHO.
ECHO Setup complete! To run the example:
ECHO 1. Activate the virtual environment: venv\Scripts\activate
ECHO 2. Run the example: python examples\langchain_examples_new.py

PAUSE 