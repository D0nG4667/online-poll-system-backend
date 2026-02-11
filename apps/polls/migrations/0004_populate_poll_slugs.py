import shortuuid
from django.db import migrations


def populate_slugs(apps, schema_editor):
    Poll = apps.get_model("polls", "Poll")
    for poll in Poll.objects.all():
        if not poll.slug:
            poll.slug = shortuuid.ShortUUID().random(length=8)
            poll.save()


class Migration(migrations.Migration):

    dependencies = [
        ("polls", "0003_poll_slug"),
    ]

    operations = [
        migrations.RunPython(populate_slugs, reverse_code=migrations.RunPython.noop),
    ]
