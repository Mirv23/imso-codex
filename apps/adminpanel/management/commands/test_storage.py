"""Vérifie le stockage de fichiers configuré (Supabase Storage ou disque local).

Écrit un fichier de test, relit son contenu, affiche l'URL publique, puis le
supprime. Permet de confirmer que Supabase Storage est bien branché en prod.

    python manage.py test_storage
"""

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Teste le backend de stockage par défaut (upload -> lecture -> url -> suppression)."

    def handle(self, *args, **options):
        backend = type(default_storage).__module__ + "." + type(default_storage).__name__
        self.stdout.write(f"Backend de stockage : {backend}")

        name = "diagnostics/test_storage.txt"
        content = b"IMSO storage OK"

        # Nettoyage préalable si un ancien fichier traîne
        if default_storage.exists(name):
            default_storage.delete(name)

        saved = default_storage.save(name, ContentFile(content))
        self.stdout.write(f"Écrit     : {saved}")

        read_back = default_storage.open(saved).read()
        ok = read_back == content
        self.stdout.write(f"Relu      : {read_back!r} ({'OK' if ok else 'ÉCHEC'})")

        self.stdout.write(f"URL       : {default_storage.url(saved)}")
        self.stdout.write(f"Existe    : {default_storage.exists(saved)}")

        default_storage.delete(saved)
        self.stdout.write(f"Supprimé  : {not default_storage.exists(saved)}")

        if ok:
            self.stdout.write(self.style.SUCCESS("Stockage fonctionnel ✔"))
        else:
            self.stderr.write("Le contenu relu ne correspond pas — stockage défaillant.")
