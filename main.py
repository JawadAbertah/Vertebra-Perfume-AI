"""
main.py — AAA Luxury Perfume Bot (Direct Context Architecture)
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

# الكود الجديد كيقرا الملف بدقة انطلاقاً من المسار الحقيقي ديالو
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

# تحييد المشاكل ديال الأقواس {{ }} مع LangChain
_SYSTEM_PROMPT = """أنت "نور"، خبيرة مبيعات عطور فاخرة في متجر AAA للعطور الخليجية.
مهمتك هي تقديم استشارات عطرية، فهم ذوق العميل، وإتمام عملية البيع.

<STRICT_RULES>
1. تحدثي بالعربية الفصحى فقط، بأسلوب راقٍ ودافئ.
2. لا تتحدثي عن أي موضوع خارج العطور ومتجرنا.
3. اعتمدي حصراً على قاعدة البيانات المرفقة. لا تخترعي أسماء أو أسعار.
4. اطرحي أسئلة لفهم ذوق العميل.
5. إجاباتك يجب أن تكون قصيرة جداً وموجزة (لا تتجاوز 2 إلى 3 أسطر).
6. لا تقترحي أكثر من عطر واحد في كل رسالة لتجنب تشتيت انتباه العميل.
</STRICT_RULES>

<THINKING_PROCESS>
قبل الرد على العميل، يجب عليك التفكير في الآتي:
1. نية العميل
2. العطور المناسبة من قاعدة البيانات
3. هل اكتملت بيانات الطلب؟
</THINKING_PROCESS>

اكتبي ردك النهائي الموجه للعميل داخل علامات <response>.
إذا أعطاك العميل بيانات الشراء الكاملة، أضيفي بلوك <order_json> في النهاية لكي يقرأه النظام بالشكل التالي:
<order_json>
{{"order_trigger": true, "customer_name": "الاسم", "phone": "الرقم", "address": "المدينة", "perfume_name": "اسم العطر", "total_price": السعر}}
</order_json>

كتالوج العطور المتاحة لدينا (اعتمدي عليه حصراً للرد على أسئلة العميل):
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
    llm = ChatGoogleGenerativeAI(model=GOOGLE_MODEL, temperature=0.3, google_api_key=GOOGLE_API_KEY)
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
        # قراءة العطور تتدار مع كل رسالة باش نضمنو بلي البوت عندو الكتالوج كامل
        catalog_text = get_catalog_text()
        
        raw_reply: str = await app_request.app.state.rag_chain.ainvoke(
            {"question": request.message, "catalog": catalog_text},
            config={"configurable": {"session_id": request.session_id}}
        )
        
        response_match = re.search(r'<response>(.*?)</response>', raw_reply, re.DOTALL | re.IGNORECASE)
        clean_text = response_match.group(1).strip() if response_match else raw_reply
        
        order_data = {}
        order_match = re.search(r'<order_json>(.*?)</order_json>', raw_reply, re.DOTALL | re.IGNORECASE)
        if order_match:
            try: order_data = json.loads(order_match.group(1).strip())
            except: pass
                
        final_output = {
            "reply": clean_text,
            "order_trigger": order_data.get("order_trigger", False),
            "customer_name": order_data.get("customer_name", ""),
            "phone": order_data.get("phone", ""),
            "address": order_data.get("address", ""),
            "perfume_name": order_data.get("perfume_name", ""),
            "total_price": order_data.get("total_price", 0)
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