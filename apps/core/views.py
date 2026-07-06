from __future__ import annotations

import json
import logging
from typing import Any

from django_ratelimit.decorators import ratelimit
from django.db import transaction
from django.core.signing import BadSignature
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, RedirectView

from apps.adminpanel.models import (
    BlogPost,
    Course,
    Enrollment,
    GEI,
    Member,
    Order,
    OrderItem,
    Payment,
    PaymentProvider,
    Product,
    Testimonial,
    VenueBooking,
)
from .forms import ContactRequestForm, CourseEnrollmentRequestForm, VenueBookingRequestForm
from .payment_tokens import make_payment_token, read_payment_token

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "core/index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        courses = Course.objects.filter(is_active=True).only(
            "id", "title", "category", "city", "instructor", "price_htg", "capacity", "description", "public_slug"
        )
        context["active_courses"] = courses

        context["active_providers"] = PaymentProvider.objects.filter(is_active=True).only(
            "id", "name", "provider_type", "instructions", "checkout_url", "sort_order"
        )

        context["total_members"] = Member.objects.filter(status=Member.Status.ACTIVE).count()
        context["total_courses"] = courses.count()
        context["total_geis"] = GEI.objects.filter(is_active=True).count()

        context["testimonials"] = Testimonial.objects.filter(is_active=True)

        context["products"] = Product.objects.filter(is_active=True).only(
            "id", "name", "slug", "kind", "description", "price_htg", "stock", "sort_order", "image"
        )

        return context


class BlogListView(TemplateView):
    template_name = "core/blog_list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["posts"] = BlogPost.objects.filter(
            status=BlogPost.Status.PUBLISHED, published_at__lte=timezone.now()
        ).order_by("-published_at")
        context["page_title"] = "Blog"
        return context


class BlogDetailView(TemplateView):
    template_name = "core/blog_detail.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        post = get_object_or_404(
            BlogPost,
            slug=kwargs.get("slug"),
            status=BlogPost.Status.PUBLISHED,
            published_at__lte=timezone.now(),
        )
        context["post"] = post
        # <title>/OG propres a l'article (etaient le titre generique du site).
        context["page_title"] = post.title
        return context


def healthcheck(_request: HttpRequest) -> JsonResponse:
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    from django.utils import timezone

    result = {
        "service": "imso",
        "database": "unknown",
        "migrations": "unknown",
        "timestamp": timezone.now().isoformat(),
        "version": "1.0.0",
    }

    try:
        connection.ensure_connection()
        result["database"] = "connected"
    except Exception as exc:
        logger.warning("Healthcheck: DB unreachable — %s", exc)
        result["database"] = "disconnected"
        result["status"] = "error"
        result["timestamp"] = timezone.now().isoformat()
        return JsonResponse(result)

    try:
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        result["migrations"] = "up_to_date" if not plan else "pending"
    except Exception:
        result["migrations"] = "unknown"

    result["status"] = "degraded" if result["migrations"] == "pending" else "ok"
    return JsonResponse(result)


class ContactRequestCreateView(View):
    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True))
    def post(self, request: HttpRequest) -> JsonResponse:
        payload = request.POST
        if request.content_type == "application/json":
            try:
                payload = json.loads(request.body.decode("utf-8"))
            except json.JSONDecodeError:
                return JsonResponse({"ok": False, "errors": {"body": ["JSON invalide"]}}, status=400)

        form = ContactRequestForm(payload)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)

        contact = form.save()
        return JsonResponse({"ok": True, "id": contact.id}, status=201)


class VenueBookingCreateView(View):
    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True))
    def post(self, request: HttpRequest) -> JsonResponse:
        payload = request.POST
        if request.content_type == "application/json":
            try:
                payload = json.loads(request.body.decode("utf-8"))
            except json.JSONDecodeError:
                return JsonResponse({"ok": False, "errors": {"body": ["JSON invalide"]}}, status=400)

        form = VenueBookingRequestForm(payload)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)

        # Anti double-reservation : si le creneau est deja pris (reservation en
        # paiement / validee / confirmee), on refuse au lieu de creer un doublon.
        from .venue import slot_taken
        cd = form.cleaned_data
        if slot_taken(cd["event_date"], cd["start_time"], cd["end_time"]):
            return JsonResponse({
                "ok": False,
                "errors": {"event_date": ["Ce créneau vient d'être réservé. Merci d'en choisir un autre."]},
            }, status=409)

        booking = form.save()
        return JsonResponse({
            "ok": True,
            "id": booking.id,
            "payment_url": f"/paiement/reservation/{make_payment_token('reservation', booking.id)}/",
        }, status=201)


