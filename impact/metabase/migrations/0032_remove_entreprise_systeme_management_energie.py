from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("metabase", "0031_entreprise_code_postal"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="entreprise",
            name="systeme_management_energie",
        ),
    ]
