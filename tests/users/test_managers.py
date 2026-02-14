import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestCustomUserManager:
    email = "normal@user.com"
    password = "foo"  # pragma: allowlist secret

    def test_create_user(self) -> None:
        user = User.objects.create_user(
            email=self.email, password=self.password
        )  # pragma: allowlist secret
        assert user.email == self.email
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser
        # Check password hashing
        assert user.check_password(self.password)

    def test_create_superuser(self) -> None:
        email = "super@user.com"
        password = "foo"  # pragma: allowlist secret
        admin = User.objects.create_superuser(email=email, password=password)
        assert admin.email == email
        assert admin.is_active
        assert admin.is_staff
        assert admin.is_superuser
        assert admin.check_password(password)

    def test_create_user_no_email(self) -> None:
        with pytest.raises(ValueError, match="The Email must be set"):
            User.objects.create_user(email="", password=self.password)

    def test_create_superuser_invalid_flags(self) -> None:
        with pytest.raises(ValueError, match="Superuser must have is_staff=True"):
            User.objects.create_superuser(
                email="super@user.com", password=self.password, is_staff=False
            )

        with pytest.raises(ValueError, match="Superuser must have is_superuser=True"):
            User.objects.create_superuser(
                email="super@user.com", password=self.password, is_superuser=False
            )
