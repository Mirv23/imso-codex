from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ContactRequest, Payment, VenueBooking, AdminNotification


@receiver(post_save, sender=VenueBooking)
def venue_booking_notification(sender, instance, created, **kwargs):
    if created:
        AdminNotification.objects.create(
            message=f"Nouvelle réservation de {instance.requester_name} pour {instance.event_type}",
            notification_type=AdminNotification.NotificationType.NEW_BOOKING,
            related_id=instance.pk,
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
                elif instance.status == VenueBooking.Status.CANCELLED:
                    nt = AdminNotification.NotificationType.BOOKING_CANCELLED
                    AdminNotification.objects.create(
                        message=f"Réservation annulée: {instance.event_type}",
                        notification_type=nt,
                        related_id=instance.pk,
                    )
        except VenueBooking.DoesNotExist:
            pass


@receiver(post_save, sender=Payment)
def payment_notification(sender, instance, created, **kwargs):
    if created:
        AdminNotification.objects.create(
            message=f"Nouveau paiement de {instance.payer_name} - {instance.amount_htg} HTG",
            notification_type=AdminNotification.NotificationType.NEW_PAYMENT,
            related_id=instance.pk,
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
        except Payment.DoesNotExist:
            pass


@receiver(post_save, sender=ContactRequest)
def contact_request_notification(sender, instance, created, **kwargs):
    if created:
        AdminNotification.objects.create(
            message=f"Nouveau message de {instance.full_name}",
            notification_type=AdminNotification.NotificationType.NEW_CONTACT,
            related_id=instance.pk,
        )
