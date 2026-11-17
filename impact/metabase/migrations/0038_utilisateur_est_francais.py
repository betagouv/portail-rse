from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("metabase", "0037_entreprise_code_pays_identifiant"),
    ]

    operations = [
        migrations.AddField(
            model_name="utilisateur",
            name="est_francais",
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]
