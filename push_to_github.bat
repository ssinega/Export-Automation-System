@echo off
echo ==========================================
echo  Pushing Export Automation System to GitHub
echo ==========================================
cd /d "%~dp0"

echo [1/5] Initializing Git repository...
git init

echo [2/5] Setting default branch to main...
git branch -M main

echo [3/5] Adding remote repository...
git remote remove origin 2>nul
git remote add origin https://github.com/ssinega/Export-Automation-System.git

echo [4/5] Staging files and creating commit...
git add .
git commit -m "Initial commit: Export Automation System"

echo [5/5] Pushing to GitHub...
git push -u origin main

echo ==========================================
echo  Done!
echo ==========================================
pause
