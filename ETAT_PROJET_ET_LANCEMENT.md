# Etat actuel du projet IMSO

Ce projet est dans :

```powershell
C:\Users\mirvp\Desktop\Imso-codex
```

Il contient maintenant :

- un site public IMSO conserve depuis le HTML initial ;
- un panel admin IMSO conserve depuis le HTML admin initial ;
- un backend Django structure ;
- une base SQLite locale de developpement deja migree ;
- une configuration Vercel Python/Django ;
- des modeles metier pour GEI, membres, cours, inscriptions, reservations de salle, demandes de contact et indicateurs dashboard.

## Routes disponibles

Quand le serveur Django tourne :

- Site public : `http://127.0.0.1:8000/`
- Panel admin IMSO : `http://127.0.0.1:8000/dashboard/`
- Admin Django natif : `http://127.0.0.1:8000/django-admin/`
- Healthcheck : `http://127.0.0.1:8000/health/`
- API resume dashboard : `http://127.0.0.1:8000/dashboard/api/summary/`
- API demandes de contact : `http://127.0.0.1:8000/api/contact-requests/`

## Important sur ton environnement local

Le dossier `.venv` existe deja, mais il ne contient pas de script `activate`.

Donc, sur ta machine, il vaut mieux lancer Django directement avec :

```powershell
.venv\Scripts\python.exe
```

Tu n'es pas oblige d'activer l'environnement virtuel pour travailler.

## Ordre exact des commandes pour lancer le projet

Ouvre PowerShell ou CMD, puis va dans le dossier du projet :

```powershell
cd C:\Users\mirvp\Desktop\Imso-codex
```

Ensuite lance les commandes dans cet ordre :

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py createsuperuser
.venv\Scripts\python.exe manage.py runserver
```

### Ce que fait chaque commande

`check` verifie que la configuration Django est correcte.

`migrate` cree ou met a jour les tables de la base de donnees.

`createsuperuser` cree ton compte administrateur. Cette commande se lance une seule fois, sauf si tu veux creer un autre admin.

`runserver` demarre le serveur local.

## Si `createsuperuser` dit qu'un utilisateur existe deja

Ce n'est pas grave. Tu peux passer directement a :

```powershell
.venv\Scripts\python.exe manage.py runserver
```

Si tu oublies le mot de passe admin, utilise :

```powershell
.venv\Scripts\python.exe manage.py changepassword NOM_UTILISATEUR
```

## PowerShell ou CMD ?

Les deux fonctionnent.

PowerShell :

```powershell
cd C:\Users\mirvp\Desktop\Imso-codex
.venv\Scripts\python.exe manage.py runserver
```

CMD :

```cmd
cd C:\Users\mirvp\Desktop\Imso-codex
.venv\Scripts\python.exe manage.py runserver
```

Comme ton `.venv` n'a pas `activate`, evite pour l'instant :

```powershell
.venv\Scripts\activate
```

## Etat technique actuel

Verifications deja faites :

- `python manage.py check` : OK
- migrations Django : OK
- rendu template public : OK
- rendu template admin : OK
- assets du site public : OK
- assets du panel admin : OK
- route `/` : OK
- route `/health/` : OK
- route `/dashboard/` : protegee par login Django
- route `/dashboard/api/summary/` : protegee si non connecte

## Ce qui est deja solide

- Le dashboard IMSO n'est pas public : il redirige vers le login Django.
- Les donnees importantes sont modelisees dans Django.
- L'admin Django natif permet de gerer les donnees sans coder une interface CRUD supplementaire.
- `.env`, `.venv`, `db.sqlite3`, `staticfiles` et `node_modules` sont ignores par Git.
- Les assets sont servis depuis `static/`.
- Le projet peut etre deploye sur Vercel avec `@vercel/python`.

## Points a finaliser avant production

### 1. Creer un vrai secret Django

En production, ne garde jamais la cle de developpement.

Dans Vercel, ajoute une variable :

```text
DJANGO_SECRET_KEY=une-longue-cle-secrete-unique
```

Tu peux generer une cle avec :

```powershell
.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. Desactiver le debug

En production :

```text
DJANGO_DEBUG=False
```

Ne mets jamais `DJANGO_DEBUG=True` sur Vercel en production.

### 3. Configurer les hosts autorises

Dans Vercel, ajoute ton domaine :

```text
DJANGO_ALLOWED_HOSTS=.vercel.app,ton-domaine.com
```

Si tu utilises seulement le domaine Vercel au debut :

```text
DJANGO_ALLOWED_HOSTS=.vercel.app
```

### 4. Configurer CSRF pour le domaine final

Quand tu connais ton URL Vercel ou ton domaine :

```text
DJANGO_CSRF_TRUSTED_ORIGINS=https://ton-projet.vercel.app,https://ton-domaine.com
```

### 5. Utiliser PostgreSQL en production

SQLite est acceptable en local, mais pas ideal pour production.

Sur Vercel, ajoute une base PostgreSQL puis configure :

```text
DATABASE_URL=postgresql://...
```

### 6. Creer un superuser production

Apres deploiement, il faut creer un superuser pour l'environnement production. Selon ton hebergeur/base de donnees, cette etape peut se faire via une commande distante, un script temporaire securise, ou une action d'initialisation.

Ne mets jamais un mot de passe admin faible.

### 7. Ne jamais envoyer ces fichiers sur GitHub

Ces fichiers doivent rester locaux :

- `.env`
- `.venv/`
- `db.sqlite3`
- `staticfiles/`

Ils sont deja dans `.gitignore`.

## Etat fonctionnel du panel admin

Le panel admin visuel est conserve exactement depuis le fichier HTML fourni.

Actuellement :

- l'interface est integree dans Django ;
- l'acces est protege par login ;
- les modeles backend existent ;
- l'API resume existe.

Ce qu'il reste a brancher si tu veux un dashboard 100% dynamique :

- connecter les cartes statistiques du panel a `/dashboard/api/summary/` ;
- connecter les formulaires du site public a `/api/contact-requests/` ;
- ajouter les endpoints CRUD si tu veux modifier les donnees directement depuis le panel IMSO, sans passer par `/django-admin/`.

## Commande quotidienne la plus simple

Quand tout est deja installe et migre :

```powershell
cd C:\Users\mirvp\Desktop\Imso-codex
.venv\Scripts\python.exe manage.py runserver
```

Puis ouvre :

```text
http://127.0.0.1:8000/
```

## Checklist avant de deployer

- `manage.py check` passe sans erreur.
- Les migrations passent.
- Tu as un superuser local.
- Tu as teste `/`, `/dashboard/`, `/django-admin/`.
- `DJANGO_SECRET_KEY` est configure sur Vercel.
- `DJANGO_DEBUG=False` sur Vercel.
- `DJANGO_ALLOWED_HOSTS` contient ton domaine.
- `DJANGO_CSRF_TRUSTED_ORIGINS` contient ton URL HTTPS.
- `DATABASE_URL` pointe vers PostgreSQL.
- Tu n'as pas pousse `.env`, `.venv` ou `db.sqlite3` sur GitHub.
