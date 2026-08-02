# agents/rag_qa.py

from dataclasses import dataclass
from typing import List, Dict, Optional
from llm_config import get_llm_response
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

from pydantic import SecretStr

load_dotenv()


# ═══════════════════════════════════════════
# DATA STRUCTURE
# ═══════════════════════════════════════════

@dataclass
class QAResult:
    question: str
    answer: str
    confidence: str         # "high" / "medium" / "low" / "none"
    source_sections: List[str]
    chunks_used: int
    found_in_docs: bool


# ═══════════════════════════════════════════
# RAG Q&A AGENT
# ═══════════════════════════════════════════

class RAGQAAgent:
    """
    Natural language questions → Docs se grounded answers.

    2 modes:
    1. Single question → QAResult
    2. Auto Q&A → Common questions automatically poochho

    Key guarantee: Hallucinate nahi karta.
    Docs mein nahi hai → clearly kehta hai.
    """

    # Common topics ke liye search query enhancements
    # Kyun? User "auth" likhe → search mein "authentication
    # authorization API key token bearer" better results dega
    SEARCH_ENHANCEMENTS = {
        "auth": "authentication authorization API key token bearer header",
        "rate": "rate limit requests per minute hour throttle quota",
        "page": "pagination page cursor offset limit next has_more",
        "error": "error codes status HTTP response 400 401 403 404 429 500",
        "webhook": "webhook callback event notification subscribe",
        "version": "version versioning API version header",
    }

    def __init__(self, rag_pipeline):
        self.rag = rag_pipeline

    # ─────────────────────────────────────
    # MAIN: Single question
    # ─────────────────────────────────────

    def ask(
        self,
        question: str,
        section_hint: Optional[str] = None
    ) -> QAResult:
        """
        section_hint kyun?
        "authentication" → sirf auth section se search karo
        More targeted results milte hain
        """

        # Enhanced search query banao
        search_query = self._enhance_query(question)

        # RAG se chunks lo
        chunks = self.rag.get_relevant_chunks(
            search_query,
            n=5,
            # n=5 kyun? Q&A ke liye zyada context better hai
            # Code agents n=3-4 use karte the
            # section=section_hint
        )

        if not chunks:
            return QAResult(
                question=question,
                answer=(
                    "This information was not found "
                    "in the API documentation provided."
                ),
                confidence="none",
                source_sections=[],
                chunks_used=0,
                found_in_docs=False
            )

        # Context banao — sections clearly label karo
        context_parts = []
        for chunk in chunks:
            labeled = (
                f"[Section: {chunk['section']}]\n"
                f"{chunk['text']}"
            )
            context_parts.append(labeled)

        context = "\n\n---\n\n".join(context_parts)
        # "---" separator kyun?
        # LLM clearly dekhe ki chunks alag hain
        # Context window mein boundaries matter karte hain

        # LLM se answer lo
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an API documentation expert.
Answer questions using ONLY the provided documentation.

Rules:
- Be specific: include exact values, parameter names, URLs
- Use code formatting for technical terms: `param_name`
- If partially documented: share what IS available
- If not in docs at all: say "Not documented in provided docs"
- Never guess or use outside knowledge"""),

            ("human", """
Documentation sections:
{context}

Question: {question}

Answer (based only on documentation above):""")
        ])

        # chain = prompt | self.llm
        # response = chain.invoke({
        #     "context": context,
        #     "question": question
        # })

        # answer = str(response.content)
        # 1. Prompt ko format karo (Functionality intact
        formatted_prompt = prompt.format(context=context, question=question)
            
            # 2. LiteLLM fallback function call (Centralized config)
            # Isse get_llm_response use hoga aur Pylance error chala jayega
        answer_text = get_llm_response(formatted_prompt)
            
            # 3. Purane variable 'answer' mein result daal do
        answer = str(answer_text)
        confidence = self._assess_confidence(answer, chunks)
        sections = list(set(c["section"] for c in chunks))
        # set() → duplicates remove karo
        # list() → set ko list mein convert karo

        return QAResult(
            question=question,
            answer=answer,
            confidence=confidence,
            source_sections=sections,
            chunks_used=len(chunks),
            found_in_docs=(confidence != "none")
        )

    # ─────────────────────────────────────
    # AUTO Q&A: Important questions
    # automatically poochho
    # ─────────────────────────────────────

    def auto_analyze(self, schema) -> Dict[str, QAResult]:
        """
        Har API ke liye 5 important questions
        automatically poochho aur answers store karo.

        Report generator ye use karta hai.
        UI mein "Key Insights" tab mein dikhta hai.
        """

        print("\n💬 Running auto Q&A...")

        # Dict[str, str] — key = topic, value = question
        standard_questions = {
            "authentication": (
                f"How do I authenticate with the {schema.api_name}? "
                f"What headers or parameters are required?"
            ),
            "rate_limits": (
                "What are the rate limits? "
                "How many requests per minute or hour are allowed?"
            ),
            "pagination": (
                "How does pagination work? "
                "What parameters control page size and navigation?"
            ),
            "error_handling": (
                "What error codes can I expect? "
                "How should I handle 429, 401, and 500 errors?"
            ),
            "base_url": (
                "What is the base URL or host for making API requests? "
                "Are there different environments?"
            ),
        }

        results = {}

        for topic, question in standard_questions.items():
            print(f"   {topic}...", end=" ", flush=True)
            result = self.ask(question)
            results[topic] = result

            status = "✅" if result.found_in_docs else "❓"
            print(status)

        return results

    # ─────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────

    def _enhance_query(self, question: str) -> str:
        """
        Simple keyword-based query enhancement.
        User ka question + related terms = better search.
        """
        question_lower = question.lower()

        for keyword, enhancement in self.SEARCH_ENHANCEMENTS.items():
            if keyword in question_lower:
                return f"{question} {enhancement}"
                # Pehla match pe return
                # Multiple enhancements avoid karo — query too long

        return question  # No enhancement needed

    def _assess_confidence(
        self,
        answer: str,
        chunks: list
    ) -> str:
        """
        Answer ki confidence assess karo.

        High: Docs mein clear info mili, specific answer
        Medium: Partial info mili
        Low: Docs se nahi mila, unsure
        None: Explicitly not found
        """
        answer_lower = answer.lower()

        # Explicit "not found" phrases
        not_found_phrases = [
            "not found", "not documented",
            "not specified", "not available",
            "cannot find", "no information",
            "not mentioned", "not provided"
        ]

        if any(phrase in answer_lower for phrase in not_found_phrases):
            return "low"

        # Good answer indicators
        if chunks and len(answer) > 150:
            # Substantial answer + sources = high confidence
            return "high"

        if chunks and len(answer) > 50:
            return "medium"

        return "low"