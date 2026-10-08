"""
main.py — AAA Luxury Perfume Bot
"""
import re
import json
import certifi
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import os

from pymongo import MongoClient
import motor.motor_asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_core.documents import Document

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL = "gemini-3.1-flash-lite"

store = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

_SYSTEM_PROMPT = """أنت "نور"، خبيرة مبيعات عطور فاخرة في متجر AAA للعطور الخليجية.
مهمتك هي تقديم استشارات عطرية، فهم ذوق العميل، وإتمام عملية البيع.

<STRICT_RULES>
1. تحدثي بالعربية الفصحى فقط، بأسلوب راقٍ ودافئ.
2. لا تتحدثي عن أي موضوع خارج العطور ومتجرنا.
3. اعتمدي حصراً على قاعدة البيانات المرفقة. لا تخترعي أسماء أو أسعار.
4. اطرحي أسئلة لفهم ذوق العميل.
5. إجاباتك يجب أن تكون قصيرة جداً وموجزة.
6. لا تقترحي أكثر من عطر واحد في كل رسالة لتجنب تشتيت انتباه العميل.
</STRICT_RULES>

<THINKING_PROCESS>
قبل الرد على العميل، يجب عليك التفكير في الآتي:
1. نية العميل
2. العطور المناسبة من قاعدة البيانات
3. هل اكتملت بيانات الطلب؟
</THINKING_PROCESS>

اكتبي ردك النهائي الموجه للعميل داخل علامات <response>.
إذا أعطاك العميل بيانات الشراء الكاملة، أضيفي بلوك <order_json> في النهاية لكي يقرأه النظام.

كتالوج العطور:
{context}
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
    app.state.sync_client = MongoClient(MONGO_URI)
    collection = app.state.sync_client["perfume_db"]["perfumes"]
    
    # استخدام FastEmbed الخفيف (بدون PyTorch وبدون API)
    embeddings = FastEmbedEmbeddings()
    
    app.state.vector_store = MongoDBAtlasVectorSearch(
        collection=collection,
        embedding=embeddings,
        index_name="vector_index"
    )
    
    # الدردشة باقية بـ Google حيت خدامة مزيان
    llm = ChatGoogleGenerativeAI(model=GOOGLE_MODEL, temperature=0.3)
    app.state.rag_chain = build_rag_chain(llm)
    
    app.state.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where())
    app.state.db = app.state.mongo_client["perfume_db"]
    yield
    app.state.mongo_client.close()
    app.state.sync_client.close()

app = FastAPI(title="AAA Luxury Perfume Bot API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")

@app.get("/seed")
async def seed_database(request: Request):
    try:
        collection = request.app.state.sync_client["perfume_db"]["perfumes"]
        embeddings = FastEmbedEmbeddings()
        
        with open("catalog.json", "r", encoding="utf-8") as f:
            catalog_data = json.load(f)

        documents = []
        for item in catalog_data:
            text_content = f"اسم العطر: {item['name']}. السعر: {item['price']}. الوصف: {item.get('description', '')}"
            doc = Document(
                page_content=text_content, 
                metadata={"name": item['name'], "price": item['price']}
            )
            documents.append(doc)
        
        collection.delete_many({})
        MongoDBAtlasVectorSearch.from_documents(
            documents=documents,
            embedding=embeddings,
            collection=collection,
            index_name="vector_index"
        )
        return JSONResponse({"status": "success", "message": "تم رفع العطور إلى MongoDB بنجاح!"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, app_request: Request):
    try:
        vector_store = app_request.app.state.vector_store
        search_results = await vector_store.asimilarity_search(request.message, k=2)
        
        dynamic_context = "\n".join([doc.page_content for doc in search_results])
        if not dynamic_context.strip():
            dynamic_context = "لا توجد عطور مطابقة حالياً."

        raw_reply: str = await app_request.app.state.rag_chain.ainvoke(
            {"context": dynamic_context, "question": request.message},
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