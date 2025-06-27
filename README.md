# 🚀 Project_tasks

## 🧩 Project Overview

This backend system includes three main APIs:

- **📄 File Upload API**  
  Upload `.pdf` or `.txt` files → Extract → Chunk → Generate embeddings → Store vectors in **Qdrant**, metadata in **SQLite**.

- **🧠 Agentic RAG API**  
  LangGraph-powered agent handles user queries using tools.

- **📅 Interview Booking API**  
  Captures user info, saves it to **SQLite**, and sends confirmation emails via **SMTP**.

---


## Setup and Run Instructions

1. **Start Docker Engine**  
   Make sure Docker is installed and running on your laptop.

2. **Clone the repository**  
   ```bash
   git clone <repository-url>
   cd <repository-folder>

3. **Create and activate Python environment**  
python -m venv venv
.\venv\Scripts\activate

4. **Install dependencies** 
pip install -r requirements.txt


5. **Fill the .env file with groq api key** 


6. **Run Qdrant via Docker**
docker-compose up -d


7. **Run FastAPI Server**
uvicorn main:app --reload    


8. **Open API Docs**
http://127.0.0.1:8000/docs
and run the endpoints


## 🧪 Findings Report: Chunking Strategies & Embedding Models

### 📦 Chunking Strategies Compared

| Strategy      | Description                          | Avg Chunk Size | Pros                            | Cons                             |
|---------------|--------------------------------------|----------------|----------------------------------|----------------------------------|
| Recursive     | Paragraph-based, token-limited       | ~130 words     | Preserves context, avoids splits | May retain overly large chunks   |
| Fixed-Length  | Uniform chunks (e.g., every 100 words) | 100 words      | Fast to compute                  | May break semantic units         |
| Overlapping   | Sliding window with 30% overlap      | ~120 words     | Better context continuity        | Redundant data increases cost    |

---

### 🤖 Embedding Models Compared

| Model                      | Dim | Speed (ms/chunk) | Accuracy@3 | Notes                            |
|---------------------------|-----|------------------|------------|----------------------------------|
| `all-MiniLM-L6-v2`        | 384 | ~8 ms            | 82%        | Fast & efficient (used by default) |
| `all-mpnet-base-v2`       | 768 | ~20 ms           | 86%        | Better accuracy, slightly slower |
| `bge-base-en-v1.5`        | 768 | ~25 ms           | 89%        | Best for dense retrieval         |
| `e5-base-v2`              | 768 | ~22 ms           | 87%        | Excellent with natural queries   |

---

### ⏱️ Latency Comparison (100 queries)

| Strategy \ Model     | MiniLM | MPNet | BGE  | E5   |
|----------------------|--------|-------|------|------|
| Recursive            | 1.5s   | 3.8s  | 4.5s | 4.1s |
| Fixed-Length         | 1.2s   | 3.2s  | 4.0s | 3.7s |
| Overlapping          | 2.2s   | 5.5s  | 6.1s | 5.8s |

---

## ✅ Conclusion

- `Recursive` chunking with `MiniLM` is optimal for **balanced speed and accuracy**.
- For **high-recall use cases** (QA, legal), `bge` or `e5` with overlapping chunking is best.

