from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

from .models import (
    AdminNotification,
    BlogPost,
    Chapter,
    ContactRequest,
    Course,
    CourseEnrollment,
    Enrollment,
    Order,
    Payment,
    Product,
    Testimonial,
    VenueBooking,
)


@receiver(pre_delete, sender=CourseEnrollment)
def cancel_materialized_course_payment(sender, instance, **kwargs):
    """Supprime le Payment de CA materialise (external_reference='CE-<id>') quand
    une inscription formation est supprimee — y compris en CASCADE (suppression
    d'un etudiant). Evite un CA fantome apres suppression."""
    try:
        Payment.objects.filter(external_reference=f"CE-{instance.pk}").delete()
    except Exception:
        pass


# ── Nettoyage automatique des fichiers du stockage ───────────────────────
# Quand un objet portant un fichier média est supprimé, on efface aussi le
# fichier du stockage (Supabase) pour éviter les fichiers orphelins. Vaut aussi
# pour les suppressions en cascade (ex. supprimer un cours efface les vidéos de
# ses chapitres).
_MEDIA_FIELDS = {
    Chapter: ["video"],
    Course: ["banner"],
    Product: ["image"],
    BlogPost: ["cover_image"],
    Testimonial: ["photo"],
}


def _cleanup_media(sender: type, instance: Any, **kwargs: Any) -> None:
    for field_name in _MEDIA_FIELDS.get(sender, []):
        f = getattr(instance, field_name, None)
        if f:
            try:
                f.delete(save=False)
            except Exception:
                pass


for _model in _MEDIA_FIELDS:
    post_delete.connect(
        _cleanup_media, sender=_model, dispatch_uid=f"media_cleanup_{_model.__name__}"
    )


def _notify_admin_by_email(subject: str, message: str) -> None:
    try:
        send_mail(
            subject=f"[IMSO Admin] {subject}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=True,
        )
    except Exception:
        pass


@receiver(pre_save, sender=Payment)
def stash_old_payment_status(sender: type[Payment], instance: Payment, **kwargs: Any) -> None:
    if instance.pk:
        try:
            instance._old_status = Payment.objects.get(pk=instance.pk).status
        except Payment.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(pre_save, sender=VenueBooking)
def stash_old_booking_status(sender: type[VenueBooking], instance: VenueBooking, **kwargs: Any) -> None:
    if instance.pk:
        try:
            instance._old_status = VenueBooking.objects.get(pk=instance.pk).status
        except VenueBooking.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=VenueBooking)
def venue_booking_notification(sender: type[VenueBooking], instance: VenueBooking, created: bool, **kwargs: Any) -> None:
    if created:
        AdminNotification.objects.create(
            message=f"Nouvelle réservation de {instance.requester_name} pour {instance.event_type}",
            notification_type=AdminNotification.NotificationType.NEW_BOOKING,
            related_id=instance.pk,
        )
        _notify_admin_by_email(
            "Nouvelle réservation",
            f"Réservation #{instance.pk}\n\nNom: {instance.requester_name}\nTéléphone: {instance.requester_phone}\nEmail: {instance.requester_email}\nÉvénement: {instance.event_type}\nDate: {instance.event_date}\nHeure: {instance.start_time} - {instance.end_time}",
        )
    else:
        # NE PAS relire la DB ici : en post_save la ligne porte deja le NOUVEAU
        # statut, donc old.status == instance.status et les notifs ne partaient
        # jamais. On compare au statut memorise en pre_save.
        old_status = getattr(instance, "_old_status", None)
        if old_status != instance.status:
            if instance.status == VenueBooking.Status.CONFIRMED:
                nt = AdminNotification.NotificationType.BOOKING_CONFIRMED
                AdminNotification.objects.create(
                    message=f"Réservation confirmée: {instance.event_type}",
                    notification_type=nt,
                    related_id=instance.pk,
                )
                _notify_admin_by_email(
                    "Réservation confirmée",
                    f"Réservation #{instance.pk} confirmée pour {instance.event_type}",
                )
            elif instance.status == VenueBooking.Status.CANCELLED:
                nt = AdminNotification.NotificationType.BOOKING_CANCELLED
                AdminNotification.objects.create(
                    message=f"Réservation annulée: {instance.event_type}",
                    notification_type=nt,
                    related_id=instance.pk,
                )
                _notify_admin_by_email(
                    "Réservation annulée",
                    f"Réservation #{instance.pk} annulée pour {instance.event_type}",
                )


