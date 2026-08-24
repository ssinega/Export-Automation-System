@echo off
setlocal enabledelayedexpansion
title Push Vercel Entrypoint Fix to GitHub

cd /d "C:\Users\Admin\Downloads\task 1\export-automation"

echo.
echo ============================================================
echo   EXPORT AUTOMATION — Push Vercel Entrypoint Fix to GitHub
echo ============================================================
echo.

git remote remove origin 2>nul
git remote add origin https://github.com/ssinega/Export-Automation-System.git
git branch -M main 2>nul

echo Staging all files...
git add -A

echo Committing...
git commit -m "Fix Vercel entrypoint in pyproject.toml to use dotted module syntax api.index:app" --allow-empty

echo Pushing to GitHub main...
git push -u origin main
if errorlevel 1 (
    git push --force-with-lease -u origin main
)

echo.
echo Latest commit:
git log -1 --oneline
echo ============================================================
echo Done!
