# -*- coding: utf-8 -*-
"""Audit du 5 nov. 2026, priorite 2 : ce qui fait « site genere par IA ».

1. Titres-formules remplaces par des phrases concretes, tirees des textes d'IMSO
   (mission, valeurs). Deux titres annoncaient aussi un compte faux : « Trois
   principes » pour 8 valeurs, « Trois etapes » pour 5 etapes.
   Le titre n'est remplace QUE s'il est encore au texte seme d'origine : une
   retouche faite depuis l'admin est preservee (meme regle que 0035/0037).

2. Les etiquettes en pastille au-dessus des titres ne sont plus affichees, sauf
   celles du hero et de « Notre mission ». Leurs cles ne servent plus a rien :
   on les retire de « Textes du site » pour que l'admin ne propose pas des
   champs sans effet. Le retour arriere les recree avec leur texte d'origine.

3. La salle est aux Cayes, pas a Port-au-Prince (adresse du pied de page et du
   flyer IMSO | CCFOR) : l'intro de la section location est corrigee.
"""
from django.db import migrations

# (cle, titre seme d'origine, nouveau titre)
TITLES = [
    ("why_title",
     "Plus qu'une mutuelle, un véritable écosystème d'opportunités.",
     "Épargner ensemble, emprunter sans collatéral abusif."),
    ("val_title",
     "Trois principes qui guident chaque décision.",
     "Mutuellement et solidairement responsables."),
    ("process_title",
     "Trois étapes simples pour rejoindre un GEI.",
     "Comment rejoindre un GEI."),
    ("cours_title",
     "Apprendre, entreprendre, transmettre.",
     "Cours ouverts aux inscriptions."),
    ("espace_title",
     "Un espace pensé pour vos événements.",
     "Louer une salle chez IMSO."),
    ("cta_title",
     "Prêt·e à entreprendre avec votre communauté ?",
     "Rejoindre un Groupe d'Entraide Intégrée."),
    ("espace_intro",
     "IMSO met à disposition une salle modulable au cœur de Port-au-Prince : conférences, séminaires, formations, anniversaires, mariages… Réservez directement en consultant les disponibilités ci-dessous.",
     "IMSO met à disposition une salle modulable aux Cayes : conférences, séminaires, formations, anniversaires, mariages… Réservez directement en consultant les disponibilités ci-dessous."),
]

# Etiquettes retirees de la page : (cle, libelle admin, groupe, texte d'origine)
LABELS = [
    ("val_label", "Label de la section Nos valeurs", "Accueil - Valeurs", "Nos valeurs"),
    ("why_label", "Intitulé (label) de la section Pourquoi nous rejoindre",
     "Accueil - Pourquoi nous rejoindre", "Pourquoi nous rejoindre"),
    ("process_label", "Label de la section Notre processus", "Accueil - Processus",
     "Notre processus"),
    ("cours_label", "Petit label au-dessus du titre de la section Cours", "Accueil - Cours",
     "Aperçu des cours"),
    ("espace_label", "Petit label au-dessus du titre de la section espace",
     "Location d'espace", "Location d'espace"),
    ("cta_testimonials_label", "Étiquette de la section témoignages",
     "Accueil - Témoignages", "Témoignages"),
    ("kit_label", "Petit label au-dessus du titre du kit", "Boutique - Kit",
     "Kit d'éducation financière"),
]


def forwards(apps, schema_editor):
    SiteText = apps.get_model("adminpanel", "SiteText")
    for key, old, new in TITLES:
        SiteText.objects.filter(key=key, value=old).update(value=new)
    SiteText.objects.filter(key__in=[k for k, *_ in LABELS]).delete()


def backwards(apps, schema_editor):
    SiteText = apps.get_model("adminpanel", "SiteText")
    for key, old, new in TITLES:
        SiteText.objects.filter(key=key, value=new).update(value=old)
    for key, label, group, value in LABELS:
        SiteText.objects.get_or_create(
            key=key, defaults={"label": label, "group": group, "value": value}
        )


class Migration(migrations.Migration):

    dependencies = [
        ("adminpanel", "0037_restore_textes_origine"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
