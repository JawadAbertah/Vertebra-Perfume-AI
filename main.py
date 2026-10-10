"""
main.py — AAA Luxury Perfume Bot (Strict JSON Architecture)
"""
import re
import json
import certifi
from contextlib import asynccontextmanager
from datetime import datetime, timezone
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
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL = "gemini-3.1-flash-lite"

store = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def get_catalog_text():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        catalog_path = os.path.join(base_dir, "catalog.json")
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog_items = json.load(f)
        if not catalog_items:
            return "الكتالوج فارغ."
        return "\n".join([f"- اسم العطر: {item.get('name', 'غير معروف')}, السعر: {item.get('price', 0)} ريال. الوصف: {item.get('description', '')}" for item in catalog_items])
    except Exception as e:
        return f"حدث خطأ أثناء قراءة الكتالوج: {str(e)}"

# Prompt صارم جداً يفرض إخراج JSON فقط بدون أي نص إضافي
_SYSTEM_PROMPT = """أنت "نور"، خبيرة مبيعات عطور فاخرة في متجر AAA للعطور الخليجية.
مهمتك هي تقديم استشارات عطرية، فهم ذوق العميل، وإتمام عملية البيع.

<CRITICAL_RULE>
يجب أن يكون ردك دائماً وأبداً بصيغة JSON فقط. ممنوع كتابة أي نص خارج الـ JSON.
يجب أن تستخدمي هذا الهيكل بالضبط (يجب أن يكون JSON صحيحاً):
{{
  "reply": "هنا تكتبين ردك النصي للعميل بالعربية الفصحى وبشكل موجز جداً ودافئ.",
  "order_data": {{
    "order_trigger": true_or_false,
    "customer_name": "اسم العميل إن وجد",
    "phone": "رقم الهاتف إن وجد",
    "address": "المدينة إن وجدت",
    "perfume_name": "اسم العطر إن وجد",
    "total_price": السعر_كرقم
  }}
}}
- إذا لم يكتمل الطلب (العميل يسأل فقط)، اجعلي order_trigger بقيمة false واتركي باقي الحقول فارغة.
- إذا أعطاك العميل معلومات الشراء (الاسم، الهاتف، المدينة، العطر)، اجعلي order_trigger بقيمة true واملئي البيانات.
</CRITICAL_RULE>

كتالوج العطور المتاحة لدينا (اعتمدي عليه حصراً):
{catalog}
"""

def build_rag_chain(llm):
    prompt = ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ])
    chain = prompt | llm | StrOutputParser()
    return RunnableWithMessageHistory(
        chain, get_session_history,
        input_messages_key="question", history_messages_key="history",
    )

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=300)
    client_id: str
    session_id: str

class ChatResponse(BaseModel):
    reply: str

class OrderRequest(BaseModel):
    customer_name: str
    phone_number: str
    city: str
    perfume_name: str
    total_price: float

class OrderResponse(BaseModel):
    success: bool
    message: str
    order_id: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # خفضنا الـ temperature لـ 0.1 لضمان التزام الذكاء الاصطناعي بالأوامر وتفادي الهلوسة
    llm = ChatGoogleGenerativeAI(model=GOOGLE_MODEL, temperature=0.1, google_api_key=GOOGLE_API_KEY)
    app.state.rag_chain = build_rag_chain(llm)
    app.state.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where())
    app.state.db = app.state.mongo_client["perfume_db"]
    yield
    app.state.mongo_client.close()

app = FastAPI(title="AAA Luxury Perfume Bot API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, app_request: Request):
    try:
        catalog_text = get_catalog_text()
        raw_reply: str = await app_request.app.state.rag_chain.ainvoke(
            {"question": request.message, "catalog": catalog_text},
            config={"configurable": {"session_id": request.session_id}}
        )
        
        # 1. تنظيف الرد من علامات Markdown لي كيزيدها Gemini
        json_str = raw_reply.replace("```json", "").replace("```", "").strip()
        
        # 2. استخراج كود الـ JSON فقط في حالة البوت زاد شي نص بالخطأ
        match = re.search(r'(\{.*\})', json_str, re.DOTALL)
        if match:
            json_str = match.group(1)
            
        # 3. فصل النص عن البيانات بأمان تام
        try:
            bot_data = json.loads(json_str)
            clean_text = bot_data.get("reply", "تم استلام طلبك شكراً لك.")
            order_info = bot_data.get("order_data", {})
            if not isinstance(order_info, dict):
                order_info = {}
        except Exception as parse_error:
            # Fallback قوي: في حالة فشل التحليل، نمسح أي كود برمجي ونعرض النص فقط
            print("JSON Parsing Error:", parse_error)
            clean_text = raw_reply
            clean_text = re.sub(r'\{.*?\}', '', clean_text, flags=re.DOTALL)
            clean_text = clean_text.replace('"', '').replace('```', '').strip()
            if not clean_text:
                clean_text = "تم الاستلام بنجاح، فريقنا سيتواصل معك قريباً."
            order_info = {}
                
        final_output = {
            "reply": clean_text,
            "order_trigger": order_info.get("order_trigger", False),
            "customer_name": order_info.get("customer_name", ""),
            "phone": order_info.get("phone", ""),
            "address": order_info.get("address", ""),
            "perfume_name": order_info.get("perfume_name", ""),
            "total_price": order_info.get("total_price", 0)
        }
        return ChatResponse(reply=json.dumps(final_output))
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/order", response_model=OrderResponse, status_code=201)
async def create_order(order: OrderRequest, app_request: Request):
    try:
        order_doc = {**order.model_dump(), "status": "pending", "created_at": datetime.now(timezone.utc)}
        result = await app_request.app.state.db["orders"].insert_one(order_doc)
        return OrderResponse(success=True, message="تم الاستلام", order_id=str(result.inserted_id))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))