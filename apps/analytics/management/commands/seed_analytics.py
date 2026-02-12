from datetime import timedelta  # noqa: I001
import random
from typing import Any


from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from apps.polls.models import Option, Poll, PollView, Question, Vote

User = get_user_model()
fake = Faker()
secure_random = random.SystemRandom()


class Command(BaseCommand):
    help = "Seeds the database with analytics data (Polls, Votes, Views)"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--users", type=int, default=10, help="Number of users to create"
        )
        parser.add_argument(
            "--polls", type=int, default=5, help="Number of polls to create"
        )
        parser.add_argument(
            "--votes",
            type=int,
            default=100,
            help="Appropriate number of votes to generate",
        )
        parser.add_argument(
            "--views",
            type=int,
            default=200,
            help="Appropriate number of views to generate",
        )

    def handle(self, *args: Any, **options: Any) -> None:  # noqa: C901
        self.stdout.write(self.style.WARNING("Starting analytics seeding..."))

        num_users = options["users"]
        num_polls = options["polls"]
        target_votes = options["votes"]
        target_views = options["views"]

        with transaction.atomic():
            # 1. Create Users
            users: list[Any] = []
            for _ in range(num_users):
                email = fake.email()
                if not User.objects.filter(email=email).exists():
                    user = User.objects.create_user(
                        email=email,
                        password="password123",  # noqa: S106
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                    )
                    users.append(user)
                else:
                    users.append(User.objects.get(email=email))

            # Add a demo user for easy login
            demo_email = "demo@example.com"
            if not User.objects.filter(email=demo_email).exists():
                demo_user = User.objects.create_user(
                    email=demo_email,
                    password="password123",  # noqa: S106
                    first_name="Demo",
                    last_name="User",
                )
                users.append(demo_user)
            else:
                users.append(User.objects.get(email=demo_email))

            self.stdout.write(self.style.SUCCESS(f"Created/Loaded {len(users)} users"))

            # 2. Create Polls
            polls = []
            for _ in range(num_polls):
                creator = secure_random.choice(users)
                # Spread creation time over last 30 days
                days_ago = secure_random.randint(0, 30)
                created_at = timezone.now() - timedelta(days=days_ago)

                poll = Poll.objects.create(
                    title=fake.sentence(nb_words=6).rstrip("."),
                    description=fake.paragraph(),
                    created_by=creator,
                    start_date=created_at,
                    end_date=created_at + timedelta(days=30),
                    is_active=True,
                )
                # Hack to set created_at
                # (since auto_now_add=True overrides it on creation)
                Poll.objects.filter(id=poll.id).update(created_at=created_at)
                poll.refresh_from_db()
                polls.append(poll)

                # Create Questions and Options
                for q_idx in range(secure_random.randint(2, 4)):
                    question = Question.objects.create(
                        poll=poll,
                        text=fake.sentence(nb_words=8).rstrip("?") + "?",
                        question_type="single",
                        order=q_idx,
                    )
                    for o_idx in range(secure_random.randint(2, 5)):
                        Option.objects.create(
                            question=question,
                            text=fake.word().title(),
                            order=o_idx,
                        )

            self.stdout.write(
                self.style.SUCCESS(f"Created {len(polls)} polls with questions")
            )

            # 3. Generate Views
            # We want views distributed over time
            views_created = 0
            for _ in range(target_views):
                poll = secure_random.choice(polls)
                viewer = (
                    secure_random.choice(users)
                    if secure_random.random() > 0.3
                    else None
                )  # 30% anonymous views

                # View time should be after poll creation
                days_since_creation = (timezone.now() - poll.created_at).days
                if days_since_creation < 0:
                    days_since_creation = 0

                view_delay = (
                    secure_random.randint(0, days_since_creation)
                    if days_since_creation > 0
                    else 0
                )
                view_time = poll.created_at + timedelta(days=view_delay)

                view = PollView.objects.create(
                    poll=poll,
                    user=viewer,
                )
                # Update created_at
                PollView.objects.filter(id=view.id).update(created_at=view_time)
                views_created += 1

            self.stdout.write(self.style.SUCCESS(f"Created {views_created} poll views"))

            # 4. Generate Votes
            votes_created = 0
            for _ in range(target_votes):
                poll = secure_random.choice(polls)
                voter = secure_random.choice(users)

                # Ensure user hasn't voted on this poll's questions yet
                # (simplified check)
                # Actually, duplicate votes are blocked by unique_together in Vote model
                # We need to pick a question the user hasn't voted on

                questions = poll.questions.all()
                for question in questions:
                    if not Vote.objects.filter(user=voter, question=question).exists():
                        question_options = question.options.all()
                        if question_options.exists():
                            option: Option = secure_random.choice(question_options)

                            # Vote time similar logic to views
                            days_since_creation = (
                                timezone.now() - poll.created_at
                            ).days
                            if days_since_creation < 0:
                                days_since_creation = 0
                            vote_delay = (
                                secure_random.randint(0, days_since_creation)
                                if days_since_creation > 0
                                else 0
                            )
                            vote_time = poll.created_at + timedelta(days=vote_delay)

                            vote = Vote.objects.create(
                                user=voter,
                                question=question,
                                option=option,
                            )
                            Vote.objects.filter(id=vote.id).update(created_at=vote_time)
                            # One vote per user per iteration loop,
                            # effectively spreading votes
                            votes_created += 1
                            break

            self.stdout.write(self.style.SUCCESS(f"Created {votes_created} votes"))

        self.stdout.write(
            self.style.SUCCESS("Analytics seeding completed successfully!")
        )
