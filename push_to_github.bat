@echo off
setlocal enabledelayedexpansion
title Push Export Automation to GitHub

cd /d "C:\Users\Admin\Downloads\task 1\export-automation"

echo.
echo ============================================================
echo   EXPORT AUTOMATION SYSTEM — GitHub Push
echo ============================================================
echo.

REM ── 1. Check if git is initialised ──────────────────────────
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    echo [1/6] Initialising new git repository...
    git init -b main
) else (
    echo [1/6] Git repository already exists. OK.
)
echo.

REM ── 2. Set remote ───────────────────────────────────────────
echo [2/6] Setting remote origin...
git remote remove origin 2>nul
git remote add origin https://github.com/ssinega/Export-Automation-System.git
echo       Remote set to: https://github.com/ssinega/Export-Automation-System.git
echo.

REM ── 3. Configure branch ─────────────────────────────────────
echo [3/6] Ensuring branch is named "main"...
git branch -M main 2>nul
echo.

REM ── 4. Stage ALL changes ────────────────────────────────────
echo [4/6] Staging all changed files...
git add -A
git status --short
echo.

REM ── 5. Commit ───────────────────────────────────────────────
echo [5/6] Committing...
git commit -m "Fix Vercel FUNCTION_INVOCATION_FAILED: lazy imports, rewrites config, python-version pin" --allow-empty
echo.

REM ── 6. Push ─────────────────────────────────────────────────
echo [6/6] Pushing to GitHub (main branch)...
echo       You may be prompted for your GitHub credentials.
echo.
git push -u origin main

echo.
if errorlevel 1 (
    echo [ERROR] Push failed. Try: git push --force-with-lease -u origin main
) else (
    echo ============================================================
    echo   SUCCESS! Vercel will auto-deploy in ~30 seconds.
    echo.
    echo   Verify here:
    echo   https://export-automation-system.vercel.app/health
    echo ============================================================
)
echo.
pause
