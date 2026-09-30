"""
main.py — AAA Luxury Perfume Bot
Stack : FastAPI · LangChain (context-stuffing RAG) · Motor (async MongoDB)
Author: Senior Python Backend Developer
"""

import json
import certifi
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import os

import motor.motor_asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from pydantic import BaseModel, Field
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# ─────────────────────────────────────────────────────────────────────────────
# Environment & constants
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

CATALOG_PATH: Path = Path("data/catalog.json")
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL: str = "gemini-3.1-flash-lite"

# ذاكرة تخزين الجلسات (In-memory store for chat history)
store = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# ─────────────────────────────────────────────────────────────────────────────
# Data loading & context formatting
# ─────────────────────────────────────────────────────────────────────────────
def load_catalog() -> dict:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(f"Catalog file not found at: {CATALOG_PATH}")
    with open(CATALOG_PATH, encoding="utf-8") as fh:
        return json.load(fh)

def format_catalog_as_context(catalog: dict) -> str:
    lines: list[str] = []
    lines.append("══════════════════════════════════════")
    lines.append("        كتالوج عطور AAA الفاخرة         ")
    lines.append("══════════════════════════════════════\n")

    for idx, perfume in enumerate(catalog["perfumes"], start=1):
        notes = perfume["notes"]
        lines.append(f"[{idx}] {perfume['name']}")
        lines.append(f"    السعر        : {perfume['price_sar']} ريال سعودي")
        lines.append(f"    رائحة البداية : {' ، '.join(notes['top'])}")
        lines.append(f"    رائحة القلب  : {' ، '.join(notes['heart'])}")
        lines.append(f"    رائحة القاعدة : {' ، '.join(notes['base'])}")
        lines.append(f"    مدة الثبات   : {perfume['longevity']}\n")

    policy = catalog["delivery_policy"]
    lines.append("══════════════════════════════════════")
    lines.append("         سياسة التوصيل                ")
    lines.append("══════════════════════════════════════")
    lines.append(f"  الدولة             : {policy['country']}")
    lines.append(f"  المناطق المخدومة    : {' ، '.join(policy['regions'])}")
    lines.append(
        f"  التوصيل العادي     : {policy['standard_delivery_days']}"
        f" | رسوم: {policy['standard_fee_sar']} ريال"
    )
    lines.append(f"  شحن مجاني من       : {policy['free_shipping_threshold_sar']} ريال فأكثر")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# LangChain RAG pipeline with Memory
# ─────────────────────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """\
أنت "نور"، خبير مبيعات عطور فاخرة في متجر AAA للعطور الفاخرة الخليجية.

قواعد صارمة يجب الالتزام بها دائماً:
١. أجب باللغة العربية الفصحى فقط، بأسلوب راقٍ ولبق يعكس فخامة المتجر.
٢. اعتمد حصراً على المعلومات الواردة في قاعدة بيانات المتجر أدناه.
٣. لا تختلق أسعاراً أو عطوراً أو سياسات توصيل خارج ما هو مذكور.
٤. يمنع منعاً باتاً قول "ليس لدي معلومات" (أو ما يعادلها). بدلاً من ذلك، وجه العميل بأسلوب بيعي ذكي لما هو متاح.
٥. لا تعتذر أبداً.
٦. إذا سُئلت عن العطور الأكثر مبيعاً أو أفضل العطور، رشّح بثقة أغلى ٣ عطور متوفرة في الكتالوج.
٧. لا تذكر أي اسم تقني أو نظام داخلي للعميل.

قواعد إغلاق الصفقات والمبيعات:
- أنت مستشار مبيعات محترف. هدفك هو إقناع العميل بالشراء.
- إذا وافق العميل على الشراء أو اختار عطراً، اطلب منه بدبلوماسية: 1. الاسم الكامل، 2. رقم الهاتف، 3. عنوان التوصيل.
- بمجرد أن يعطيك العميل هذه المعلومات، يجب عليك التوقف عن الرد بالنص العادي، وإرجاع هذا الـ JSON فقط لا غير دون أي زيادات:
{{"order_trigger": true, "customer_name": "الاسم", "phone": "الرقم", "address": "العنوان", "perfume_name": "اسم العطر", "total_price": السعر_بالأرقام}}

══════════════════════════════════════
      قاعدة بيانات المتجر
══════════════════════════════════════
{context}
"""

def build_rag_chain(llm: ChatGoogleGenerativeAI):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"), # هذه هي الذاكرة
            ("human", "{question}"),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    
    # دمج السلسلة مع نظام إدارة الجلسات
    return RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="history",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    client_id: str  
    session_id: str 

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
    print("🚀 Starting AAA Perfume Bot …")
    catalog = load_catalog()
    app.state.catalog_context = format_catalog_as_context(catalog)
    
    llm = ChatGoogleGenerativeAI(
        model=GOOGLE_MODEL,
        temperature=0.3,
        google_api_key=GOOGLE_API_KEY,
    )
    app.state.rag_chain = build_rag_chain(llm)
    
    app.state.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where())
    app.state.db = app.state.mongo_client["perfume_db"]
    print("✅ Server is ready to accept requests.\n")
    yield
    app.state.mongo_client.close()


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI application
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="AAA Luxury Perfume Bot API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", summary="Serve modern HTML SaaS Widget")
async def serve_frontend():
    return FileResponse("static/index.html")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, app_request: Request) -> ChatResponse:
    try:
        reply: str = await app_request.app.state.rag_chain.ainvoke(
            {
                "context": app_request.app.state.catalog_context,
                "question": request.message,
            },
            config={"configurable": {"session_id": request.session_id}} # تمرير الـ Session ID
        )
        return ChatResponse(reply=reply)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"خطأ داخلي: {exc}") from exc

@app.post("/order", response_model=OrderResponse, status_code=201)
async def create_order(order: OrderRequest, app_request: Request) -> OrderResponse:
    try:
        order_doc: dict = {
            **order.model_dump(),
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
        }
        result = await app_request.app.state.db["orders"].insert_one(order_doc)
        return OrderResponse(
            success=True,
            message="تم استلام طلبك بنجاح!",
            order_id=str(result.inserted_id),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"فشل في حفظ الطلب: {exc}") from exc

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
 
 
handler = Mangum(app)