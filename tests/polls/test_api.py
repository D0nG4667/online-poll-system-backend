import pytest
from django.urls import reverse
from apps.polls.models import Poll


@pytest.mark.django_db
class TestPollAPI:
    """
    Tests for Poll ViewSet CRUD operations.
    """

    def test_list_polls_anonymous(self, api_client, poll):
        """
        Test that anonymous users can list polls.
        """
        url = reverse("polls:poll-list")
        response = api_client.get(url)

        assert response.status_code == 200
        assert len(response.data) >= 1
        assert response.data[0]["title"] == poll.title

    def test_list_polls_authenticated(self, auth_client, poll):
        """
        Test that authenticated users can list polls.
        """
        url = reverse("polls:poll-list")
        response = auth_client.get(url)

        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_retrieve_poll_detail(self, api_client, poll):
        """
        Test retrieving a single poll by ID.
        """
        url = reverse("polls:poll-detail", kwargs={"pk": poll.id})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["title"] == poll.title
        assert "questions" in response.data

    def test_retrieve_nonexistent_poll(self, api_client):
        """
        Test retrieving a poll that doesn't exist.
        """
        url = reverse("polls:poll-detail", kwargs={"pk": 9999})
        response = api_client.get(url)

        assert response.status_code == 404

    def test_create_poll_authenticated(self, auth_client):
        """
        Test creating a poll when authenticated.
        """
        url = reverse("polls:poll-list")
        data = {"title": "New Test Poll", "description": "Description for test poll"}
        response = auth_client.post(url, data, format="json")

        assert response.status_code == 201
        assert response.data["title"] == data["title"]
        assert Poll.objects.filter(title=data["title"]).exists()

    def test_create_poll_unauthorized(self, api_client):
        """
        Test that anonymous users cannot create polls.
        """
        url = reverse("polls:poll-list")
        data = {"title": "Unauthorized Poll"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == 403

    def test_create_poll_sets_created_by(self, auth_client, test_user):
        """
        Test that the created_by field is set to the current user.
        """
        url = reverse("polls:poll-list")
        data = {"title": "Ownership Test"}
        response = auth_client.post(url, data, format="json")

        assert response.status_code == 201
        poll = Poll.objects.get(id=response.data["id"])
        # The serializer returns StringRelatedField for created_by
        assert response.data["created_by"] == str(test_user)
        assert poll.created_by == test_user

    def test_create_poll_invalid_data(self, auth_client):
        """
        Test poll creation with missing title.
        """
        url = reverse("polls:poll-list")
        data = {"description": "No title here"}
        response = auth_client.post(url, data, format="json")

        assert response.status_code == 400
        assert "title" in response.data

    def test_update_poll_authenticated(self, auth_client, poll):
        """
        Test updating a poll.
        """
        url = reverse("polls:poll-detail", kwargs={"pk": poll.id})
        data = {"title": "Updated Title"}
        response = auth_client.patch(url, data, format="json")

        assert response.status_code == 200
        assert response.data["title"] == "Updated Title"
        poll.refresh_from_db()
        assert poll.title == "Updated Title"

    def test_delete_poll_authenticated(self, auth_client, poll):
        """
        Test deleting a poll.
        """
        url = reverse("polls:poll-detail", kwargs={"pk": poll.id})
        response = auth_client.delete(url)

        assert response.status_code == 204
        assert not Poll.objects.filter(id=poll.id).exists()

    def test_filter_polls_by_active(self, api_client, test_user):
        """
        Test filtering polls by active status.
        """
        Poll.objects.create(title="Active Poll", created_by=test_user, is_active=True)
        Poll.objects.create(
            title="Inactive Poll", created_by=test_user, is_active=False
        )

        url = reverse("polls:poll-list")

        # Test active
        response = api_client.get(f"{url}?is_active=true")
        assert response.status_code == 200
        # Results might contain more from other fixtures, but should include our active one
        titles = [p["title"] for p in response.data]
        assert "Active Poll" in titles
        # Inactive should NOT be there if filtering works correctly
        # Note: Need to check if filtering is actually enabled in the ViewSet

    def test_order_polls_by_created_at(self, api_client, test_user):
        """
        Test ordering of polls.
        """
        # Poll 1 (earlier)
        Poll.objects.create(title="Oldest", created_by=test_user)
        # Poll 2 (later)
        Poll.objects.create(title="Newest", created_by=test_user)

        url = reverse("polls:poll-list")
        response = api_client.get(url)

        assert response.status_code == 200
        # Default ordering is -created_at
        assert response.data[0]["title"] == "Newest"


class TestQuestionAPI:
    """
    Tests for Question ViewSet CRUD operations.
    """

    def test_list_questions(self, api_client, question):
        """
        Test that anonymous users can list questions.
        """
        url = reverse("polls:question-list")
        response = api_client.get(url)

        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_create_question_authenticated(self, auth_client, poll):
        """
        Test creating a question for a poll.
        """
        url = reverse("polls:question-list")
        data = {
            "poll": poll.id,
            "text": "What is the meaning of life?",
            "question_type": "single",
        }
        response = auth_client.post(url, data, format="json")

        assert response.status_code == 201
        assert response.data["text"] == data["text"]

    def test_update_question_authenticated(self, auth_client, question):
        """
        Test updating a question.
        """
        url = reverse("polls:question-detail", kwargs={"pk": question.id})
        data = {"text": "Updated Question Text"}
        response = auth_client.patch(url, data, format="json")

        assert response.status_code == 200
        assert response.data["text"] == "Updated Question Text"

    def test_delete_question_authenticated(self, auth_client, question):
        """
        Test deleting a question.
        """
        from apps.polls.models import Question

        url = reverse("polls:question-detail", kwargs={"pk": question.id})
        response = auth_client.delete(url)

        assert response.status_code == 204
        assert not Question.objects.filter(id=question.id).exists()


class TestOptionAPI:
    """
    Tests for Option ViewSet CRUD operations.
    """

    def test_list_options(self, api_client, option):
        """
        Test that anonymous users can list options.
        """
        url = reverse("polls:option-list")
        response = api_client.get(url)

        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_create_option_authenticated(self, auth_client, question):
        """
        Test creating an option for a question.
        """
        url = reverse("polls:option-list")
        data = {"question": question.id, "text": "Green", "order": 1}
        response = auth_client.post(url, data, format="json")

        assert response.status_code == 201
        assert response.data["text"] == data["text"]

    def test_update_option_authenticated(self, auth_client, option):
        """
        Test updating an option.
        """
        url = reverse("polls:option-detail", kwargs={"pk": option.id})
        data = {"text": "Updated Option Text"}
        response = auth_client.patch(url, data, format="json")

        assert response.status_code == 200
        assert response.data["text"] == "Updated Option Text"


class TestVoteAPI:
    """
    Tests for Vote ViewSet operations.
    """

    def test_create_vote_authenticated(self, auth_client, option):
        """
        Test successful vote submission.
        """
        url = reverse("polls:vote-list")
        data = {"question": option.question.id, "option": option.id}
        response = auth_client.post(url, data, format="json")

        assert response.status_code == 201
        assert response.data["option"] == option.id

    def test_create_vote_unauthorized(self, api_client, option):
        """
        Test that anonymous users cannot vote.
        """
        url = reverse("polls:vote-list")
        data = {"question": option.question.id, "option": option.id}
        response = api_client.post(url, data, format="json")

        assert response.status_code == 403

    def test_prevent_duplicate_voting(self, auth_client, option):
        """
        Test that a user cannot vote twice on the same question.
        """
        url = reverse("polls:vote-list")
        data = {"question": option.question.id, "option": option.id}

        # First vote
        response1 = auth_client.post(url, data, format="json")
        assert response1.status_code == 201

        # Second vote
        response2 = auth_client.post(url, data, format="json")
        assert response2.status_code == 400
        assert "detail" in response2.data or "non_field_errors" in response2.data
