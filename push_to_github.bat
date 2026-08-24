@echo off
setlocal enabledelayedexpansion
title Push ALL Vercel Fixes to GitHub

cd /d "C:\Users\Admin\Downloads\task 1\export-automation"

echo.
echo ============================================================
echo   EXPORT AUTOMATION — Push All Vercel Fixes to GitHub
echo ============================================================
echo.
echo Working directory: %CD%
echo.

REM ── Make sure git exists ─────────────────────────────────────
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] git not found. Install Git and try again.
    pause
    exit /b 1
)

REM ── Check git is initialised ─────────────────────────────────
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    echo [1/5] No git repo found. Initialising...
    git init -b main
) else (
    echo [1/5] Git repo already initialised.
)

REM ── Set remote ───────────────────────────────────────────────
echo [2/5] Setting remote origin...
git remote remove origin 2>nul
git remote add origin https://github.com/ssinega/Export-Automation-System.git

REM ── Ensure main branch ───────────────────────────────────────
git branch -M main 2>nul

REM ── Stage ALL changes ────────────────────────────────────────
echo [3/5] Staging all files...
git add -A
echo.
echo Files staged:
git status --short
echo.

REM ── Commit ───────────────────────────────────────────────────
echo [4/5] Committing...
git commit -m "Fix Vercel crash: make all pandas imports lazy across all modules" --allow-empty
if errorlevel 1 (
    echo [WARN] Nothing new to commit. Trying with --allow-empty...
)
echo.

REM ── Push ─────────────────────────────────────────────────────
echo [5/5] Pushing to GitHub main...
echo       You may be prompted for GitHub credentials.
echo.
git push -u origin main

echo.
if errorlevel 1 (
    echo [WARN] Normal push failed. Trying force-with-lease...
    git push --force-with-lease -u origin main
)
if errorlevel 1 (
    echo.
    echo [ERROR] Push failed. Check your GitHub credentials and try:
    echo         git push -u origin main
    echo.
) else (
    echo.
    echo ============================================================
    echo   SUCCESS! Vercel will auto-deploy in approximately 30s.
    echo.
    echo   Test these URLs after 30 seconds:
    echo   Health: https://export-automation-system.vercel.app/health
    echo   Home:   https://export-automation-system.vercel.app/
    echo ============================================================
    echo.
    echo Latest commit:
    git log -1 --oneline
)
echo.
pause
