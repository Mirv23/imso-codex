<#
.SYNOPSIS
    Script de déploiement IMSO sur Vercel
.DESCRIPTION
    Vérifie que les secrets Vercel sont configurés (appelle setup-vercel.ps1 si besoin),
    puis lance le déploiement. N'écrit PAS de fichier .env local.
.PARAMETER Prod
    Déploie en production (par défaut: preview)
.PARAMETER SkipSetup
    Ignore la vérification des secrets (déploiement rapide)
#>

param(
    [switch]$Prod,
    [switch]$SkipSetup
)

$envName = if ($Prod) { "production" } else { "preview" }

Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║         IMSO Haiti - Déploiement Vercel            ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host "Environnement cible : $envName" -ForegroundColor Yellow
Write-Host ""

# 1. Vérifier que vercel CLI est installé
if (-not (Get-Command "vercel" -ErrorAction SilentlyContinue)) {
    Write-Host "ERREUR: vercel CLI non installé." -ForegroundColor Red
    Write-Host "  Pour installer: npm i -g vercel" -ForegroundColor Yellow
    exit 1
}

# 2. Vérifier l'authentification
$whoami = & vercel whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERREUR: Vous n'êtes pas connecté à Vercel." -ForegroundColor Red
    Write-Host "  Exécutez: vercel login" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Authentifié: $whoami" -ForegroundColor Green

# 3. Vérifier que les secrets sont configurés (sauf si --SkipSetup)
if (-not $SkipSetup) {
    Write-Host "→ Vérification des variables d'environnement Vercel..." -ForegroundColor Yellow
    $envList = & vercel env ls $envName 2>&1
    $hasSecret = $envList -match "DJANGO_SECRET_KEY"

    if (-not $hasSecret) {
        Write-Host "⚠ DJANGO_SECRET_KEY non trouvée sur $envName." -ForegroundColor Yellow
        $runSetup = Read-Host "Lancer le script de configuration des secrets ? (O/n)"
        if ($runSetup -ne "n" -and $runSetup -ne "N") {
            & "$PSScriptRoot\setup-vercel.ps1" -Environments $envName
            if ($LASTEXITCODE -ne 0) {
                Write-Host "ERREUR: Configuration des secrets échouée." -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "ATTENTION: Déploiement sans secrets configurés. Risque d'échec." -ForegroundColor Red
        }
    } else {
        Write-Host "✓ Variables Vercel déjà configurées" -ForegroundColor Green
    }
}

# 4. Déploiement (ne pas écrire de .env local)
Write-Host ""
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Lancement du déploiement Vercel ($envName)..." -ForegroundColor Yellow
Write-Host ""

# S'assurer qu'aucun .env.local ou .env n'est présent
if (Test-Path ".env.local") {
    Write-Host "⚠ .env.local présent - Vercel l'ignore mais nettoyage recommandé" -ForegroundColor DarkYellow
}

$deployArgs = @("deploy")
if ($Prod) { $deployArgs += "--prod" }

$deployResult = & vercel $deployArgs --confirm 2>&1
$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║               DÉPLOIEMENT RÉUSSI !                 ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host "  $deployResult"
    Write-Host ""
    Write-Host "Prochaines étapes:" -ForegroundColor Yellow
    Write-Host "  1. Migrations : vercel run python scripts/vercel-migrate.py" -ForegroundColor White
    Write-Host "  2. Vérifier le site : https://imsohaiti.com" -ForegroundColor White
} else {
    Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║               ÉCHEC DU DÉPLOIEMENT                 ║" -ForegroundColor Red
    Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host "  $deployResult"
    exit 1
}
