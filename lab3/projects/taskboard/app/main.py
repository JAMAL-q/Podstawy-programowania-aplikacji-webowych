from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="TaskBoard")

# 1. Konfiguracja CORS i Nagłówków
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["GET", "POST", "DELETE", "PUT"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"], # Wymagane dla licznika pod listą
)

class TaskIn(BaseModel):
    title: str
    priority: str = "medium"

# Baza danych w pamięci (zmienne)
TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Przygotować środowisko", "status": "done", "priority": "high"},
    2: {"id": 2, "title": "Przeczytać RFC 9110", "status": "open", "priority": "medium"},
}
NEXT_ID = 3

@app.get("/")
def root():
    return {"message": "Hello Web"}

@app.get("/health")
def health():
    return {"status": "OK"}

# 2. Pobieranie listy zadań z nagłówkiem X-Total-Count
@app.get("/tasks")
def list_tasks(response: Response, status: str | None = None):
    items = list(TASKS.values())
    if status is not None and status != "":
        items = [t for t in items if t["status"] == status]
    
    # Przekazujemy liczbę zadań w nagłówku X-Total-Count
    response.headers["X-Total-Count"] = str(len(items))
    return {"items": items, "total": len(items)}

# 3. Pobieranie pojedynczego zadania
@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Zadanie nie istnieje")
    return task

# 4. Dodawanie nowego zadania (POST)
@app.post("/tasks", status_code=201)
def create_task(payload: TaskIn, response: Response):
    global NEXT_ID
    
    # Sprawdzamy czy zadanie o takim tytule już istnieje (Dla testu błędu 409)
    for t in TASKS.values():
        if t["title"] == payload.title:
            raise HTTPException(status_code=409, detail="Zadanie o tym tytule już istnieje")

    new_task = {
        "id": NEXT_ID,
        "title": payload.title,
        "status": "open",
        "priority": payload.priority
    }
    TASKS[NEXT_ID] = new_task
    
    response.headers["Location"] = f"/tasks/{NEXT_ID}"
    NEXT_ID += 1
    return new_task

# 5. Usuwanie zadania (DELETE)
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Zadanie nie istnieje")
    del TASKS[task_id]
    return Response(status_code=204)