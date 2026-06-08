# IMSO Website + Backend Django

Projet IMSO avec le site public et le panel admin conserves depuis les fichiers HTML autonomes initiaux. Les styles, animations, dispositions, images et polices d'origine sont gardes dans les templates Django.

## Structure

- `templates/core/index.html` : interface publique IMSO originale
- `templates/adminpanel/dashboard.html` : interface admin originale
- `static/website/assets/` : assets du site public
- `static/adminpanel/assets/` : assets du panel admin
- `apps/adminpanel/` : modeles metier, vues dashboard, API resume
- `imso_backend/` : configuration Django
- `vercel.json` : configuration Vercel Python

## Lancer localement

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Site public : `http://127.0.0.1:8000/`

Panel admin IMSO : `http://127.0.0.1:8000/dashboard/`

Admin Django natif : `http://127.0.0.1:8000/django-admin/`

## Deployer sur Vercel

1. Envoyer ce dossier dans un depot GitHub.
2. Importer le depot dans Vercel.
3. Ajouter au minimum `DJANGO_SECRET_KEY` dans les variables d'environnement.
4. Ajouter une base PostgreSQL et renseigner `DATABASE_URL` pour un backend persistant.
5. Deployer.
