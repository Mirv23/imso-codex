from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Course",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=180)),
                ("category", models.CharField(max_length=80)),
                ("instructor", models.CharField(max_length=120)),
                ("city", models.CharField(max_length=120)),
                ("price_htg", models.PositiveIntegerField(default=0)),
                ("capacity", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["category", "title"]},
        ),
        migrations.CreateModel(
            name="DashboardMetric",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("label", models.CharField(max_length=120)),
                ("value", models.CharField(max_length=40)),
                ("helper", models.CharField(blank=True, max_length=160)),
                ("sort_order", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ["sort_order", "label"]},
        ),
        migrations.CreateModel(
            name="GEI",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=120)),
                ("city", models.CharField(max_length=120)),
                ("coordinator", models.CharField(blank=True, max_length=120)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"verbose_name": "GEI", "verbose_name_plural": "GEI", "ordering": ["city", "name"]},
        ),
        migrations.CreateModel(
            name="ContactRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("full_name", models.CharField(max_length=140)),
                ("phone", models.CharField(max_length=40)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("subject", models.CharField(choices=[("membership", "Adhesion a un GEI"), ("course", "Inscription a un cours"), ("venue", "Location de salle"), ("mentor", "Devenir mentor"), ("other", "Autre")], default="membership", max_length=30)),
                ("message", models.TextField(blank=True)),
                ("is_processed", models.BooleanField(default=False)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Member",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("first_name", models.CharField(max_length=80)),
                ("last_name", models.CharField(max_length=80)),
                ("phone", models.CharField(max_length=40)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("status", models.CharField(choices=[("prospect", "Prospect"), ("active", "Actif"), ("paused", "En pause"), ("alumni", "Ancien membre")], default="prospect", max_length=20)),
                ("joined_at", models.DateField(blank=True, null=True)),
                ("monthly_saving_htg", models.PositiveIntegerField(default=0)),
                ("gei", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="members", to="adminpanel.gei")),
            ],
            options={"ordering": ["last_name", "first_name"]},
        ),
        migrations.CreateModel(
            name="VenueBooking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("requester_name", models.CharField(max_length=140)),
                ("requester_phone", models.CharField(max_length=40)),
                ("event_type", models.CharField(max_length=80)),
                ("event_date", models.DateField()),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("guest_count", models.PositiveIntegerField(default=0)),
                ("status", models.CharField(choices=[("requested", "Demandee"), ("confirmed", "Confirmee"), ("cancelled", "Annulee")], default="requested", max_length=20)),
                ("notes", models.TextField(blank=True)),
            ],
            options={"ordering": ["event_date", "start_time"]},
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(choices=[("pending", "En attente"), ("confirmed", "Confirmee"), ("cancelled", "Annulee")], default="pending", max_length=20)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="adminpanel.course")),
                ("member", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="adminpanel.member")),
            ],
            options={"ordering": ["-created_at"], "unique_together": {("member", "course")}},
        ),
    ]
