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

