# 🌟 Vertebra-Perfume-AI | Luxury Sales Assistant

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb)
![Google Gemini](https://img.shields.io/badge/Gemini_3.1_Flash-8E75B2?style=for-the-badge&logo=google)
![Python](https://img.shields.io/badge/Python_3.9+-3776AB?style=for-the-badge&logo=python)

An intelligent, production-ready AI sales assistant designed specifically for luxury e-commerce. Built for **Vertebra (AI Automation Agency)**, this bot acts as an expert perfume consultant that understands customer preferences in native Arabic, recommends products, and seamlessly extracts order data directly into a MongoDB database.

## 🚀 Key Features

* **Direct Context Architecture:** Bypasses heavy Vector Databases (like Milvus or heavy HuggingFace embeddings) for small-to-medium catalogs. Injects the catalog directly into the LLM context, reducing server RAM usage by 80% and ensuring 100% accurate native Arabic comprehension without embedding translation loss.
* **Strict JSON Data Extraction:** Uses advanced Prompt Engineering to force the LLM to output structured JSON. It safely separates conversational text (sent to the user) from order metadata (name, phone, city, total price) sent to the database.
* **Data Leakage Prevention:** Implements a robust Regex fallback filtering system to ensure raw JSON or code snippets never leak into the client-facing chat UI, even if the LLM hallucinates.
* **Asynchronous Database Operations:** Uses `Motor` for non-blocking MongoDB interactions, ensuring high concurrency and fast response times.
* **Embeddable UI Widget:** Includes a lightweight floating chat widget ready to be integrated into any e-commerce platform (Shopify, WooCommerce, Custom HTML).

## 🧠 Technical Challenges & Solutions

During development, several critical backend architecture challenges were solved:

1. **Free-Tier Server Memory Constraints (OOM Errors):** 
   * *Problem:* Running traditional RAG (Retrieval-Augmented Generation) with local `sentence-transformers` consumed >512MB RAM, crashing lightweight cloud instances.
   * *Solution:* Pivoted to a **Direct Context Injection** model. By feeding the optimized JSON catalog directly into the LLM's system prompt, we eliminated the need for PyTorch/Embeddings entirely, allowing the app to run smoothly on just ~100MB of RAM.
2. **LLM Output Instability & JSON Leaking:**
   * *Problem:* The LLM would occasionally mix natural language with JSON order objects, exposing backend data structures to the end-user.
   * *Solution:* Enforced a `Strict JSON Output` rule with `temperature=0.1`. Added a dual-layer extraction function in Python that parses the JSON safely, and a Regex sanitizer that aggressively scrubs any rogue brackets `{}` or code blocks from the user-facing reply.

## 🛠️ Tech Stack

* **Backend:** FastAPI, Python, Uvicorn
* **AI / LLM:** Google Generative AI (Gemini 3.1 Flash Lite), LangChain Core (Prompts & Parsers)
* **Database:** MongoDB Atlas, Motor (Async IO)
* **Frontend:** HTML5, CSS3, Tailwind (CDN), Vanilla JS (Embeddable Widget)

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the interactive test frontend & widget. |
| `POST` | `/chat` | Receives user messages, processes NLP context, and returns AI replies + Order Triggers. |
| `POST` | `/order` | Securely stores extracted customer order data asynchronously to MongoDB. |

## 💻 Local Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/JawadAbertah/Vertebra-Perfume-AI.git](https://github.com/JawadAbertah/Vertebra-Perfume-AI.git)
   cd Vertebra-Perfume-AI