class CourseEnrollmentCreateView(View):
    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True))
    def post(self, request: HttpRequest) -> JsonResponse:
        payload = request.POST
        if request.content_type == "application/json":
            try:
                payload = json.loads(request.body.decode("utf-8"))
            except json.JSONDecodeError:
                return JsonResponse({"ok": False, "errors": {"body": ["JSON invalide"]}}, status=400)

        form = CourseEnrollmentRequestForm(payload)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)

        member = form.get_or_create_member()
        course_id = form.cleaned_data.get("course_id")
        course_title = form.cleaned_data.get("course_title")
        course_price = form.cleaned_data.get("course_price_htg", 0)

        course = None
        if course_id:
            course = get_object_or_404(Course, id=course_id)

        # Idempotent : une 2e inscription (double-clic, retour pour repayer) au
        # meme cours reutilise l'inscription existante au lieu de violer la
        # contrainte unique (member, course) -> plus de 500.
        try:
            enrollment, created = Enrollment.objects.get_or_create(
                member=member,
                course=course,
                defaults={"status": Enrollment.Status.PENDING},
            )
        except IntegrityError:
            # Race concurrente : recuperer l'inscription creee entre-temps.
            enrollment = Enrollment.objects.filter(member=member, course=course).order_by("id").first()
            if enrollment is None:
                raise
            created = False

        return JsonResponse({
            "ok": True,
            "id": enrollment.id,
            "payment_url": f"/paiement/cours/{make_payment_token('cours', enrollment.id)}/",
        }, status=201 if created else 200)


from django.core.serializers.json import DjangoJSONEncoder


class PaymentPageView(TemplateView):
    template_name = "core/paiement.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        providers = PaymentProvider.objects.filter(is_active=True).only(
            "id", "name", "provider_type", "instructions", "checkout_url", "sort_order"
        )
        context["providers"] = providers
        _providers_raw = json.dumps(list(providers.values(
            "id", "name", "provider_type", "instructions", "checkout_url", "sort_order"
        )), cls=DjangoJSONEncoder)
        # Injecte dans un <script> via |safe : echapper < > & (comme le fait
        # json_script de Django) sinon un champ "instructions" contenant
        # "</script>" ferme la balise et casse toute la page (et ouvre un XSS).
        context["providers_json"] = (
            _providers_raw.replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
        )

        payment_type = kwargs.get("type")
        # Le jeton signé remplace l'id séquentiel : illisible/infalsifiable sans SECRET_KEY.
        try:
            payment_id = read_payment_token(payment_type, kwargs.get("token") or "")
        except (BadSignature, ValueError, TypeError):
            raise Http404("Lien de paiement invalide.")
        # Le template rejoue le POST vers l'API avec ce même jeton (jamais l'id brut).
        context["payment_token"] = kwargs.get("token")

        context["payment_purpose"] = "other"
        context["payment_label"] = "Paiement"
        context["amount_htg"] = 0
        context["payer_name"] = ""
        context["payer_phone"] = ""
        context["payer_email"] = ""
        context["booking_id"] = None
        context["enrollment_id"] = None
        context["order_id"] = None

        if payment_type == "reservation":
            booking = get_object_or_404(VenueBooking, id=payment_id)
            context["booking"] = booking
            context["payment_purpose"] = "venue"
            context["payment_label"] = f"Réservation de salle - {booking.event_type}"
            context["amount_htg"] = 0
            context["payer_name"] = booking.requester_name
            context["payer_phone"] = booking.requester_phone
            context["payer_email"] = booking.requester_email
            context["booking_id"] = booking.id
        elif payment_type == "cours":
            enrollment = get_object_or_404(
                Enrollment.objects.select_related("member", "course"),
                id=payment_id,
            )
            context["enrollment"] = enrollment
            context["payment_purpose"] = "course"
            context["payment_label"] = f"Inscription - {enrollment.course.title if enrollment.course else 'Cours'}"
            context["amount_htg"] = enrollment.course.price_htg if enrollment.course else 0
            context["payer_name"] = f"{enrollment.member.first_name} {enrollment.member.last_name}".strip()
            context["payer_phone"] = enrollment.member.phone
            context["payer_email"] = enrollment.member.email
            context["enrollment_id"] = enrollment.id
        elif payment_type == "commande":
            order = get_object_or_404(Order, id=payment_id)
            context["order"] = order
            context["payment_purpose"] = "product"
            context["payment_label"] = f"Commande {order.reference}"
            context["amount_htg"] = order.total_htg
            context["payer_name"] = order.customer_name
            context["payer_phone"] = order.customer_phone
            context["payer_email"] = order.customer_email
            context["order_id"] = order.id

        return context


