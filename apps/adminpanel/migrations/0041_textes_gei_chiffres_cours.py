# -*- coding: utf-8 -*-
"""JK-2 : relecture des textes du site vitrine.

1. Chiffres de « Notre mission » : 8.6M HTG d'épargne mobilisée, +100M HTG de
   projets financés (à la place du taux de remboursement) et +800 projets
   approuvés (à la place des ateliers tenus en 2025).

2. GEI veut dire « Groupe d'Épargne et d'Investissement », pas « Groupe
   d'Entraide Intégrée ». Le nom est corrigé partout en base : Textes du site,
   Paramètres, étapes et valeurs. Seul le nom change, le reste du texte est
   conservé.

3. Tournures qui sonnaient « texte généré » (écriture inclusive à points,
   chiffres invérifiables, « accédez immédiatement »…) : le texte n'est
   remplacé QUE s'il est encore au texte d'origine. Une retouche faite depuis
   l'admin est préservée (même règle que 0035/0037/0038).

4. Les cours « Gestion RH » et « Techniques de gestion » ne sont plus proposés :
   ils sont désactivés (is_active=False), pas supprimés. Inscriptions et
   chapitres restent en base.

5. Capacité de la salle : 60 personnes sans tables, jusqu'à 45 avec tables.
   Ces nombres étaient écrits en dur dans le gabarit. Ils deviennent deux
   champs de « Textes du site » (espace_cap1_num, espace_cap2_num),
   modifiables depuis l'admin.

6. Part des femmes : le chiffre exact n'est pas affiché. La tuile indique
   qu'une large part des fonds décaissés va aux femmes entrepreneures.

7. Étape « Présentation PowerPoint du modèle GEI » : la durée « 1 jour » est
   retirée (le champ meta est vidé, l'étape reste).
"""
import re

from django.db import migrations

STATS = {
    "stat_savings": "8.6M",
    "stat_repayment": "+100M",
    "stat_repayment_label": "HTG de projets financés",
    "stat_workshops": "+800",
    "stat_workshops_label": "Projets approuvés",
    "stat_women": "Femmes",
    "stat_women_label": "Une large part des fonds décaissés va aux entrepreneures",
}

ETAPE_SANS_DUREE = re.compile(r"powerpoint", re.IGNORECASE)
DUREE_UN_JOUR = re.compile(r"^\W*1\s*jour\W*$", re.IGNORECASE)

APOS = "['’]"
GEI_PLURIEL = re.compile(r"Groupes d" + APOS + r"\s*Entraide\s+Int[ée]gr[ée]es?", re.IGNORECASE)
GEI_SINGULIER = re.compile(r"Groupe d" + APOS + r"\s*Entraide\s+Int[ée]gr[ée]e", re.IGNORECASE)
GEI_NOM_PLURIEL = "Groupes d'Épargne et d'Investissement"
GEI_NOM = "Groupe d'Épargne et d'Investissement"

SETTING_TEXT_FIELDS = (
    "tagline", "hero_title", "hero_subtitle", "hero_cta_text", "about_title",
    "about_text", "shop_intro", "footer_text", "formation_hero_title",
    "formation_hero_subtitle", "meta_description", "meta_keywords",
)

