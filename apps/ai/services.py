import json
import logging
import os
from typing import Any, cast

import sentry_sdk
from django.conf import settings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector

logger = logging.getLogger(__name__)


class RAGService:
    """
    Service for Handling RAG operations:
    1. Managing LLM initialization with Fallback.
    2. Generating Embeddings.
    3. Querying the Vector Store (PGVector).
    """

    def __init__(self) -> None:
        self.openai_key = settings.OPENAI_API_KEY
        self.gemini_key = settings.GEMINI_API_KEY
        if self.openai_key:
            os.environ["OPENAI_API_KEY"] = self.openai_key
        self._embedding_model: OpenAIEmbeddings | None = None

    @property
    def embedding_model(self) -> OpenAIEmbeddings:
        """
        Returns the embedding model.
        Using OpenAIEmbeddings for consistency.
        """
        if not self._embedding_model:
            if not self.openai_key:
                logger.warning("OPENAI_API_KEY not found. Embeddings may fail.")
            self._embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
        return self._embedding_model

    def get_llm(self, fallback_mode: bool = True) -> BaseChatModel:
        """
        Returns an LLM instance with fallback strategy.
        Priority:
        1. OpenAI (gpt-4o-mini or gpt-3.5-turbo)
        2. Google Gemini (gemini-pro) if fallback_mode is True and OpenAI fails/missing.
        """
        llm: BaseChatModel | None = None

        # Try primary: OpenAI
        if self.openai_key:
            try:
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.3,
                )
                logger.info("Using Primary LLM: OpenAI gpt-4o-mini")
                return llm
            except Exception as e:
                logger.warning(f"OpenAI LLM init failed: {e}")

        # Fallback: Gemini
        if fallback_mode and self.gemini_key:
            logger.info("Switching to Fallback LLM: Google Gemini")
            try:
                llm = ChatGoogleGenerativeAI(
                    google_api_key=self.gemini_key,
                    model="gemini-pro",
                    temperature=0.3,
                    convert_system_message_to_human=True,
                )
                return llm
            except Exception as e:
                logger.error(f"Failed to initialize Gemini LLM: {e}")

        if not llm:
            raise ValueError(
                "No available LLM providers configured (OpenAI or Gemini)."
            )

        return llm

    def get_vector_store(self) -> PGVector:
        """
        Returns a PGVector store instance.
        """
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL not set in environment.")

        # SQLAlchemy requires postgresql+psycopg:// for psycopg 3
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

        collection_name = "poll_embeddings"

        return PGVector(
            embeddings=self.embedding_model,
            collection_name=collection_name,
            connection=db_url,
            use_jsonb=True,
        )

    def ingest_poll_data(self, poll_slug: str) -> str:
        """
        Ingest poll data into the vector store.
        Converts Poll + Questions + Options into searchable text chunks.
        """
        from apps.polls.models import Poll

        try:
            poll = Poll.objects.prefetch_related("questions__options__votes").get(
                slug=poll_slug
            )
        except Poll.DoesNotExist as e:
            logger.error(f"Poll with slug {poll_slug} not found.")
            raise ValueError(f"Poll with slug {poll_slug} not found.") from e

        # Format data for embedding
        text_chunks = []

        # 1. General Poll Info
        text_chunks.append(
            f"Poll Title: {poll.title}. Description: {poll.description or 'None'}."
        )

        # 2. Questions and Options
        for question in poll.questions.all():
            options_text = ", ".join(
                [
                    f"{opt.text} ({opt.votes.count()} votes)"
                    for opt in question.options.all()
                ]
            )
            q_text = (
                f"Question: {question.text}. Type: {question.question_type}. "
                f"Results: {options_text}."
            )
            text_chunks.append(q_text)

        # Create Documents
        from langchain_core.documents import Document

        docs = [
            Document(
                page_content=chunk,
                metadata={"poll_id": poll.id, "source": "poll_system"},
            )
            for chunk in text_chunks
        ]

        # Store in Vector DB
        vector_store = self.get_vector_store()
        vector_store.add_documents(docs)
        logger.info(
            f"Successfully ingested {len(docs)} documents for Poll {poll.title}."
        )

        return f"Successfully ingested {len(docs)} text chunks for Poll {poll.title}."

    def retrieve_context(self, query: str, poll_id: int) -> str:
        """
        Retrieve relevant context from the vector store.
        Filters by poll_id.
        """
        try:
            vector_store = self.get_vector_store()
            # Search
            results = vector_store.similarity_search(
                query, k=4, filter={"poll_id": poll_id}
            )

            context = "\n".join([doc.page_content for doc in results])
            return context
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return ""

    def generate_insight(self, poll_slug: str, user_query: str) -> str:
        """
        Orchestrates the RAG flow: Retrieve -> Generate.
        """
        # Resolve slug to ID for vector store lookup
        from apps.polls.models import Poll

        try:
            poll_id = Poll.objects.values_list("id", flat=True).get(slug=poll_slug)
        except Poll.DoesNotExist as e:
            raise ValueError(f"Poll with slug {poll_slug} not found.") from e

        sentry_sdk.add_breadcrumb(
            category="ai",
            message=f"Generating insight for poll {poll_slug}",
            level="info",
            data={"query": user_query},
        )
        # 1. Retrieve Context
        context_text = self.retrieve_context(user_query, poll_id)

        if not context_text:
            logger.warning(
                f"No relevant context found for query: '{user_query}' "
                f"on Poll {poll_slug}"
            )
            context_text = "No specific poll data found for this query."

        # 2. Generate Answer
        system_prompt = (
            "You are a helpful data analyst for a polling system. "
            "Use the following context to answer the user's question about the poll. "
            "If the answer is not in the context, state that you don't have that "
            "information. Keep answers concise and data-driven."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Context:\n{context_text}\n\nQuestion: {user_query}"),
        ]

        # 3. Call LLM (with fallback)
        try:
            llm = self.get_llm(fallback_mode=False)
            response = llm.invoke(messages)
            return str(response.content)
        except Exception as e:
            logger.warning(f"Primary LLM failed: {e}. Attempting fallback...")
            if self.gemini_key:
                try:
                    llm_fallback = self.get_llm(fallback_mode=True)
                    response = llm_fallback.invoke(messages)
                    return str(response.content)
                except Exception as fb_err:
                    logger.error(f"Fallback failed: {fb_err}")
                    return "Service unavailable."
            return "Service unavailable."

    def generate_poll_structure(self, user_prompt: str) -> dict[str, Any]:
        """
        Generate a complete poll structure from a natural language description.
        Returns a structured dict with poll title, description, questions, and options.
        """
        sentry_sdk.add_breadcrumb(
            category="ai",
            message="Generating poll structure from prompt",
            level="info",
            data={"prompt_length": len(user_prompt)},
        )
        system_prompt = """
        You are a helpful assistant that generates structured poll data.
        Given a user's description, create a complete poll with:
        - A clear, concise title
        - A brief description
        - 1-5 relevant questions
        - 2-6 options per question

        Return ONLY a valid JSON object with this exact structure:
        {
            "title": "Poll Title",
            "description": "Poll description",
            "questions": [
                {
                    "text": "Question text?",
                    "question_type": "SINGLE_CHOICE or MULTIPLE_CHOICE",
                    "options": [
                        {"text": "Option 1"},
                        {"text": "Option 2"}
                    ]
                }
            ]
        }

        Rules:
        - Keep titles under 200 characters
        - Keep descriptions under 500 characters
        - Use SINGLE_CHOICE for single-answer questions
        - Use MULTIPLE_CHOICE for multiple-answer questions
        - Make options clear and mutually exclusive when possible
        - Return ONLY valid JSON, no markdown or explanations
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Generate a poll structure for: {user_prompt}"),
        ]

        try:
            # Try primary LLM
            llm = self.get_llm(fallback_mode=False)
            response = llm.invoke(messages)
            content = str(response.content).strip()

            # Clean up markdown formatting if present
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()

            # Parse JSON
            poll_structure = json.loads(content)

            # Validate structure
            required_fields = ["title", "description", "questions"]
            if not all(field in poll_structure for field in required_fields):
                raise ValueError("Missing required fields in generated poll")

            logger.info(
                f"Successfully generated poll structure: {poll_structure['title']}"
            )
            return cast(dict[str, Any], poll_structure)

        except Exception as e:
            logger.error(f"Primary LLM failed for poll generation: {e}")
            # Try fallback
            if self.gemini_key:
                try:
                    llm_fallback = self.get_llm(fallback_mode=True)
                    response = llm_fallback.invoke(messages)
                    content = str(response.content).strip()

                    # Clean up markdown
                    if content.startswith("```json"):
                        content = (
                            content.replace("```json", "").replace("```", "").strip()
                        )
                    elif content.startswith("```"):
                        content = content.replace("```", "").strip()

                    poll_structure = json.loads(content)
                    logger.info(
                        "Generated poll structure using fallback LLM: "
                        f"{poll_structure['title']}"
                    )
                    return cast(dict[str, Any], poll_structure)
                except Exception as fb_err:
                    logger.error(f"Fallback LLM also failed: {fb_err}")

            # Return error structure
            raise ValueError(f"Failed to generate poll structure: {str(e)}") from e