class PaymentProcessView(View):
    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True))
    def post(self, request: HttpRequest, type: str, token: str) -> JsonResponse:
        # Jeton signé -> id d'origine (empêche l'énumération/l'usurpation d'un autre dossier).
        try:
            id = read_payment_token(type, token)
        except (BadSignature, ValueError, TypeError):
            return JsonResponse({"ok": False, "error": "Lien de paiement invalide"}, status=404)
        # Handle both JSON and multipart form data
        if request.content_type and "multipart/form-data" in request.content_type:
            data = request.POST.dict()
        else:
            try:
                data = json.loads(request.body.decode("utf-8"))
            except json.JSONDecodeError:
                return JsonResponse({"ok": False, "error": "JSON invalide"}, status=400)

        provider_id = data.get("provider_id")
        if not provider_id:
            return JsonResponse({"ok": False, "error": "Mode de paiement requis"}, status=400)
        # Coercition avant la requete : un provider_id non entier ferait lever
        # ValueError par l'AutoField -> 500. On renvoie un 400 propre.
        try:
            provider_id = int(provider_id)
        except (TypeError, ValueError):
            return JsonResponse({"ok": False, "error": "Mode de paiement invalide"}, status=400)

        provider = get_object_or_404(PaymentProvider, id=provider_id, is_active=True)

        booking = None
        enrollment = None
        order = None
        purpose = Payment.Purpose.OTHER
        amount = 0
        payer_name = data.get("payer_name", "")
        payer_phone = data.get("payer_phone", "")
        payer_email = data.get("payer_email", "")

        if type == "reservation":
            booking = get_object_or_404(VenueBooking, id=id)
            purpose = Payment.Purpose.VENUE
            payer_name = payer_name or booking.requester_name
            payer_phone = payer_phone or booking.requester_phone
            payer_email = payer_email or booking.requester_email
            if booking.status == VenueBooking.Status.REQUESTED:
                booking.status = VenueBooking.Status.PAYMENT_PENDING
                booking.save(update_fields=["status", "updated_at"])
        elif type == "cours":
            enrollment = get_object_or_404(
                Enrollment.objects.select_related("member", "course"),
                id=id,
            )
            purpose = Payment.Purpose.COURSE
            amount = enrollment.course.price_htg if enrollment.course else 0
            payer_name = payer_name or f"{enrollment.member.first_name} {enrollment.member.last_name}".strip()
            payer_phone = payer_phone or enrollment.member.phone
            payer_email = payer_email or enrollment.member.email
        elif type == "commande":
            order = get_object_or_404(Order, id=id)
            purpose = Payment.Purpose.PRODUCT
            amount = order.total_htg
            payer_name = payer_name or order.customer_name
            payer_phone = payer_phone or order.customer_phone
            payer_email = payer_email or order.customer_email

        # Extract fields from JSON or form-data
        transaction_id = ""
        screenshot_file = None
        if request.content_type and "application/json" in request.content_type:
            transaction_id = data.get("transaction_id", "")
        elif request.content_type and "multipart/form-data" in request.content_type:
            transaction_id = request.POST.get("transaction_id", "")
            screenshot_file = request.FILES.get("screenshot")

        is_manual = provider.provider_type in (
            PaymentProvider.ProviderType.MANUAL,
            PaymentProvider.ProviderType.MONCASH,
            PaymentProvider.ProviderType.NATCASH,
            PaymentProvider.ProviderType.BANK,
            PaymentProvider.ProviderType.CASH,
        )

        notes = f"Paiement initié via {provider.name}"
        if transaction_id:
            notes += f" · TX: {transaction_id}"

        payment = Payment.objects.create(
            purpose=purpose,
            provider=provider,
            status=Payment.Status.PENDING,
            entry_mode=Payment.EntryMode.CLIENT,
            payer_name=payer_name,
            payer_phone=payer_phone,
            payer_email=payer_email,
            amount_htg=amount,
            venue_booking=booking,
            enrollment=enrollment,
            order=order,
            notes=notes,
        )

        # Preuve de paiement (capture mobile money) televersee en multipart :
        # la persister sur le paiement, sinon l'admin ne voit jamais la preuve.
        if screenshot_file:
            ct = getattr(screenshot_file, "content_type", "") or ""
            if ct.startswith("image/") and screenshot_file.size <= 5 * 1024 * 1024:
                try:
                    payment.screenshot.save(screenshot_file.name, screenshot_file)
                except Exception:
                    logger.warning("Echec sauvegarde screenshot paiement %s", payment.id)

        if provider.checkout_url:
            return JsonResponse({
                "ok": True,
                "payment_id": payment.id,
                "reference": payment.reference,
                "redirect_url": provider.checkout_url,
            })

        resp = {
            "ok": True,
            "payment_id": payment.id,
            "reference": payment.reference,
            "message": "Paiement enregistré. En attente de validation.",
            "instructions": provider.instructions,
            "is_manual": is_manual,
        }

        if is_manual and amount > 0:
            resp["amount_htg"] = amount
            resp["total_label"] = f"{amount:,} HTG"

        return JsonResponse(resp)


