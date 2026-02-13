from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.fields import RandomSlugField


class Poll(models.Model):
    """
    Represents a Poll created by a user.
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="polls"
    )
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = RandomSlugField(length=8, help_text=_("Public shareable identifier"))
    start_date = models.DateTimeField(_("Start Date"), default=timezone.now)
    end_date = models.DateTimeField(_("End Date"), null=True, blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Poll")
        verbose_name_plural = _("Polls")

    # index by slug
    indexes = [
        models.Index(fields=["slug"]),
    ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args: Any, **kwargs: Any) -> None:
        super().save(*args, **kwargs)

    @property
    def is_open(self) -> bool:
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True


class Question(models.Model):
    """
    A Question within a Poll.
    """

    QUESTION_TYPES = (
        ("single", _("Single Choice")),
        ("multiple", _("Multiple Choice")),
        ("text", _("Text Answer")),  # Future scope? But good to have enum
    )

    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="questions")
    text = models.CharField(_("Question Text"), max_length=500)
    question_type = models.CharField(
        _("Type"), max_length=20, choices=QUESTION_TYPES, default="single"
    )
    order = models.PositiveIntegerField(_("Order"), default=0)
    slug = RandomSlugField(length=8, unique=True, null=False)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")

    def __str__(self) -> str:
        return self.text


class Option(models.Model):
    """
    An Option for a Question.
    """

    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="options"
    )
    text = models.CharField(_("Option Text"), max_length=255)
    order = models.PositiveIntegerField(_("Order"), default=0)
    slug = RandomSlugField(length=8, unique=True, null=False)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = _("Option")
        verbose_name_plural = _("Options")

    def __str__(self) -> str:
        return self.text


class Vote(models.Model):
    """
    A Vote cast by a user on a specific Option.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="votes"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="votes"
    )
    option = models.ForeignKey(
        Option, on_delete=models.CASCADE, related_name="votes"
    )  # For text answers, this might be null?
    # But for single/multiple choice it's required.
    created_at = models.DateTimeField(auto_now_add=True)
    slug = RandomSlugField(length=8, unique=True, null=False)

    class Meta:
        verbose_name = _("Vote")
        verbose_name_plural = _("Votes")
        unique_together = ["user", "question"]

    def __str__(self) -> str:
        return f"{self.user} voted on {self.question}"


class PollView(models.Model):
    """
    Tracks every time a poll is viewed.
    """

    poll = models.ForeignKey(Poll, related_name="views", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Poll View")
        verbose_name_plural = _("Poll Views")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"View of {self.poll.title} at {self.created_at}"
