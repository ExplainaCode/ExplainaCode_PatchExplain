@echo off

:: Navigate to the project directory (if needed)
@REM cd /path/to/your/project

:: Activate virtual environment
call venv\Scripts\activate

echo Virtual environment activated.

:: Install dependencies
pip install -r requirements.txt

echo dependencies installed
