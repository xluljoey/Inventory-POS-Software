#!/bin/bash

# Repository configuration
REPO_URL="https://github.com/xluljoey/Inventory-POS-Software.git"

echo "🚀 Starting Clean Git Setup..."

# 1. GITIGNORE SYNC: Create or update .gitignore with correct patterns
echo "📦 Updating .gitignore..."
cat <<EOT > .gitignore
.venv/
venv/
venv311/
__pycache__/
*.pyc
*.db
*.bak
token.json
credentials.json
logs/
.pytest_cache/
EOT

# 2. RE-INITIALIZATION: Wipe history to fix bloat
echo "🗑️  Wiping existing Git history (7,000+ objects)..."
rm -rf .git

echo "🆕 Initializing fresh repository..."
git init

# 3. VENV REMOVAL: Verify folders are ignored
# Since .git was deleted, we just need to ensure git add respects .gitignore
echo "🔍 Adding files (Respecting .gitignore)..."
git add .

# 4. INITIAL COMMIT
git commit -m "Initial clean commit: Production-ready codebase"

# 5. BRANCH SETUP: Create main and premium-sync
echo "🌿 Setting up branches..."
git branch -M main
git branch premium-sync

# 6. REMOTE PUSH: Connect and force push
echo "☁️  Connecting to GitHub..."
git remote add origin "$REPO_URL"

echo "📤 Force pushing clean 'main' branch..."
# Note: You may be prompted for credentials if not using SSH/Personal Access Token
git push -u origin main --force

echo "✅ Success! Your repository has been slimmed down and pushed to GitHub."
echo "Branches created: main, premium-sync"
