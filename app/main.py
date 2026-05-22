from functools import lru_cache

from fastapi import FastAPI, HTTPException

from app.config import get_settings
from app.erp import load_erp_procurement
from app.llm import LLMService
from app.rag import LocalTfidfVectorStore
from app.reconciliation import reconcile_declaration
from app.schemas import (
    AskRequest,
    AskResponse,
    Citation,
    DeclarationCreate,
    StoredDeclaration,
    SummaryResponse,
)
from app.storage import DeclarationStore


app = FastAPI(
    title="GreenPack EPR Compliance Service",
    description="Submit plastic declarations, reconcile ERP procurement, and ask EPR policy questions.",
    version="1.0.0",
)


@lru_cache
def get_store() -> DeclarationStore:
    return DeclarationStore(get_settings().database_path)


@lru_cache
def get_llm() -> LLMService:
    return LLMService(get_settings())


@lru_cache
def get_vector_store() -> LocalTfidfVectorStore:
    return LocalTfidfVectorStore(get_settings().rag_corpus_path)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/submit", response_model=StoredDeclaration)
def submit_declaration(payload: DeclarationCreate) -> StoredDeclaration:
    return get_store().create(payload)


@app.get("/summary/{producer_id}/{month}", response_model=SummaryResponse)
def summary(producer_id: str, month: str) -> SummaryResponse:
    declaration = get_store().get_latest(producer_id, month)
    if declaration is None:
        raise HTTPException(
            status_code=404,
            detail=f"No declaration found for producer_id={producer_id}, month={month}",
        )

    erp_records = load_erp_procurement(get_settings().erp_feed_path, producer_id, month)
    if not erp_records:
        raise HTTPException(
            status_code=404,
            detail=f"No ERP procurement records found for producer_id={producer_id}, month={month}",
        )

    reconciled = reconcile_declaration(declaration, erp_records)
    llm = get_llm()
    narrative = llm.summarize_reconciliation(producer_id, month, reconciled)
    return SummaryResponse(
        producer_id=producer_id,
        month=month,
        tolerance_percent=5.0,
        reconciliation=reconciled,
        narrative=narrative,
        llm_provider=llm.provider,
    )


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    vector_store = get_vector_store()
    contexts = vector_store.search(request.question)
    llm = get_llm()
    answer = llm.answer_from_context(request.question, contexts)
    citations = [
        Citation(
            document=item["document"],
            section=item["section"],
            score=item["score"],
        )
        for item in contexts
    ]
    if answer == "I do not know based on the provided documents":
        citations = []
    return AskResponse(answer=answer, citations=citations, llm_provider=llm.provider)
