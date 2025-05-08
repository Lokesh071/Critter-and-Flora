@echo off
echo Activating virtual environment...
call tf-env\Scripts\activate.bat

if %errorlevel% neq 0 (
    echo Error activating virtual environment.
    pause
    exit /b %errorlevel%
)

REM Reset the password in the database
echo Running password reset script...
mysql -u root -p"yourpassword" -P 3307 < reset_password.sql

REM Check if the MySQL command was successful
if %errorlevel% neq 0 (
    echo Error resetting password. Please check MySQL connection and credentials.
    pause
    exit /b %errorlevel%
)

echo Password reset successful.

REM Start the Flask application
echo Starting Flask server...
python app.py

pause 
