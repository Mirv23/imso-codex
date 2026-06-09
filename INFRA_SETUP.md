# IMSO — Infrastructure & Déploiement

## Base de données PostgreSQL

### Options de provisioning

| Service | Gratuit ? | URL de connexion |
|---------|-----------|-----------------|
| [Supabase](https://supabase.com) | Oui (500 Mo) | `postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres?sslmode=require` |
| [Render](https://render.com) | Oui (1 Go, expire après 90 jours) | `postgresql://[USER]:[PASSWORD]@[HOST]:5432/[DB_NAME]` |
| [Railway](https://railway.app) | Oui (500 Mo) | `postgresql://[USER]:[PASSWORD]@[HOST]:5432/[DB_NAME]?sslmode=require` |
| [AWS RDS](https://aws.amazon.com/rds/) | Non (payant) | `postgresql://[USER]:[PASSWORD]@[HOST]:5432/[DB_NAME]?sslmode=require` |

### Étapes pour lier à Vercel

1. Provisionner une base PostgreSQL chez l'un des fournisseurs ci-dessus.
2. Copier l'URL de connexion (format `postgresql://...`).
3. Dans le dashboard Vercel du projet, aller dans **Settings → Environment Variables**.
4. Ajouter la variable `DATABASE_URL` avec l'URL de connexion.
5. Ajouter aussi `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, etc.
6. Redéployer le projet (`vercel --prod` ou depuis le dashboard).

### Obtenir l'URL de connexion

```bash
# Exemple d'URL de connexion PostgreSQL
DATABASE_URL=postgresql://user:password@host:5432/imso?sslmode=require
```

### Migration initiale

```bash
# Configurer DATABASE_URL dans .env (pour le développement local)
echo "DATABASE_URL=postgresql://user:password@host:5432/imso?sslmode=require" >> .env

# Exécuter les migrations
python manage.py migrate

# Créer le superutilisateur
python manage.py createsuperuser

# Collecter les fichiers statiques
python manage.py collectstatic --noinput
```

> **Note :** En développement local avec SQLite, aucune configuration PostgreSQL n'est nécessaire. Le fichier `.env` utilise `DATABASE_URL=sqlite:///db.sqlite3` par défaut.

### Variables d'environnement requises en production

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | URL de connexion PostgreSQL |
| `DJANGO_SECRET_KEY` | Clé secrète Django (unique, longue) |
| `DJANGO_DEBUG` | `False` en production |
| `DJANGO_ALLOWED_HOSTS` | Liste des hôtes autorisés |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Origines de confiance CSRF |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Origines CORS autorisées |
| `DJANGO_SECURE_SSL_REDIRECT` | `True` pour forcer HTTPS |
| `DJANGO_SESSION_COOKIE_SECURE` | `True` en production |
| `DJANGO_CSRF_COOKIE_SECURE` | `True` en production |
| `DJANGO_LOG_LEVEL` | `INFO` ou `WARNING` |
