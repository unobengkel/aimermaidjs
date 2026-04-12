import os
import shutil
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from openai import OpenAI

import database
import rag_handler

app = FastAPI(title="Mermaid AI Editor Backend")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Schemas
class DiagramBase(BaseModel):
    name: str
    mermaid_code: str

class DiagramCreate(DiagramBase):
    pass

class DiagramResponse(DiagramBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    created_at: datetime
    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    api_key: str
    document_ids: Optional[List[int]] = []

# Ensure uploads directory exists
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# --- DIAGRAM ROUTES ---

@app.post("/api/diagrams", response_model=DiagramResponse)
def create_diagram(diagram: DiagramCreate, db: Session = Depends(get_db)):
    db_diagram = database.Diagram(name=diagram.name, mermaid_code=diagram.mermaid_code)
    db.add(db_diagram)
    db.commit()
    db.refresh(db_diagram)
    return db_diagram

@app.get("/api/diagrams", response_model=List[DiagramResponse])
def get_diagrams(db: Session = Depends(get_db)):
    return db.query(database.Diagram).order_by(database.Diagram.created_at.desc()).all()

@app.get("/api/diagrams/{diagram_id}", response_model=DiagramResponse)
def get_diagram(diagram_id: int, db: Session = Depends(get_db)):
    db_diagram = db.query(database.Diagram).filter(database.Diagram.id == diagram_id).first()
    if not db_diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    return db_diagram

@app.put("/api/diagrams/{diagram_id}", response_model=DiagramResponse)
def update_diagram(diagram_id: int, diagram: DiagramCreate, db: Session = Depends(get_db)):
    db_diagram = db.query(database.Diagram).filter(database.Diagram.id == diagram_id).first()
    if not db_diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    db_diagram.name = diagram.name
    db_diagram.mermaid_code = diagram.mermaid_code
    db.commit()
    db.refresh(db_diagram)
    return db_diagram

@app.delete("/api/diagrams/{diagram_id}")
def delete_diagram(diagram_id: int, db: Session = Depends(get_db)):
    db_diagram = db.query(database.Diagram).filter(database.Diagram.id == diagram_id).first()
    if not db_diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    db.delete(db_diagram)
    db.commit()
    return {"message": "Success"}


# --- DOCUMENT (RAG) ROUTES ---

@app.post("/api/documents", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.pdf', '.txt']:
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")
    
    # Save to disk
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Save to SQLite
    db_doc = database.Document(filename=file.filename, file_type=ext)
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # Process and Add to ChromaDB Vector Store
    try:
        rag_handler.process_and_add_document(file_path, db_doc.id)
    except Exception as e:
        # Revert on failure
        db.delete(db_doc)
        db.commit()
        os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

    return db_doc

@app.get("/api/documents", response_model=List[DocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    return db.query(database.Document).order_by(database.Document.created_at.desc()).all()

@app.delete("/api/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    db_doc = db.query(database.Document).filter(database.Document.id == document_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Remove from Chroma DB
    rag_handler.delete_document_vectors(document_id)

    # Remove from Disk
    file_path = os.path.join(UPLOAD_DIR, db_doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Remove from SQLite
    db.delete(db_doc)
    db.commit()
    return {"message": "Success"}


# --- CHAT ROUTE ---

@app.post("/api/chat")
async def chat_with_ai(request: ChatRequest):
    if not request.api_key:
        raise HTTPException(status_code=400, detail="API Key is missing")

    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    # Inject RAG Context if document_ids are provided
    if request.document_ids:
        # We find the latest user query to fetch context
        last_user_query = ""
        for m in reversed(messages):
            if m["role"] == "user":
                last_user_query = m["content"]
                break
        
        if last_user_query:
            context = rag_handler.query_rag_context(last_user_query, request.document_ids)
            if context:
                rag_injection = f"Gunakan konteks dokumen berikut ini untuk membantu menjawab:\n\n---\n{context}\n---\n\n"
                
                # Prepend the context to the last user message
                for m in reversed(messages):
                    if m["role"] == "user":
                        m["content"] = rag_injection + m["content"]
                        break

    # Call DeepSeek API
    try:
        client = OpenAI(api_key=request.api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount Static Files (Frontend UI)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")
