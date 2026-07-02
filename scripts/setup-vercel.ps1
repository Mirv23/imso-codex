<#
.SYNOPSIS
    Configure toutes les variables d'environnement Vercel pour IMSO Haiti
.DESCRIPTION
    Lit les valeurs depuis l'environnement local ou les demande interactivement,
    puis les configure via `vercel env add PLAIN` pour production, preview et development.
.PARAMETER Environments
    Environnements Vercel cibles (par défaut: production,preview,development)
#>

param(
    [string]$Environments = "production,preview,development"
)

$envTargets = $Environments.Split(",") | ForEach-Object { $_.Trim() }

Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   IMSO Haiti - Configuration des secrets Vercel    ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "Environnements cibles: $($envTargets -join ', ')" -ForegroundColor Yellow
Write-Host ""

# 1. Vérifier que vercel CLI est installé
if (-not (Get-Command "vercel" -ErrorAction SilentlyContinue)) {
    Write-Host "ERREUR: vercel CLI non installé." -ForegroundColor Red
    Write-Host "Pour installer: npm i -g vercel" -ForegroundColor Yellow
    exit 1
}

# 2. Vérifier qu'on est authentifié
$whoami = & vercel whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERREUR: Vous n'êtes pas connecté à Vercel." -ForegroundColor Red
    Write-Host "Exécutez: vercel login" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Authentifié Vercel: $whoami" -ForegroundColor Green

# 3. Définition de toutes les variables avec leurs défauts et catégories
$variables = @(
    @{ Name = "DJANGO_SECRET_KEY"; Default = ""; Required = $true; Prompt = "Clé secrète Django (obligatoire)" }
    @{ Name = "ADMIN_PASSWORD"; Default = ""; Required = $true; Prompt = "Mot de passe admin (obligatoire)" }
    @{ Name = "PAYMENT_CONFIRM_KEY"; Default = ""; Required = $true; Prompt = "Clé de confirmation paiement (obligatoire)" }
    @{ Name = "FIELD_ENCRYPTION_KEY"; Default = ""; Required = $true; Prompt = "Clé de chiffrement des secrets (obligatoire)" }
    @{ Name = "ADMIN_USERNAME"; Default = "mirv"; Required = $false; Prompt = "Nom d'utilisateur admin" }
    @{ Name = "ADMIN_EMAIL"; Default = "admin@imsohaiti.com"; Required = $false; Prompt = "Email admin" }
    @{ Name = "DATABASE_URL"; Default = "sqlite:///db.sqlite3"; Required = $false; Prompt = "URL de base de données" }
    @{ Name = "DJANGO_DEBUG"; Default = "False"; Required = $false; Prompt = "Mode debug Django" }
    @{ Name = "DJANGO_ALLOWED_HOSTS"; Default = "localhost,127.0.0.1,.vercel.app,imsohaiti.com"; Required = $false; Prompt = "Hôtes autorisés" }
    @{ Name = "DJANGO_CSRF_TRUSTED_ORIGINS"; Default = "https://imsohaiti.com,https://www.imsohaiti.com"; Required = $false; Prompt = "Origines CSRF autorisées" }
    @{ Name = "DJANGO_CORS_ALLOWED_ORIGINS"; Default = "https://imsohaiti.com,https://www.imsohaiti.com"; Required = $false; Prompt = "Origines CORS autorisées" }
    @{ Name = "DJANGO_CORS_ALLOW_ALL_ORIGINS"; Default = "False"; Required = $false; Prompt = "Tout autoriser CORS" }
    @{ Name = "DJANGO_LOG_LEVEL"; Default = "INFO"; Required = $false; Prompt = "Niveau de log" }
    @{ Name = "DJANGO_SECURE_SSL_REDIRECT"; Default = "True"; Required = $false; Prompt = "Redirection SSL" }
    @{ Name = "DJANGO_HSTS_SECONDS"; Default = "31536000"; Required = $false; Prompt = "Durée HSTS en secondes" }
    @{ Name = "DJANGO_SESSION_COOKIE_SECURE"; Default = "True"; Required = $false; Prompt = "Session cookie secure" }
    @{ Name = "DJANGO_CSRF_COOKIE_SECURE"; Default = "True"; Required = $false; Prompt = "CSRF cookie secure" }
    @{ Name = "SENTRY_DSN"; Default = ""; Required = $false; Prompt = "Sentry DSN (optionnel)" }
    @{ Name = "SENTRY_TRACES_SAMPLE_RATE"; Default = "0.1"; Required = $false; Prompt = "Sentry traces sample rate" }
    @{ Name = "DJANGO_ENV"; Default = "production"; Required = $false; Prompt = "Environnement Django" }
    @{ Name = "WEBHOOK_SECRET"; Default = ""; Required = $true; Prompt = "Secret webhook (obligatoire, sinon webhooks 503)" }
    @{ Name = "ADMIN_API_TOKEN"; Default = ""; Required = $false; Prompt = "Token API admin (optionnel)" }
    @{ Name = "DJANGO_EMAIL_BACKEND"; Default = "django.core.mail.backends.console.EmailBackend"; Required = $false; Prompt = "Backend email" }
    @{ Name = "DJANGO_EMAIL_HOST"; Default = ""; Required = $false; Prompt = "Hôte SMTP (optionnel)" }
    @{ Name = "DJANGO_EMAIL_PORT"; Default = "587"; Required = $false; Prompt = "Port SMTP" }
    @{ Name = "DJANGO_EMAIL_USE_TLS"; Default = "True"; Required = $false; Prompt = "TLS pour email" }
    @{ Name = "DJANGO_EMAIL_USER"; Default = ""; Required = $false; Prompt = "Utilisateur SMTP (optionnel)" }
    @{ Name = "DJANGO_EMAIL_PASSWORD"; Default = ""; Required = $false; Prompt = "Mot de passe SMTP (optionnel)" }
    @{ Name = "DJANGO_DEFAULT_FROM_EMAIL"; Default = "noreply@imsohaiti.com"; Required = $false; Prompt = "Expéditeur par défaut" }
    @{ Name = "DJANGO_CACHE_BACKEND"; Default = "django.core.cache.backends.locmem.LocMemCache"; Required = $false; Prompt = "Backend cache" }
    @{ Name = "DJANGO_CACHE_LOCATION"; Default = "imso-cache"; Required = $false; Prompt = "Localisation du cache" }
    @{ Name = "DJANGO_FILE_STORAGE"; Default = "django.core.files.storage.FileSystemStorage"; Required = $false; Prompt = "Backend stockage fichiers" }
)