class PaymentConfirmationView(View):
    def get(self, request: HttpRequest, reference: str) -> JsonResponse:
        payment = get_object_or_404(Payment, reference=reference)
        return JsonResponse({
            "ok": True,
            "reference": payment.reference,
            "status": payment.status,
            "purpose": payment.purpose,
            "amount_htg": payment.amount_htg,
            "paid_at": payment.paid_at,
        })


from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import os


@csrf_exempt  # appel serveur-a-serveur authentifie par X-API-KEY (comme le webhook)
@require_http_methods(["POST"])
def confirm_manual_payment(request: HttpRequest) -> JsonResponse:
    """Confirms a manual payment with transaction ID and optional screenshot."""
    api_key = request.META.get("HTTP_X_API_KEY")
    expected_key = os.environ.get("PAYMENT_CONFIRM_KEY")
    if not api_key or api_key != expected_key:
        return JsonResponse({"ok": False, "error": "Clé API invalide"}, status=403)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        # Try multipart form data
        data = request.POST.dict()

    reference = data.get("payment_reference")
    if not reference:
        return JsonResponse({"ok": False, "error": "Référence de paiement requise"}, status=400)

    payment = get_object_or_404(Payment, reference=reference)

    if payment.external_reference:
        logger.info("Payment %s already confirmed, skipping", reference)
        return JsonResponse({
            "ok": True,
            "reference": payment.reference,
            "message": "Paiement déjà confirmé.",
        })

    transaction_id = data.get("transaction_id", "")
    screenshot_file = request.FILES.get("screenshot")

    notes = payment.notes or ""
    if transaction_id:
        notes += f" | Confirmation manuelle - Transaction: {transaction_id}"
    else:
        notes += " | Confirmation manuelle (sans ID transaction)"
    if screenshot_file:
        notes += " + Screenshot fourni"

    payment.notes = notes
    payment.external_reference = transaction_id or payment.external_reference
    if screenshot_file:
        payment.screenshot.save(screenshot_file.name, screenshot_file)
    payment.save(update_fields=["notes", "external_reference"])

    return JsonResponse({
        "ok": True,
        "reference": payment.reference,
        "message": "Confirmation reçue. Un administrateur validera sous 24h.",
    })


def get_active_providers(request: HttpRequest) -> JsonResponse:
    providers = PaymentProvider.objects.filter(is_active=True).values(
        "id", "name", "provider_type", "instructions", "checkout_url", "sort_order"
    )
    return JsonResponse(list(providers), safe=False)


def get_active_courses(request: HttpRequest) -> JsonResponse:
    courses = Course.objects.filter(is_active=True).values(
        "id", "title", "category", "city", "instructor", "price_htg", "capacity", "description", "public_slug"
    )
    return JsonResponse(list(courses), safe=False)


def get_active_products(request: HttpRequest) -> JsonResponse:
    """Liste publique des produits en vente (boutique du kit)."""
    products = Product.objects.filter(is_active=True).values(
        "id", "name", "slug", "kind", "description", "price_htg", "stock", "sort_order"
    )
    return JsonResponse(list(products), safe=False)


