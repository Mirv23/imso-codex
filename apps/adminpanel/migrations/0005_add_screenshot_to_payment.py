# Generated manually for Phase 4 — screenshot field on Payment

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0004_adminnotification'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='screenshot',
            field=models.FileField(blank=True, upload_to='screenshots/'),
        ),
    ]
