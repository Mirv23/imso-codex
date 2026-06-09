from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import ContactRequest, Enrollment, Payment, VenueBooking, AdminNotification


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
        try:
            old = VenueBooking.objects.get(pk=instance.pk)
            if old.status != instance.status:
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
        except VenueBooking.DoesNotExist:
            pass


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
        try:
            old = Payment.objects.get(pk=instance.pk)
            if old.status != instance.status and instance.status == Payment.Status.PAID:
                AdminNotification.objects.create(
                    message=f"Paiement reçu: {instance.reference}",
                    notification_type=AdminNotification.NotificationType.PAYMENT_RECEIVED,
                    related_id=instance.pk,
                )
                _notify_admin_by_email(
                    "Paiement reçu",
                    f"Paiement reçu: {instance.reference}\nMontant: {instance.amount_htg} HTG\nPayeur: {instance.payer_name}",
                )
        except Payment.DoesNotExist:
            pass


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
