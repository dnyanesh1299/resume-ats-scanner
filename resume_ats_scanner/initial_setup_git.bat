@echo off
echo =========================================
echo 🔐 GitHub Initial Setup + Clone Repo
echo =========================================

:: Ask Git username
set /p gituser=Enter GitHub Username: 

:: Ask Git email
set /p gitemail=Enter GitHub Email: 

:: Set git config
git config --global user.name "%gituser%"
git config --global user.email "%gitemail%"

echo.
echo ✅ Git user configured
echo Username: %gituser%
echo Email: %gitemail%

echo.
:: Ask repository URL
set /p repourl=Enter GitHub Repository URL (https://github.com/...): 

echo.
echo 🔄 Starting repository clone...
echo When asked:
echo - Username = your GitHub username
echo - Password = GitHub Personal Access Token
echo.

git clone %repourl%

echo.
echo =========================================
echo ✅ Repository cloned successfully
echo =========================================
pause