@receiver(post_save, sender=Payment)
def payment_notification(sender: type[Payment], instance: Payment, created: bool, **kwargs: Any) -> None:
    if created:
        AdminNotification.objects.create(
            message=f"Nouveau paiement de {instance.payer_name} - {instance.amount_htg} HTG",
            notification_type=AdminNotification.NotificationType.NEW_PAYMENT,
            related_id=instance.pk,
        )
        _notify_admin_by_email(
            "Nouveau paiement",
            f"Paiement #{instance.pk}\n\nPayeur: {instance.payer_name}\nMontant: {instance.amount_htg} HTG\nRéférence: {instance.reference}\nObjet: {instance.purpose}",
        )
    else:
        # Comparer au statut memorise en pre_save (stash_old_payment_status), pas
        # a une relecture DB qui renverrait deja le nouveau statut en post_save.
        old_status = getattr(instance, "_old_status", None)
        if old_status != instance.status and instance.status == Payment.Status.PAID:
            AdminNotification.objects.create(
                message=f"Paiement reçu: {instance.reference}",
                notification_type=AdminNotification.NotificationType.PAYMENT_RECEIVED,
                related_id=instance.pk,
            )
            _notify_admin_by_email(
                "Paiement reçu",
                f"Paiement reçu: {instance.reference}\nMontant: {instance.amount_htg} HTG\nPayeur: {instance.payer_name}",
            )


@receiver(pre_save, sender=Order)
def stash_old_order_status(sender: type[Order], instance: Order, **kwargs: Any) -> None:
    if instance.pk:
        try:
            instance._old_status = Order.objects.get(pk=instance.pk).status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


def _decrement_order_stock(order: Order) -> None:
    """Decrement ATOMIQUE du stock des produits d'une commande (evite la race
    read-modify-write / la survente)."""
    from django.db.models import F, Value
    from django.db.models.functions import Greatest
    from django.utils import timezone as _tz
    with transaction.atomic():
        for item in order.items.select_related("product"):
            if item.product_id:
                Product.objects.filter(pk=item.product_id).update(
                    stock=Greatest(F("stock") - item.quantity, Value(0)),
                    updated_at=_tz.now(),
                )


@receiver(post_save, sender=Order)
def order_stock_on_paid(sender: type[Order], instance: Order, created: bool, **kwargs: Any) -> None:
    """Source UNIQUE de la decrementation : sur la transition -> PAID, quel que
    soit le declencheur (paiement encaisse OU passage a 'Payee' dans le dashboard)."""
    if created:
        return
    old_status = getattr(instance, "_old_status", None)
    if old_status != Order.Status.PAID and instance.status == Order.Status.PAID:
        _decrement_order_stock(instance)


@receiver(post_save, sender=Payment)
def payment_cascade_status(sender: type[Payment], instance: Payment, created: bool, **kwargs: Any) -> None:
    if created:
        return
    old_status = getattr(instance, '_old_status', None)
    if old_status == instance.status or instance.status != Payment.Status.PAID:
        return
    if instance.venue_booking and instance.venue_booking.status == VenueBooking.Status.PAYMENT_PENDING:
        instance.venue_booking.status = VenueBooking.Status.ADMIN_REVIEW
        instance.venue_booking.save(update_fields=["status", "updated_at"])
    if instance.enrollment and instance.enrollment.status == Enrollment.Status.PENDING:
        instance.enrollment.status = Enrollment.Status.CONFIRMED
        instance.enrollment.save(update_fields=["status", "updated_at"])
    if instance.order and instance.order.status == Order.Status.PENDING:
        # On se contente de passer la commande a PAID : le signal post_save(Order)
        # ci-dessus decremente le stock (source unique, pas de double decrement).
        instance.order.status = Order.Status.PAID
        instance.order.save(update_fields=["status", "updated_at"])


@receiver(post_save, sender=ContactRequest)
def contact_request_notification(sender: type[ContactRequest], instance: ContactRequest, created: bool, **kwargs: Any) -> None:
    if created:
        AdminNotification.objects.create(
            message=f"Nouveau message de {instance.full_name}",
            notification_type=AdminNotification.NotificationType.NEW_CONTACT,
            related_id=instance.pk,
        )
        _notify_admin_by_email(
            "Nouveau message contact",
            f"De: {instance.full_name}\nTéléphone: {instance.phone}\nEmail: {instance.email}\nSujet: {instance.subject}\nMessage: {instance.message}",
        )
