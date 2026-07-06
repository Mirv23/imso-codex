"""Migre les fichiers sensibles du bucket PUBLIC vers le bucket PRIVÉ.

Après le passage des champs `Chapter.video`, `Profile.id_document` et
`Payment.screenshot` au stockage privé, les objets déjà présents dans le bucket
public doivent être recopiés (mêmes clés) dans le bucket privé pour rester
accessibles via les URLs signées. On copie côté serveur (S3 CopyObject), on
vérifie, puis on supprime l'original public (sauf --keep-source).

    # simulation (n'écrit rien) :
    python manage.py migrate_private_media --dry-run
    # migration réelle :
    python manage.py migrate_private_media
    # migration en conservant les originaux publics :
    python manage.py migrate_private_media --keep-source

Nécessite les variables SUPABASE_S3_* (mêmes identifiants qu'en prod).
Le bucket privé est créé s'il n'existe pas.
"""
from __future__ import annotations

import os

from django.core.management.base import BaseCommand, CommandError

# Préfixes des fichiers désormais servis depuis le bucket privé.
PRIVATE_PREFIXES = ["courses/videos/", "kyc/", "screenshots/"]


class Command(BaseCommand):
    help = "Recopie les fichiers sensibles du bucket public vers le bucket privé."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="N'écrit rien, liste seulement.")
        parser.add_argument(
            "--keep-source", action="store_true",
            help="Conserve les fichiers dans le bucket public après copie.",
        )

    def handle(self, *args, **options):
        if not (os.environ.get("SUPABASE_S3_ACCESS_KEY") and os.environ.get("SUPABASE_S3_SECRET_KEY")):
            raise CommandError("SUPABASE_S3_* absent : rien à migrer (stockage local).")

        # Réutilise le client S3 déjà configuré pour le projet.
        from apps.adminpanel.views import _s3_client_and_bucket

        client, public_bucket = _s3_client_and_bucket(private=False)
        _, private_bucket = _s3_client_and_bucket(private=True)
        dry = options["dry_run"]
        keep = options["keep_source"]

        self.stdout.write(f"Public : {public_bucket}  ->  Privé : {private_bucket}")
        self.stdout.write(f"Préfixes : {', '.join(PRIVATE_PREFIXES)}")
        if dry:
            self.stdout.write(self.style.WARNING("Mode simulation (--dry-run) : aucune écriture."))

        # Crée le bucket privé si besoin.
        self._ensure_bucket(client, private_bucket, dry)

        copied = skipped = failed = deleted = 0
        for prefix in PRIVATE_PREFIXES:
            for key in self._iter_keys(client, public_bucket, prefix):
                # Déjà présent dans le privé ? on ne réécrase pas.
                if self._exists(client, private_bucket, key):
                    self.stdout.write(f"  = déjà privé : {key}")
                    skipped += 1
                    if not keep and not dry:
                        self._delete(client, public_bucket, key)
                        deleted += 1
                    continue
                if dry:
                    self.stdout.write(f"  + copierait : {key}")
                    copied += 1
                    continue
                try:
                    client.copy_object(
                        Bucket=private_bucket,
                        Key=key,
                        CopySource={"Bucket": public_bucket, "Key": key},
                    )
                except Exception as exc:  # noqa: BLE001
                    self.stderr.write(f"  ! échec copie {key} : {exc}")
                    failed += 1
                    continue
                if not self._exists(client, private_bucket, key):
                    self.stderr.write(f"  ! copie non confirmée {key}")
                    failed += 1
                    continue
                copied += 1
                self.stdout.write(f"  + copié : {key}")
                if not keep:
                    self._delete(client, public_bucket, key)
                    deleted += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Terminé — copiés={copied} déjà-privés={skipped} "
                f"supprimés-du-public={deleted} échecs={failed}"
            )
        )
        if failed:
            raise CommandError(f"{failed} fichier(s) en échec — voir ci-dessus.")

    # ── Helpers S3 ────────────────────────────────────────────────────────
    def _ensure_bucket(self, client, bucket, dry):
        try:
            client.head_bucket(Bucket=bucket)
            self.stdout.write(f"Bucket privé « {bucket} » : présent.")
            return
        except Exception:
            pass
        if dry:
            self.stdout.write(self.style.WARNING(f"Bucket privé « {bucket} » créerait (simulation)."))
            return
        try:
            client.create_bucket(Bucket=bucket)
            self.stdout.write(self.style.SUCCESS(f"Bucket privé « {bucket} » créé."))
        except Exception as exc:  # noqa: BLE001
            raise CommandError(
                f"Impossible de créer le bucket privé « {bucket} » ({exc}). "
                "Créez-le manuellement dans Supabase (public = OFF) puis relancez."
            )

    def _iter_keys(self, client, bucket, prefix):
        token = None
        while True:
            kwargs = {"Bucket": bucket, "Prefix": prefix}
            if token:
                kwargs["ContinuationToken"] = token
            resp = client.list_objects_v2(**kwargs)
            for obj in resp.get("Contents", []) or []:
                yield obj["Key"]
            if resp.get("IsTruncated"):
                token = resp.get("NextContinuationToken")
            else:
                break

    def _exists(self, client, bucket, key):
        try:
            client.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False

    def _delete(self, client, bucket, key):
        try:
            client.delete_object(Bucket=bucket, Key=key)
        except Exception as exc:  # noqa: BLE001
            self.stderr.write(f"  ! échec suppression public {key} : {exc}")