# 4. Collecter les valeurs
$values = @{}
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Collecte des valeurs (vide = valeur par défaut)" -ForegroundColor Yellow
Write-Host "Les valeurs obligatoires doivent être fournies." -ForegroundColor Yellow
Write-Host ""

foreach ($var in $variables) {
    $name = $var.Name
    $default = $var.Default
    $required = $var.Required
    $prompt = $var.Prompt

    # Essayer de lire depuis l'environnement local d'abord
    $localVal = [Environment]::GetEnvironmentVariable($name, "User")
    if (-not $localVal) {
        $localVal = [Environment]::GetEnvironmentVariable($name, "Machine")
    }
    if (-not $localVal) {
        $localVal = [Environment]::GetEnvironmentVariable($name, "Process")
    }

    $displayDefault = if ($default) { $default } else { "(aucun)" }
    $displayEnv = if ($localVal) { " [env: $($localVal.Substring(0, [Math]::Min(20, $localVal.Length)))$(if($localVal.Length -gt 20){'...'}else{''})]" } else { "" }

    if ($required) {
        do {
            $input = Read-Host "$prompt"
            if (-not $input -and $localVal) { $input = $localVal }
            if (-not $input) { Write-Host "  => Requis!" -ForegroundColor Red }
        } until ($input)
        $values[$name] = $input
    } else {
        $input = Read-Host "$prompt [$displayDefault]$displayEnv"
        if (-not $input) {
            $values[$name] = if ($localVal) { $localVal } else { $default }
        } else {
            $values[$name] = $input
        }
    }
}

# 5. Afficher le résumé avant l'envoi
Write-Host ""
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Résumé des valeurs à configurer:" -ForegroundColor Yellow
foreach ($var in $variables) {
    $name = $var.Name
    $val = $values[$name]
    $masked = if ($val.Length -gt 0) { $val.Substring(0, [Math]::Min(4, $val.Length)) + "..." } else { "(vide)" }
    Write-Host "  $name = $masked"
}

Write-Host ""
$confirm = Read-Host "Continuer la configuration Vercel ? (O/n)"
if ($confirm -eq "n" -or $confirm -eq "N") {
    Write-Host "Configuration annulée." -ForegroundColor Red
    exit 0
}

# 6. Envoyer chaque variable à Vercel pour chaque environnement
Write-Host ""
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Configuration des variables d'environnement Vercel..." -ForegroundColor Yellow

$successCount = 0
$failCount = 0

foreach ($var in $variables) {
    $name = $var.Name
    $val = $values[$name]

    foreach ($envName in $envTargets) {
        Write-Host "→ $name [$envName]..." -NoNewline

        # Piping pour éviter l'invite interactive (PLAIN = visible dans l'UI Vercel)
        $result = ($val | & vercel env add PLAIN $name $envName --yes 2>&1)
        $exitCode = $LASTEXITCODE

        if ($exitCode -eq 0) {
            Write-Host " OK" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host " ERREUR" -ForegroundColor Red
            Write-Host "    $result" -ForegroundColor DarkRed
            $failCount++
        }
    }
}

# 7. Résumé final
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                   RÉSUMÉ FINAL                     ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "  Variables configurées avec succès : $successCount" -ForegroundColor Green
if ($failCount -gt 0) { Write-Host "  Échecs                          : $failCount" -ForegroundColor Red }
Write-Host "  Nouvelles variables utilisables sans redéploiement." -ForegroundColor Gray
Write-Host ""
Write-Host "Prochaines étapes:" -ForegroundColor Yellow
Write-Host "  1. Déployer : .\scripts\deploy-vercel.ps1 -Prod" -ForegroundColor White
Write-Host "  2. Vérifier : https://imsohaiti.com" -ForegroundColor White
