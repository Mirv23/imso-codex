# -*- coding: utf-8 -*-
"""Points sans fonction : un titre ne prend pas de point final.

1. Retire le point final des titres stockes en base : cles « *_title » de
   « Textes du site » et titres des Parametres (hero, Notre mission, Formation).
   Seul le point final est retire, aucun mot n'est change : la regle s'applique
   donc aussi aux titres retouches depuis l'admin. Points de suspension intacts.

2. La pastille flottante « Solidarite · Epargne · Croissance » posee sur la
   photo du hero n'est plus affichee : sa cle est retiree de « Textes du site »
   (champ sans effet). Le retour arriere la recree avec son texte d'origine.

3. Intro de la salle : en production, « au coeur de Port-au-Prince » avait ete
   retire depuis l'admin en laissant un trou (« une salle modulable  : ») ; la
   migration 0038 n'y touchait donc pas. On comble ce trou par « aux Cayes »,
   sans rien changer d'autre au texte.
"""
from django.db import migrations

ESPACE_GAP = "salle modulable  :"
ESPACE_FIX = "salle modulable aux Cayes :"

SETTING_TITLES = ("hero_title", "about_title", "formation_hero_title")

OVERLAY = {
    "key": "hero_visual_overlay",
    "label": "Légende superposée sur le visuel du Hero",
    "group": "Accueil - Hero",
    "value": "Solidarité · Épargne · Croissance",
}


def _strip_final_period(value):
    if value and value.endswith(".") and not value.endswith(".."):
        return value[:-1].rstrip()
    return value


def forwards(apps, schema_editor):
    SiteText = apps.get_model("adminpanel", "SiteText")
    SiteSetting = apps.get_model("adminpanel", "SiteSetting")
    for t in SiteText.objects.filter(key__endswith="_title"):
        new = _strip_final_period(t.value)
        if new != t.value:
            SiteText.objects.filter(pk=t.pk).update(value=new)
    for s in SiteSetting.objects.all():
        changed = {}
        for field in SETTING_TITLES:
            old = getattr(s, field, "")
            new = _strip_final_period(old)
            if new != old:
                changed[field] = new
        if changed:
            SiteSetting.objects.filter(pk=s.pk).update(**changed)
    SiteText.objects.filter(key=OVERLAY["key"]).delete()
    for t in SiteText.objects.filter(key="espace_intro", value__contains=ESPACE_GAP):
        SiteText.objects.filter(pk=t.pk).update(value=t.value.replace(ESPACE_GAP, ESPACE_FIX, 1))


def backwards(apps, schema_editor):
    SiteText = apps.get_model("adminpanel", "SiteText")
    for t in SiteText.objects.filter(key="espace_intro", value__contains=ESPACE_FIX):
        SiteText.objects.filter(pk=t.pk).update(value=t.value.replace(ESPACE_FIX, ESPACE_GAP, 1))
    SiteText.objects.get_or_create(
        key=OVERLAY["key"],
        defaults={"label": OVERLAY["label"], "group": OVERLAY["group"], "value": OVERLAY["value"]},
    )


class Migration(migrations.Migration):

    dependencies = [
        ("adminpanel", "0039_trainingregistration"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
