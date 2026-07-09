from django.db import migrations
import json

IMAGES = json.loads(r'''[{"key": "espace_photo_1", "label": "Location d'espace \u2014 Galerie (Salle principale)", "group": "Location d'espace", "alt": "Salle de conf\u00e9rence am\u00e9nag\u00e9e"}, {"key": "espace_photo_2", "label": "Location d'espace \u2014 Galerie (Conf\u00e9rence)", "group": "Location d'espace", "alt": "Configuration conf\u00e9rence"}, {"key": "espace_photo_3", "label": "Location d'espace \u2014 Galerie (Banquet)", "group": "Location d'espace", "alt": "Configuration banquet"}, {"key": "espace_photo_4", "label": "Location d'espace \u2014 Galerie (C\u00e9r\u00e9monie)", "group": "Location d'espace", "alt": "D\u00e9coration de c\u00e9r\u00e9monie"}, {"key": "hero_photo_1", "label": "Accueil \u2014 Photo hero 1 (Solidarit\u00e9)", "group": "Accueil", "alt": "Entrepreneure ha\u00eftienne souriante"}, {"key": "hero_photo_2", "label": "Accueil \u2014 Photo hero 2 (\u00c9pargne)", "group": "Accueil", "alt": "Membre comptant son \u00e9pargne"}, {"key": "hero_photo_3", "label": "Accueil \u2014 Photo hero 3 (Croissance)", "group": "Accueil", "alt": "Entrepreneur fier devant son commerce"}, {"key": "why_featured", "label": "Pourquoi nous rejoindre \u2014 Image mise en avant", "group": "Pourquoi nous rejoindre", "alt": "Mains jointes en signe d'entraide \u2014 r\u00e9seau IMSO"}]''')


def seed(apps, schema_editor):
    SiteImage = apps.get_model("adminpanel", "SiteImage")
    for i, e in enumerate(IMAGES):
        SiteImage.objects.get_or_create(
            key=e["key"],
            defaults={"label": e["label"], "group": e["group"], "alt": e["alt"], "sort_order": i},
        )


def unseed(apps, schema_editor):
    apps.get_model("adminpanel", "SiteImage").objects.filter(key__in=[e["key"] for e in IMAGES]).delete()


class Migration(migrations.Migration):
    dependencies = [("adminpanel", "0024_siteimage")]
    operations = [migrations.RunPython(seed, unseed)]