# (clé, texte d'origine, nouveau texte)
REWRITES = [
    ("why_card1_text",
     "Des centaines d'entrepreneurs, formateurs et épargnants partagent quotidiennement conseils, ressources et opportunités. Vous n'êtes jamais seul·e dans votre projet.",
     "Entrepreneurs, formateurs et épargnants s'échangent conseils, contacts et occasions d'affaires. Votre projet est suivi par tout le groupe."),
    ("why_card3_text",
     "Gestion, comptabilité, marketing local : 14 cours animés par des praticiens haïtiens chaque trimestre.",
     "Gestion, comptabilité, vente : des cours donnés par des formateurs haïtiens qui connaissent le terrain."),
    ("why_card4_text",
     "Cotisations mensuelles modulables, registre partagé en temps réel, retraits encadrés par les statuts du GEI.",
     "Cotisations mensuelles adaptées à vos moyens, registre tenu par le groupe, retraits encadrés par les statuts du GEI."),
    ("why_card5_text",
     "Chaque nouveau membre est jumelé à un·e mentor·e expérimenté·e du GEI pendant ses six premiers mois.",
     "Chaque nouveau membre est accompagné par un membre expérimenté du GEI pendant ses six premiers mois."),
    ("cta_paragraph",
     "Rejoignez l'un des cinq GEI actifs et accédez immédiatement à l'épargne collective, aux formations et au mentorat de pair-à-pair.",
     "Adhérez au GEI le plus proche de chez vous : vous épargnez avec le groupe, vous suivez les formations et un membre expérimenté vous accompagne à vos débuts."),
    ("cta_title",
     "Prêt·e à entreprendre avec votre communauté ?",
     "Rejoindre un Groupe d'Épargne et d'Investissement"),
    ("process_intro",
     "Un parcours pensé pour vous accueillir progressivement, le temps de comprendre les règles communes et de bâtir des liens avec votre groupe.",
     "L'adhésion se fait en plusieurs étapes, le temps de connaître les règles du groupe et ses membres."),
    ("cta_modal_sub",
     "Complétez vos informations et nous confirmons sous 24h.",
     "Laissez vos coordonnées, nous vous rappelons sous 24 h pour confirmer."),
    ("cta_modal_success_sub",
     "Nous vous contactons sous 24h pour confirmer votre réservation.",
     "Nous vous appelons sous 24 h pour confirmer votre réservation."),
]

COURS_RETIRES = (
    re.compile(r"^\s*gestion\s+(des\s+)?(rh|r\.h\.?|ressources\s+humaines)\b", re.IGNORECASE),
    re.compile(r"^\s*techniques?\s+de\s+gestion\b", re.IGNORECASE),
)

CAPACITES = [
    ("espace_cap1_num", "Capacité de la salle sans tables (nombre de personnes)", "60"),
    ("espace_cap2_num", "Capacité de la salle avec tables (nombre de personnes)", "45"),
]


def renomme_gei(texte):
    if not texte:
        return texte
    texte = GEI_PLURIEL.sub(GEI_NOM_PLURIEL, texte)
    return GEI_SINGULIER.sub(GEI_NOM, texte)


def _renomme_champs(model, fields):
    for obj in model.objects.all():
        changed = {}
        for field in fields:
            old = getattr(obj, field, None)
            if isinstance(old, str):
                new = renomme_gei(old)
                if new != old:
                    changed[field] = new
        if changed:
            model.objects.filter(pk=obj.pk).update(**changed)


def forwards(apps, schema_editor):
    SiteText = apps.get_model("adminpanel", "SiteText")
    SiteSetting = apps.get_model("adminpanel", "SiteSetting")
    ProcessStep = apps.get_model("adminpanel", "ProcessStep")
    CoreValue = apps.get_model("adminpanel", "CoreValue")
    Course = apps.get_model("adminpanel", "Course")

    SiteSetting.objects.update(**STATS)

    for key, old, new in REWRITES:
        SiteText.objects.filter(key=key, value=old).update(value=new)

    _renomme_champs(SiteText, ("value",))
    _renomme_champs(SiteSetting, SETTING_TEXT_FIELDS)
    _renomme_champs(ProcessStep, ("title", "text", "meta"))
    _renomme_champs(CoreValue, ("title", "text"))

    for step in ProcessStep.objects.all():
        if ETAPE_SANS_DUREE.search(step.title or "") and DUREE_UN_JOUR.match(step.meta or ""):
            ProcessStep.objects.filter(pk=step.pk).update(meta="")

    for course in Course.objects.filter(is_active=True):
        if any(p.search(course.title or "") for p in COURS_RETIRES):
            Course.objects.filter(pk=course.pk).update(is_active=False)

    for key, label, value in CAPACITES:
        SiteText.objects.update_or_create(
            key=key, defaults={"label": label, "group": "Location d'espace", "value": value}
        )


def backwards(apps, schema_editor):
    """Retour arrière partiel : les textes réécrits reprennent leur version
    d'origine et les champs de capacité sont retirés. Le nom des GEI, les
    chiffres et les cours désactivés ne sont pas rétablis (l'ancien état n'est
    pas connu avec certitude) : à refaire depuis l'admin si besoin."""
    SiteText = apps.get_model("adminpanel", "SiteText")
    for key, old, new in REWRITES:
        SiteText.objects.filter(key=key, value=new).update(value=old)
    SiteText.objects.filter(key__in=[k for k, *_ in CAPACITES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("adminpanel", "0040_titres_sans_point_final"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