class OrderCreateView(View):
    """Crée une commande boutique. Le total est TOUJOURS recalculé côté serveur
    à partir des prix en base — jamais depuis les montants envoyés par le client."""

    @method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True))
    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"ok": False, "error": "JSON invalide"}, status=400)

        name = (data.get("customer_name") or "").strip()
        phone = (data.get("customer_phone") or "").strip()
        address = (data.get("delivery_address") or "").strip()
        items = data.get("items") or []

        errors: dict[str, list[str]] = {}
        if not name:
            errors["customer_name"] = ["Nom requis."]
        if not phone:
            errors["customer_phone"] = ["Téléphone requis."]
        if not address:
            errors["delivery_address"] = ["Adresse de livraison requise."]
        if not isinstance(items, list) or not items:
            errors["items"] = ["Le panier est vide."]
        if errors:
            return JsonResponse({"ok": False, "errors": errors}, status=400)

        with transaction.atomic():
            order = Order.objects.create(
                customer_name=name,
                customer_phone=phone,
                customer_email=(data.get("customer_email") or "").strip(),
                delivery_address=address,
                city=(data.get("city") or "").strip(),
                note=(data.get("note") or "").strip(),
            )
            total = 0
            for raw in items:
                try:
                    qty = int(raw.get("quantity", 1))
                except (TypeError, ValueError, AttributeError):
                    continue
                if qty < 1:
                    continue
                qty = min(qty, 1000)  # borne haute (evite le depassement d'entier / commandes absurdes)
                try:
                    product = Product.objects.get(id=raw.get("product_id"), is_active=True)
                except (Product.DoesNotExist, ValueError, TypeError):
                    continue
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    quantity=qty,
                    unit_price_htg=product.price_htg,
                )
                total += qty * product.price_htg

            if total <= 0:
                order.delete()
                return JsonResponse(
                    {"ok": False, "error": "Aucun produit valide dans la commande."},
                    status=400,
                )
            order.total_htg = total
            order.save(update_fields=["total_htg", "updated_at"])

        return JsonResponse(
            {
                "ok": True,
                "id": order.id,
                "reference": order.reference,
                "total_htg": order.total_htg,
                "payment_url": f"/paiement/commande/{make_payment_token('commande', order.id)}/",
            },
            status=201,
        )


# ── SEO : robots.txt & sitemap.xml ───────────────────────────────
@require_http_methods(["GET"])
def robots_txt(request: HttpRequest) -> HttpResponse:
    host = f"{request.scheme}://{request.get_host()}"
    body = "\n".join([
        "User-agent: *",
        "Allow: /",
        "Disallow: /dashboard/",
        "Disallow: /django-admin/",
        "Disallow: /api/",
        f"Sitemap: {host}/sitemap.xml",
    ])
    return HttpResponse(body + "\n", content_type="text/plain")


@require_http_methods(["GET"])
def sitemap_xml(request: HttpRequest) -> HttpResponse:
    from django.utils.html import escape
    host = f"{request.scheme}://{request.get_host()}"
    paths = ["/", "/blog/", "/formation/"]
    try:
        slugs = BlogPost.objects.filter(
            status=BlogPost.Status.PUBLISHED, published_at__lte=timezone.now()
        ).values_list("slug", flat=True)
        paths += [f"/blog/{s}/" for s in slugs if s]
    except Exception:
        pass
    urls = "".join(f"<url><loc>{escape(host + p)}</loc></url>" for p in paths)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{urls}</urlset>"
    )
    return HttpResponse(xml, content_type="application/xml")


# ── Disponibilité des créneaux de réservation de salle ───────────
@require_http_methods(["GET"])
def venue_availability(request: HttpRequest) -> JsonResponse:
    """Créneaux OCCUPÉS (réservation en paiement / validée / confirmée) sur une
    plage de dates, pour que le calendrier public affiche la vraie disponibilité.

    GET /api/venue-availability/?from=YYYY-MM-DD&to=YYYY-MM-DD
    -> {"occupied": {"2026-08-01": ["matin"], ...}, "slots": ["matin","aprem","soir"]}
    """
    from datetime import timedelta
    from django.utils.dateparse import parse_date
    from .venue import VENUE_SLOTS, OCCUPIED_STATUSES, occupied_slots_for

    def _d(raw):
        try:
            return parse_date(str(raw or "")) or None
        except (ValueError, TypeError):
            return None

    today = timezone.localdate()
    frm = _d(request.GET.get("from")) or today
    to = _d(request.GET.get("to")) or (frm + timedelta(days=120))
    # Fenêtre bornée (max ~6 mois) pour éviter une requête non maîtrisée.
    if (to - frm).days > 186:
        to = frm + timedelta(days=186)
    if to < frm:
        to = frm

    qs = VenueBooking.objects.filter(
        status__in=OCCUPIED_STATUSES, event_date__gte=frm, event_date__lte=to
    ).only("event_date", "start_time", "end_time")
    occ = occupied_slots_for(qs)
    return JsonResponse({
        "occupied": {d: sorted(s) for d, s in occ.items()},
        "slots": [s[0] for s in VENUE_SLOTS],
    })
