from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("permits", "0005_permitblock_segment_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="streetsegment",
            name="nta_code",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="streetsegment",
            name="nta_name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="streetsegment",
            name="nta_match_status",
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
