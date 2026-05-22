from typing import Any

from app.config import Settings
from app.schemas import CategoryReconciliation


UNKNOWN_ANSWER = "I do not know based on the provided documents"


class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = "offline_fallback"
        self._client = None
        if settings.groq_api_key:
            try:
                from groq import Groq

                self._client = Groq(api_key=settings.groq_api_key)
                self.provider = f"groq:{settings.groq_model}"
            except Exception:
                self._client = None

    def summarize_reconciliation(
        self,
        producer_id: str,
        month: str,
        reconciliation: list[CategoryReconciliation],
    ) -> str:
        payload = [item.model_dump() for item in reconciliation]
        if self._client is None:
            return self._offline_summary(producer_id, month, payload)

        prompt = (
            "You write concise compliance summaries for an Indian plastic packaging "
            "producer. The deterministic reconciliation is already complete; do not "
            "recalculate or invent numbers. In 3-5 sentences, explain any categories "
            "outside the 5% tolerance and recommend a practical next action. "
            f"Producer: {producer_id}. Month: {month}. Reconciliation JSON: {payload}"
        )
        return self._chat(prompt)

    def answer_from_context(
        self,
        question: str,
        contexts: list[dict[str, Any]],
    ) -> str:
        if not contexts:
            return UNKNOWN_ANSWER
        if self._client is None:
            return self._offline_context_answer(question, contexts)

        context_text = "\n\n".join(
            f"Document: {item['document']}\nSection: {item['section']}\n"
            f"Text: {item['text']}"
            for item in contexts
        )
        prompt = (
            "Answer the compliance officer's question using only the provided source "
            "sections. If the answer is not directly supported by those sections, "
            f"return exactly: {UNKNOWN_ANSWER}\n\n"
            f"Question: {question}\n\nSources:\n{context_text}"
        )
        return self._chat(prompt)

    def _chat(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self.settings.groq_model,
            messages=[
                {
                    "role": "system",
                    "content": "Be accurate, concise, and grounded in the supplied data.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=350,
        )
        return response.choices[0].message.content.strip()

    @staticmethod
    def _offline_summary(
        producer_id: str, month: str, reconciliation: list[dict[str, Any]]
    ) -> str:
        flagged = [item for item in reconciliation if item["flagged"]]
        if not flagged:
            return (
                f"For {producer_id} in {month}, all declared plastic quantities are "
                "within the 5% tolerance against ERP procurement records. The "
                "compliance team should retain the declaration and ERP extract as "
                "supporting evidence for the monthly EPR file."
            )
        gap_text = "; ".join(
            f"{item['category']} is {abs(item['difference_percent'] or 0):.2f}% "
            f"{'above' if item['difference_kg'] > 0 else 'below'} procurement"
            for item in flagged
        )
        return (
            f"For {producer_id} in {month}, the reconciliation found material gaps: "
            f"{gap_text}. These categories exceed the 5% tolerance and should be "
            "reviewed against purchase invoices, production issues, and stock movement "
            "records before final EPR filing."
        )

    @staticmethod
    def _offline_context_answer(question: str, contexts: list[dict[str, Any]]) -> str:
        terms = {term.lower() for term in question.split() if len(term) > 3}
        sentences: list[str] = []
        for item in contexts:
            for sentence in item["text"].split("."):
                cleaned = sentence.strip()
                if cleaned and any(term in cleaned.lower() for term in terms):
                    sentences.append(cleaned + ".")
        if not sentences:
            return UNKNOWN_ANSWER
        return " ".join(sentences[:3])
