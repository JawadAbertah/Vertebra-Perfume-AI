import os
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_core.documents import Document
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

client = MongoClient(os.environ["MONGO_URI"])
collection = client["perfume_db"]["perfumes"]

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

print("جاري قراءة الكتالوج...")
with open("catalog.json", "r", encoding="utf-8") as f:
    catalog_data = json.load(f)

documents = []
for item in catalog_data:
    # دمج المعلومات باش الذكاء الاصطناعي يفهمها
    text_content = f"اسم العطر: {item['name']}. السعر: {item['price']}. الوصف: {item.get('description', '')}"
    doc = Document(
        page_content=text_content, 
        metadata={"name": item['name'], "price": item['price']}
    )
    documents.append(doc)

print("جاري تحويل البيانات إلى Vectors ورفعها إلى MongoDB...")
# مسح البيانات القديمة باش ما يتعاودوش
collection.delete_many({})

# رفع البيانات
MongoDBAtlasVectorSearch.from_documents(
    documents=documents,
    embedding=embeddings,
    collection=collection,
    index_name="vector_index"
)

print("🎉 تم بناء قاعدة البيانات الذكية بنجاح!")