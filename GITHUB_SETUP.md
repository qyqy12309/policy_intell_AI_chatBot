# GitHub Repository Setup Guide

## Quick Setup (Automated)

**Option 1: Use the batch script**
1. Double-click `push_to_github.bat`
2. Follow the prompts
3. Create the repository on GitHub if you haven't already

**Option 2: Manual Setup**

### Step 1: Create Repository on GitHub

1. Visit: https://github.com/new
2. Repository name: `policy-intelligence-engine`
3. Description: "AI-powered conversational insurance assistant with policy analysis"
4. Choose Public or Private
5. **DO NOT** add README, .gitignore, or license (we already have these)
6. Click "Create repository"

### Step 2: Push Your Code

Open PowerShell/Command Prompt in `C:\Users\User\Desktop` and run:

```bash
git remote add origin https://github.com/qyqy12309/policy-intelligence-engine.git
git branch -M main
git push -u origin main
```

### Authentication

If you're asked for credentials:

**Option A: Use Personal Access Token**
1. Go to: https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scopes: `repo` (full control)
4. Copy the token
5. Use token as password when pushing

**Option B: Use GitHub Desktop**
1. Download GitHub Desktop
2. File → Add Local Repository
3. Select `C:\Users\User\Desktop`
4. Publish repository

**Option C: Use SSH (Advanced)**
1. Generate SSH key: `ssh-keygen -t ed25519 -C "your_email@example.com"`
2. Add to GitHub: Settings → SSH and GPG keys → New SSH key
3. Change remote URL: `git remote set-url origin git@github.com:qyqy12309/policy-intelligence-engine.git`

## Verify Upload

After pushing, visit:
https://github.com/qyqy12309/policy-intelligence-engine

You should see all your files!

## Repository Structure

The repository follows the structure from `FILE_STRUCTURE.md`:

- `backend/` - Backend API server
- `frontend/` - Web chat interface
- Root documentation files

All files are organized as specified in the structure document.

