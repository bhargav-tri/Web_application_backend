# main.py
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from db import engine, create_db_and_tables
from models import Task, TaskCreate, TaskRead, TaskUpdate

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    create_db_and_tables()
    yield
    # shutdown (optional)
    # e.g., close pools, flush logs, etc.

app = FastAPI(title="Tasks API", lifespan=lifespan)

# CORS: add your frontend origin during local dev & deploy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_session():
    with Session(engine) as session:
        yield session

# @app.on_event("startup")
# def on_startup():
#     create_db_and_tables()

"""Commented due to presence of lifespan handler"""

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tasks", response_model=List[TaskRead])
def list_tasks(session: Session = Depends(get_session)):
    return session.exec(select(Task).order_by(Task.created_at.desc())).all()

@app.post("/tasks", response_model=TaskRead, status_code=201)
def create_task(payload: TaskCreate, session: Session = Depends(get_session)):
    task = Task(**payload.dict())
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, payload: TaskUpdate, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(task, k, v)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()
    return None
