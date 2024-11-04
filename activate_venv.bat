@echo off

:: Navigate to the project directory (if needed)
@REM cd /path/to/your/project

:: Activate virtual environment
call new_venv\Scripts\activate

echo Virtual environment activated.

:: Upgrade pip
python.exe -m pip install --upgrade pip

:: Install dependencies
pip install -r requirements.txt

echo dependencies installed
