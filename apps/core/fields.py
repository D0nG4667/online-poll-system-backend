import shortuuid
from django.db import models


class RandomSlugField(models.SlugField):
    """
    A field that automatically generates a unique, random slug if not provided.
    Encapsulates generation logic away from the Model.save() method.
    """

    def __init__(self, *args, length=8, **kwargs):
        self.length = length
        kwargs.setdefault("max_length", 12)
        kwargs.setdefault("unique", True)
        kwargs.setdefault("blank", True)
        kwargs.setdefault("db_index", True)
        kwargs.setdefault(
            "default", ""
        )  # Principal fix: provide dummy default for migrations
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["length"] = self.length
        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        """
        Generate slug before saving if it doesn't exist.
        """
        current_value = getattr(model_instance, self.attname)
        if not current_value:
            new_slug = self._generate_unique_slug(model_instance)
            setattr(model_instance, self.attname, new_slug)
            return new_slug
        return super().pre_save(model_instance, add)

    def _generate_unique_slug(self, instance):
        model_class = instance.__class__
        # Principal Pattern: The "Verify & Retry" loop
        for _ in range(10):  # Maximum retries for collisions
            slug = shortuuid.ShortUUID().random(length=self.length)
            if not model_class.objects.filter(**{self.attname: slug}).exists():
                return slug

        # Ultimate fallback to a longer, safer string if the space is crowded
        return shortuuid.uuid()[: self.max_length]
