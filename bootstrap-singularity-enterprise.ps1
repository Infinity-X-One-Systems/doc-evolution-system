# bootstrap-singularity-enterprise.ps1
# Singularity Prime — Enterprise Bootstrap Script
# FAANG-Grade Scaffold for Infinity-X-One-Systems
#
# Prerequisites:
#   - GitHub CLI (gh) authenticated with org:write, repo, project scopes
#   - git configured with your identity
#
# Usage:
#   .\bootstrap-singularity-enterprise.ps1

param(
    [string]$Org  = "Infinity-X-One-Systems",
    [string]$Repo = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $Repo) {
    $Repo = Read-Host "Enter new repository name"
}
if (-not $Repo) {
    Write-Error "Repository name is required."
    exit 1
}

$FullRepo = "$Org/$Repo"

Write-Host ""
Write-Host "✦ Singularity Prime — Enterprise Bootstrap" -ForegroundColor Cyan
Write-Host "  Org:  $Org" -ForegroundColor DarkCyan
Write-Host "  Repo: $Repo" -ForegroundColor DarkCyan
Write-Host ""

# ── Step 1: Create repository from template ───────────────────────────────
Write-Host "[1/6] Creating repository from template..." -ForegroundColor Yellow
gh repo create "$FullRepo" `
    --template "$Org/infinity-templates" `
    --private `
    --confirm
Write-Host "      ✓ Repository created: https://github.com/$FullRepo" -ForegroundColor Green

# ── Step 2: Clone ──────────────────────────────────────────────────────────
Write-Host "[2/6] Cloning repository..." -ForegroundColor Yellow
git clone "https://github.com/$FullRepo.git"
Set-Location $Repo
Write-Host "      ✓ Cloned to ./$Repo" -ForegroundColor Green

# ── Step 3: Apply branch protection ───────────────────────────────────────
Write-Host "[3/6] Applying hardened branch protection to 'main'..." -ForegroundColor Yellow
gh api `
    -X PUT `
    "repos/$FullRepo/branches/main/protection" `
    -f "required_status_checks[strict]=true" `
    -f "required_status_checks[contexts][]=pat" `
    -f "required_status_checks[contexts][]=codeql" `
    -f "required_status_checks[contexts][]=state-machine" `
    -f "required_status_checks[contexts][]=docs" `
    -f "required_pull_request_reviews[required_approving_review_count]=1" `
    -f "required_pull_request_reviews[dismiss_stale_reviews]=true" `
    -f "required_pull_request_reviews[require_code_owner_reviews]=true" `
    -f "enforce_admins=true" `
    -f "allow_force_pushes=false" `
    -f "allow_deletions=false" `
    -f "required_conversation_resolution=true"
Write-Host "      ✓ Branch protection applied" -ForegroundColor Green

# ── Step 4: Set required secrets ──────────────────────────────────────────
Write-Host "[4/6] Configuring secrets (enter values or press Enter to skip)..." -ForegroundColor Yellow
$secrets = @(
    "ADMIN_PLANE_PAT",
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "VAULT_ADDR",
    "VAULT_TOKEN",
    "MESH_HOOK_URL"
)
foreach ($secret in $secrets) {
    $value = Read-Host "  $secret (blank to skip)"
    if ($value) {
        $value | gh secret set $secret --repo "$FullRepo"
        Write-Host "      ✓ $secret set" -ForegroundColor Green
    } else {
        Write-Host "      ⚠ $secret skipped" -ForegroundColor DarkYellow
    }
}

# ── Step 5: Enable GitHub Pages ───────────────────────────────────────────
Write-Host "[5/6] Enabling GitHub Pages (docs/ folder on main)..." -ForegroundColor Yellow
gh api `
    -X POST `
    "repos/$FullRepo/pages" `
    -f "source[branch]=main" `
    -f "source[path]=/docs" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "      ✓ GitHub Pages enabled" -ForegroundColor Green
} else {
    Write-Host "      ⚠ Pages may already be enabled or require manual setup" -ForegroundColor DarkYellow
}

# ── Step 6: Initial commit & push ─────────────────────────────────────────
Write-Host "[6/6] Verifying initial state and pushing..." -ForegroundColor Yellow
git add .
git commit -m "feat: Initialize Singularity Prime Enterprise Fabric" --allow-empty
git push origin main
Write-Host "      ✓ Initial push complete" -ForegroundColor Green

Write-Host ""
Write-Host "✦ Bootstrap complete!" -ForegroundColor Cyan
Write-Host "  Repository: https://github.com/$FullRepo" -ForegroundColor White
Write-Host "  Pages:      https://$($Org.ToLower()).github.io/$Repo/" -ForegroundColor White
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor DarkCyan
Write-Host "    1. Open singularity.code-workspace in VS Code" -ForegroundColor White
Write-Host "    2. Verify all GitHub Actions workflows pass" -ForegroundColor White
Write-Host "    3. Review singularity/evolution/todo.json for remaining tasks" -ForegroundColor White
Write-Host ""
