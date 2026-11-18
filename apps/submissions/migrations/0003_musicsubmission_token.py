import uuid

from django.db import migrations, models


def add_tokens(apps, schema_editor):
    MusicSubmission = apps.get_model("submissions", "MusicSubmission")
    for submission in MusicSubmission.objects.filter(token__isnull=True):
        submission.token = uuid.uuid4()
        submission.save(update_fields=["token"])


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="musicsubmission",
            name="token",
            field=models.UUIDField(editable=False, null=True, verbose_name="شناسه پیگیری"),
        ),
        migrations.RunPython(add_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="musicsubmission",
            name="token",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, unique=True, verbose_name="شناسه پیگیری"
            ),
        ),
    ]
