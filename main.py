"""
main.py — AAA Luxury Perfume Bot
Stack : FastAPI · LangChain (context-stuffing RAG) · Motor (async MongoDB)
Author: Senior Python Backend Developer
"""

import json
import os
import certifi
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import motor.motor_asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────────────
# Environment & constants
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

CATALOG_PATH: Path = Path("data/catalog.json")
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL: str = "gemini-3.1-flash-lite"


# ─────────────────────────────────────────────────────────────────────────────
# Data loading & context formatting
# ─────────────────────────────────────────────────────────────────────────────
def load_catalog() -> dict:
    """Load catalog.json and return the parsed dictionary."""
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(f"Catalog file not found at: {CATALOG_PATH}")
    with open(CATALOG_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def format_catalog_as_context(catalog: dict) -> str:
    """
    Flatten the catalog JSON into a clean Arabic text block that will be
    injected into the LLM system prompt as the sole source of truth.
    """
    lines: list[str] = []

    lines.append("══════════════════════════════════════")
    lines.append("       كتالوج عطور AAA الفاخرة        ")
    lines.append("══════════════════════════════════════\n")

    for idx, perfume in enumerate(catalog["perfumes"], start=1):
        notes = perfume["notes"]
        lines.append(f"[{idx}] {perfume['name']}")
        lines.append(f"    السعر       : {perfume['price_sar']} ريال سعودي")
        lines.append(f"    رائحة البداية : {' ، '.join(notes['top'])}")
        lines.append(f"    رائحة القلب  : {' ، '.join(notes['heart'])}")
        lines.append(f"    رائحة القاعدة : {' ، '.join(notes['base'])}")
        lines.append(f"    مدة الثبات   : {perfume['longevity']}\n")

    policy = catalog["delivery_policy"]
    lines.append("══════════════════════════════════════")
    lines.append("          سياسة التوصيل               ")
    lines.append("══════════════════════════════════════")
    lines.append(f"  الدولة              : {policy['country']}")
    lines.append(f"  المناطق المخدومة    : {' ، '.join(policy['regions'])}")
    lines.append(
        f"  التوصيل العادي      : {policy['standard_delivery_days']}"
        f" | رسوم: {policy['standard_fee_sar']} ريال"
    )
    lines.append(
        f"  التوصيل السريع      : {policy['express_delivery_days']}"
        f" | رسوم: {policy['express_fee_sar']} ريال"
    )
    lines.append(
        f"  شحن مجاني من        : {policy['free_shipping_threshold_sar']} ريال فأكثر"
    )
    lines.append(f"  ملاحظات             : {policy['notes']}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# LangChain RAG pipeline
# ─────────────────────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """\
أنت "نور"، مساعد خدمة العملاء في متجر AAA للعطور الفاخرة الخليجية.

قواعد صارمة يجب الالتزام بها دائماً:
١. أجب باللغة العربية الفصحى فقط، بأسلوب راقٍ ولبق يعكس فخامة المتجر.
٢. اعتمد حصراً على المعلومات الواردة في قاعدة بيانات المتجر أدناه.
٣. لا تختلق أسعاراً أو عطوراً أو سياسات توصيل خارج ما هو مذكور.
٤. إذا لم تتوفر المعلومة في قاعدة البيانات، أبلغ العميل بأدب أنك ستحيله
   إلى خدمة العملاء المتخصصة.
٥. لا تذكر أي اسم تقني أو نظام داخلي للعميل.

══════════════════════════════════════
        قاعدة بيانات المتجر
══════════════════════════════════════
{context}
"""


def build_rag_chain(llm: ChatGoogleGenerativeAI):
    """
    Assemble a simple context-stuffing RAG chain:
      Prompt → LLM → StrOutputParser
    The full catalog context is injected on every call via the {context} slot.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_PROMPT),
            ("human", "{question}"),
        ]
    )
    return prompt | llm | StrOutputParser()


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="رسالة العميل")


class ChatResponse(BaseModel):
    reply: str = Field(..., description="رد المساعد الذكي")


class OrderRequest(BaseModel):
    customer_name: str = Field(..., description="اسم العميل الكامل")
    phone_number: str = Field(..., description="رقم الجوال")
    city: str = Field(..., description="المدينة")
    perfume_name: str = Field(..., description="اسم العطر المطلوب")
    total_price: float = Field(..., gt=0, description="السعر الإجمالي بالريال")


class OrderResponse(BaseModel):
    success: bool
    message: str
    order_id: str


# ─────────────────────────────────────────────────────────────────────────────
# Application lifespan (startup / shutdown)
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    print("🚀 Starting AAA Perfume Bot …")

    # 1. Load & format catalog
    catalog = load_catalog()
    app.state.catalog_context = format_catalog_as_context(catalog)
    print("📚 Catalog loaded successfully.")

    # 2. Build LangChain RAG chain
    llm = ChatGoogleGenerativeAI(
        model=GOOGLE_MODEL,
        temperature=0.3,
        google_api_key=GOOGLE_API_KEY,
    )
    app.state.rag_chain = build_rag_chain(llm)
    print(f"🤖 RAG chain ready (model: {GOOGLE_MODEL}).")

    # 3. Connect to MongoDB
    app.state.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where())
    app.state.db = app.state.mongo_client["perfume_db"]
    print(f"🗄️  MongoDB connected → {MONGO_URI}")

    print("✅ Server is ready to accept requests.\n")
    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    app.state.mongo_client.close()
    print("🛑 MongoDB connection closed. Goodbye!")


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI application
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AAA Luxury Perfume Bot API",
    description=(
        "Chatbot & order management API for AAA Gulf Luxury Perfume Store. "
        "Powered by FastAPI · LangChain · MongoDB."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────
@app.post(
    "/chat",
    response_model=ChatResponse,
    summary="Arabic RAG-powered customer service chat",
    tags=["Chat"],
)
async def chat(request: ChatRequest, app_request: Request) -> ChatResponse:
    """
    Receives a customer message and returns an AI-generated reply in Arabic,
    grounded strictly on the catalog loaded at startup.
    """
    try:
        reply: str = await app_request.app.state.rag_chain.ainvoke(
            {
                "context": app_request.app.state.catalog_context,
                "question": request.message,
            }
        )
        return ChatResponse(reply=reply)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"خطأ داخلي أثناء معالجة الطلب: {exc}",
        ) from exc


@app.post(
    "/order",
    response_model=OrderResponse,
    status_code=201,
    summary="Save a customer order to MongoDB",
    tags=["Orders"],
)
async def create_order(order: OrderRequest, app_request: Request) -> OrderResponse:
    """
    Accepts order details and persists them asynchronously to the
    ``perfume_db.orders`` MongoDB collection via the Motor async driver.
    """
    try:
        order_doc: dict = {
            **order.model_dump(),
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
        }
        result = await app_request.app.state.db["orders"].insert_one(order_doc)
        return OrderResponse(
            success=True,
            message="تم استلام طلبك بنجاح! سيتواصل معك فريقنا قريباً. 🌹",
            order_id=str(result.inserted_id),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"فشل في حفظ الطلب: {exc}",
        ) from exc


# ─────────────────────────────────────────────────────────────────────────────
# Dev entry-point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
