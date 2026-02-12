from django.db import migrations
import shortuuid

def populate_slugs(apps, schema_editor):
    Question = apps.get_model("polls", "Question")
    Option = apps.get_model("polls", "Option")
    Vote = apps.get_model("polls", "Vote")

    for question in Question.objects.all():
        if not question.slug:
            question.slug = shortuuid.ShortUUID().random(length=8)
            question.save(update_fields=["slug"])

    for option in Option.objects.all():
        if not option.slug:
            option.slug = shortuuid.ShortUUID().random(length=8)
            option.save(update_fields=["slug"])

    for vote in Vote.objects.all():
        if not vote.slug:
            vote.slug = shortuuid.ShortUUID().random(length=8)
            vote.save(update_fields=["slug"])

class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0008_vote_slug'),
    ]

    operations = [
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
    ]
