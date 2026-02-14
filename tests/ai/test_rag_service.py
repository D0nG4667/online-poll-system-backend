import json
import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from apps.ai.services import RAGService


# Mock dependencies that are imported inside methods
@pytest.fixture
def mock_poll_model() -> Any:
    with patch("apps.polls.models.Poll") as mock:
        yield mock


class TestRAGService:
    @pytest.fixture
    def rag_service(self) -> Any:
        env_vars = {
            "OPENAI_API_KEY": "test-key",  # pragma: allowlist secret
            "GEMINI_API_KEY": "test-gemini-key",  # pragma: allowlist secret
            "DATABASE_URL": (
                "postgres://user:pass@localhost:5432/db"  # pragma: allowlist secret
            ),
        }
        with patch.dict("os.environ", env_vars):
            with patch(
                "django.conf.settings.OPENAI_API_KEY", "test-key"
            ):  # pragma: allowlist secret
                with patch(
                    "django.conf.settings.GEMINI_API_KEY", "test-gemini-key"
                ):  # pragma: allowlist secret
                    yield RAGService()

    def test_init(self) -> None:
        """Test initialization sets keys correctly."""
        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "env-key",  # pragma: allowlist secret
                "GEMINI_API_KEY": "env-gemini-key",  # pragma: allowlist secret
            },
        ):
            with patch("django.conf.settings.OPENAI_API_KEY", "settings-key"):
                with patch("django.conf.settings.GEMINI_API_KEY", "settings-gemini-key"):
                    service = RAGService()
                    assert service.openai_key == "settings-key"  # pragma: allowlist secret
                    assert service.gemini_key == "settings-gemini-key"  # pragma: allowlist secret
                    assert (
                        os.environ["OPENAI_API_KEY"] == "settings-key"  # pragma: allowlist secret
                    )

    def test_embedding_model_property(self, rag_service: RAGService) -> None:
        """Test embedding model lazy loading."""
        assert rag_service._embedding_model is None
        with patch("apps.ai.services.OpenAIEmbeddings") as mock_embeddings:
            model = rag_service.embedding_model
            mock_embeddings.assert_called_once_with(model="text-embedding-3-small")
            assert model == mock_embeddings.return_value
            # Access again should not re-initialize
            model2 = rag_service.embedding_model
            assert model2 == model
            mock_embeddings.assert_called_once()

    def test_embedding_model_no_key_warning(self) -> None:
        """Test warning when OpenAI key is missing for embeddings."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("django.conf.settings.OPENAI_API_KEY", None):
                with patch("django.conf.settings.GEMINI_API_KEY", None):
                    service = RAGService()
                    with patch("apps.ai.services.logger") as mock_logger:
                        with patch("apps.ai.services.OpenAIEmbeddings"):
                            _ = service.embedding_model
                            mock_logger.warning.assert_called_with(
                                "OPENAI_API_KEY not found. Embeddings may fail."
                            )

    def test_get_llm_primary_success(self, rag_service: RAGService) -> None:
        """Test primary LLM initialization."""
        with patch("apps.ai.services.ChatOpenAI") as mock_chat_openai:
            llm = rag_service.get_llm()
            mock_chat_openai.assert_called_once_with(model="gpt-4o-mini", temperature=0.3)
            assert llm == mock_chat_openai.return_value

    def test_get_llm_primary_fail_fallback_success(self, rag_service: RAGService) -> None:
        """Test fallback to Gemini when OpenAI fails."""
        with (
            patch("apps.ai.services.ChatOpenAI", side_effect=Exception("OpenAI Down")),
            patch("apps.ai.services.ChatGoogleGenerativeAI") as mock_gemini,
        ):
            llm = rag_service.get_llm(fallback_mode=True)
            mock_gemini.assert_called_once_with(
                google_api_key="test-gemini-key",  # pragma: allowlist secret
                model="gemini-pro",
                temperature=0.3,
                convert_system_message_to_human=True,
            )
            assert llm == mock_gemini.return_value

    def test_get_llm_all_fail(self, rag_service: RAGService) -> None:
        """Test error when all LLMs fail."""
        rag_service.openai_key = None  # Disable primary

        with patch(
            "apps.ai.services.ChatGoogleGenerativeAI",
            side_effect=Exception("Gemini Down"),
        ):
            with pytest.raises(ValueError, match="No available LLM providers"):
                rag_service.get_llm(fallback_mode=True)

    def test_get_vector_store_success(self, rag_service: RAGService) -> None:
        """Test vector store creation with correct DB URL replacement."""
        db_url = "postgresql+psycopg://user:pass@localhost:5432/db"  # pragma: allowlist secret
        with patch("apps.ai.services.PGVector") as mock_pgvector:
            with patch("apps.ai.services.OpenAIEmbeddings"):
                _ = rag_service.get_vector_store()
                mock_pgvector.assert_called_once()
                _, kwargs = mock_pgvector.call_args
                # The service might be using a different driver or keeping it as is.
                # If the service replaces postgres:// with postgresql+psycopg://,
                # ensure we match that.
                # Assuming the service does the replacement.
                assert kwargs["connection"] == db_url.replace(
                    "postgres://", "postgresql+psycopg://"
                )

    def test_get_vector_store_no_url(self, rag_service: RAGService) -> None:
        """Test error when DATABASE_URL is missing."""
        # Need to clear environ AND specific fixture patches if they were applied?
        # The fixture applies patches. We can override them.
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="DATABASE_URL not set"):
                rag_service.get_vector_store()

    def test_ingest_poll_data_success(self, rag_service: RAGService) -> None:
        """Test regular ingestion flow."""
        mock_poll = MagicMock()
        mock_poll.title = "Test Poll"
        mock_poll.description = "Test Desc"
        mock_poll.id = 1

        mock_question = MagicMock()
        mock_question.text = "Q1"
        mock_question.question_type = "SINGLE"

        mock_option = MagicMock()
        mock_option.text = "Opt1"
        mock_option.votes.count.return_value = 5

        mock_question.options.all.return_value = [mock_option]
        mock_poll.questions.all.return_value = [mock_question]

        with patch("apps.polls.models.Poll.objects.prefetch_related") as mock_prefetch:
            mock_prefetch.return_value.get.return_value = mock_poll

            with patch("apps.ai.services.RAGService.get_vector_store") as mock_get_store:
                mock_vector_store = MagicMock()
                mock_get_store.return_value = mock_vector_store

                result = rag_service.ingest_poll_data("test-slug")

                mock_vector_store.add_documents.assert_called_once()
                assert "Successfully ingested" in result

    def test_ingest_poll_data_not_found(self, rag_service: RAGService) -> None:
        """Test ingestion with invalid poll slug."""
        # We need to correctly simulate Poll.DoesNotExist from the imported model
        from apps.polls.models import Poll

        with patch("apps.polls.models.Poll.objects.prefetch_related") as mock_prefetch:
            mock_prefetch.return_value.get.side_effect = Poll.DoesNotExist

            with pytest.raises(ValueError, match="Poll with slug invalid-slug not found"):
                rag_service.ingest_poll_data("invalid-slug")

    def test_retrieve_context_success(self, rag_service: RAGService) -> None:
        """Test context retrieval."""
        with patch("apps.ai.services.RAGService.get_vector_store") as mock_get_store:
            mock_store = MagicMock()
            mock_doc = MagicMock()
            mock_doc.page_content = "Context Content"
            mock_store.similarity_search.return_value = [mock_doc]
            mock_get_store.return_value = mock_store

            context = rag_service.retrieve_context("query", 1)
            assert context == "Context Content"
            mock_store.similarity_search.assert_called_with("query", k=4, filter={"poll_id": 1})

    def test_retrieve_context_error(self, rag_service: RAGService) -> None:
        """Test context retrieval error handling."""
        with patch(
            "apps.ai.services.RAGService.get_vector_store",
            side_effect=Exception("DB Error"),
        ):
            context = rag_service.retrieve_context("query", 1)
            assert context == ""

    def test_generate_insight_success(self, rag_service: RAGService) -> None:
        """Test insight generation success path."""
        with patch("apps.polls.models.Poll.objects.values_list") as mock_values:
            mock_values.return_value.get.return_value = 123

            with patch.object(rag_service, "retrieve_context", return_value="Context"):
                with patch.object(rag_service, "get_llm") as mock_get_llm:
                    mock_llm = MagicMock()
                    mock_llm.invoke.return_value.content = "Insight Answer"
                    mock_get_llm.return_value = mock_llm

                    insight = rag_service.generate_insight("poll-slug", "query")
                    assert insight == "Insight Answer"

    def test_generate_insight_poll_not_found(self, rag_service: RAGService) -> None:
        """Test insight generation with missing poll."""
        from apps.polls.models import Poll

        with patch("apps.polls.models.Poll.objects.values_list") as mock_values:
            mock_values.return_value.get.side_effect = Poll.DoesNotExist

            with pytest.raises(ValueError, match="Poll with slug missing-poll not found"):
                rag_service.generate_insight("missing-poll", "query")

    def test_generate_insight_no_context(self, rag_service: RAGService) -> None:
        """Test insight generation when context is empty."""
        with patch("apps.polls.models.Poll.objects.values_list") as mock_values:
            mock_values.return_value.get.return_value = 123

            # Return empty context
            with patch.object(rag_service, "retrieve_context", return_value=""):
                with patch("apps.ai.services.logger") as mock_logger:
                    with patch.object(rag_service, "get_llm") as mock_get_llm:
                        mock_llm = MagicMock()
                        mock_llm.invoke.return_value.content = "Generic Answer"
                        mock_get_llm.return_value = mock_llm

                        _ = rag_service.generate_insight("poll-slug", "query")

                        # Use call_args_list to check matches partially
                        # or simply assert called
                        mock_logger.warning.assert_called()
                        # Verify that one of the calls contained the expected substrings
                        found = any(
                            "No relevant context found" in str(call)
                            for call in mock_logger.warning.call_args_list
                        )
                        assert found

    def test_generate_insight_fallback(self, rag_service: RAGService) -> None:
        """Test insight generation fallback to Gemini."""
        with patch("apps.polls.models.Poll.objects.values_list") as mock_values:
            mock_values.return_value.get.return_value = 123

            with patch.object(rag_service, "retrieve_context", return_value="Context"):
                with patch.object(rag_service, "get_llm") as mock_get_llm:
                    primary_llm = MagicMock()
                    primary_llm.invoke.side_effect = Exception("Primary Fail")

                    fallback_llm = MagicMock()
                    fallback_llm.invoke.return_value.content = "Fallback Answer"

                    def side_effect(fallback_mode: bool = True) -> Any:
                        return fallback_llm if fallback_mode else primary_llm

                    mock_get_llm.side_effect = side_effect

                    insight = rag_service.generate_insight("poll-slug", "query")
                    assert insight == "Fallback Answer"

    def test_generate_insight_all_fail(self, rag_service: RAGService) -> None:
        """Test insight generation when all LLMs fail."""
        with patch("apps.polls.models.Poll.objects.values_list") as mock_values:
            mock_values.return_value.get.return_value = 123

            with patch.object(rag_service, "retrieve_context", return_value="Context"):
                with patch.object(rag_service, "get_llm") as mock_get_llm:
                    mock_get_llm.return_value.invoke.side_effect = Exception("All Fail")

                    insight = rag_service.generate_insight("poll-slug", "query")
                    assert insight == "Service unavailable."

    def test_generate_poll_structure_success(self, rag_service: RAGService) -> None:
        """Test successful structure generation and parsing."""
        json_resp = {"title": "Poll", "description": "Desc", "questions": []}

        with patch.object(rag_service, "get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = json.dumps(json_resp)
            mock_get_llm.return_value = mock_llm

            result = rag_service.generate_poll_structure("prompt")
            assert result["title"] == "Poll"

    def test_generate_poll_structure_markdown_stripping_fallback(
        self, rag_service: RAGService
    ) -> None:
        """Test stripping of markdown code blocks in fallback flow."""
        # Fail primary
        # Fallback returns markdown
        json_resp = {"title": "Fallback Poll", "description": "Desc", "questions": []}
        content = f"```json\n{json.dumps(json_resp)}\n```"

        with patch.object(rag_service, "get_llm") as mock_get_llm:
            primary_llm = MagicMock()
            primary_llm.invoke.side_effect = Exception("Fail")

            fallback_llm = MagicMock()
            fallback_llm.invoke.return_value.content = content

            def side_effect(fallback_mode: bool = False) -> Any:
                return fallback_llm if fallback_mode else primary_llm

            mock_get_llm.side_effect = side_effect

            result = rag_service.generate_poll_structure("prompt")
            assert result["title"] == "Fallback Poll"

    def test_generate_poll_structure_validation_error_and_fail(
        self, rag_service: RAGService
    ) -> None:
        """Test validation missing fields creates ValueError
        and falls back, then all fail."""
        json_resp = {"title": "Incomplete"}  # Missing fields

        with patch.object(rag_service, "get_llm") as mock_get_llm:
            primary_llm = MagicMock()
            primary_llm.invoke.return_value.content = json.dumps(json_resp)

            # Make fallback also fail with parsing error or other
            fallback_llm = MagicMock()
            fallback_llm.invoke.side_effect = Exception("Fallback Fail")

            def side_effect(fallback_mode: bool = False) -> Any:
                return fallback_llm if fallback_mode else primary_llm

            mock_get_llm.side_effect = side_effect

            with pytest.raises(ValueError, match="Failed to generate poll structure"):
                rag_service.generate_poll_structure("prompt")
