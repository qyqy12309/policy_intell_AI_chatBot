@echo off
echo ========================================
echo Uploading to GitHub Repository
echo ========================================
echo.
echo Step 1: Make sure you've created the repository on GitHub
echo Repository name: policy-intelligence-engine
echo GitHub URL: https://github.com/qyqy12309
echo.
echo Press any key to continue after creating the repository...
pause

cd /d "%~dp0"

echo.
echo Adding remote repository...
git remote add origin https://github.com/qyqy12309/policy-intelligence-engine.git 2>nul
if errorlevel 1 (
    echo Remote already exists. Updating...
    git remote set-url origin https://github.com/qyqy12309/policy-intelligence-engine.git
)

echo.
echo Setting branch to main...
git branch -M main

echo.
echo Pushing to GitHub...
git push -u origin main

if errorlevel 1 (
    echo.
    echo ERROR: Push failed!
    echo.
    echo Possible reasons:
    echo 1. Repository not created on GitHub yet
    echo 2. Authentication required (use GitHub Desktop or SSH keys)
    echo 3. Network issues
    echo.
    echo Solution:
    echo - Create the repository at: https://github.com/new
    echo - Or use GitHub Desktop to push
    echo - Or set up SSH keys for authentication
) else (
    echo.
    echo ========================================
    echo SUCCESS! Your code is on GitHub!
    echo ========================================
    echo.
    echo View your repository at:
    echo https://github.com/qyqy12309/policy-intelligence-engine
    echo.
)

pause

