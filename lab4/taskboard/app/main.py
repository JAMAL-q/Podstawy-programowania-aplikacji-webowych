from itertools import count
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)
from starlette.exceptions import HTTPException as StarletteHTTPException


# 1. Modele błędów dla OpenAPI i Problem Details (Zadanie 5)
class FieldError(BaseModel):
    loc: list[str | int]
    msg: str
    type: str

class Problem(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    errors: list[FieldError] | None = None


# 2. Definicja aplikacji z opisanymi odpowiedziami błędów w OpenAPI (Zadanie 5)
app = FastAPI(
    title="TaskBoard API",
    responses={
        400: {"model": Problem, "description": "Bad Request / Invalid JSON"},
        404: {"model": Problem, "description": "Not Found"},
        409: {"model": Problem, "description": "Conflict"},
        422: {"model": Problem, "description": "Validation Error"},
    },
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)

# 3. Dane w pamięci
PROJECTS: dict[int, dict] = {
    1: {"id": 1, "name": "TaskBoard", "description": "Główny projekt"},
    2: {"id": 2, "name": "Praca dyplomowa", "description": None},
}

USERS: dict[int, dict] = {
    1: {"id": 1, "name": "Jan Kowalski", "email": "jan@example.com"},
    2: {"id": 2, "name": "Anna Nowak", "email": "anna@example.com"},
}

TASKS: dict[int, dict] = {
    1: {
        "id": 1,
        "project_id": 1,
        "title": "Zaprojektować API",
        "status": "done",
        "priority": "high",
        "assignee_id": 1,
    },
    2: {
        "id": 2,
        "project_id": 1,
        "title": "Napisać testy",
        "status": "open",
        "priority": "medium",
        "assignee_id": 2,
    },
}

next_project_id = count(3)
next_task_id = count(3)


# 4. Pomocnicza funkcja generująca odpowiedzi Problem Details (Krok 6)
def problem(
    status: int,
    detail: str,
    errors: list[dict] | None = None,
    headers: dict | None = None,
) -> JSONResponse:
    titles = {
        400: "Bad Request",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Entity",
    }
    content = Problem(
        title=titles.get(status, "Error"),
        status=status,
        detail=detail,
        errors=errors,
    ).model_dump(exclude_none=True)

    return JSONResponse(
        status_code=status,
        content=content,
        media_type="application/problem+json",
        headers=headers,
    )


@app.exception_handler(StarletteHTTPException)
def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return problem(exc.status_code, str(exc.detail), headers=exc.headers)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    if any(error.get("type") == "json_invalid" for error in exc.errors()):
        return problem(400, "Ciało żądania nie jest poprawnym dokumentem JSON")

    formatted_errors = []
    for err in exc.errors():
        formatted_errors.append(
            {
                "loc": list(err["loc"]),
                "msg": err["msg"],
                "type": err["type"],
            }
        )
    return problem(
        422, "Dane wejściowe nie spełniają kontraktu API", formatted_errors
    )


# 5. Typy i Walidacja Pydantic (Krok 3)
def not_blank(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Wartość nie może składać się z samych białych znaków")
    return value


Title = Annotated[
    str, Field(min_length=1, max_length=200), AfterValidator(not_blank)
]
Status = Literal["open", "in_progress", "done"]
Priority = Literal["low", "medium", "high"]


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Title
    description: str | None = None


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Title | None = None
    description: str | None = None

    @field_validator("name")
    @classmethod
    def reject_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Pole nie może mieć wartości null")
        return value


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    task_count: int


class UserOut(BaseModel):
    id: int
    name: str


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: int
    title: Title
    status: Status = "open"
    priority: Priority = "medium"
    assignee_id: int | None = None


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Title | None = None
    status: Status | None = None
    priority: Priority | None = None
    assignee_id: int | None = None

    @field_validator("title", "status", "priority")
    @classmethod
    def reject_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Pole nie może mieć wartości null")
        return value


class TaskOut(BaseModel):
    id: int
    project_id: int
    title: str
    status: Status
    priority: Priority
    assignee_id: int | None = None


# Pomocnicze funkcje biznesowe
def get_task_or_404(task_id: int) -> dict:
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(
            status_code=404, detail=f"Zadanie {task_id} nie istnieje"
        )
    return task


def check_unique_title(
    project_id: int, title: str, ignore_task_id: int | None = None
):
    for t_id, t in TASKS.items():
        if t_id == ignore_task_id:
            continue
        if t["project_id"] == project_id and t["title"] == title:
            raise HTTPException(
                status_code=409,
                detail="Zadanie o takim tytule w tym projekcie już istnieje",
            )


# 6. ENDPOINTY API

# --- UŻYTKOWNICY ---
@app.get("/users", response_model=list[UserOut])
def list_users():
    return list(USERS.values())


@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    user = USERS.get(user_id)
    if not user:
        raise HTTPException(
            status_code=404, detail=f"Użytkownik {user_id} nie istnieje"
        )
    return user


# --- PROJEKTY ---
@app.get("/projects", response_model=list[ProjectOut])
def list_projects():
    res = []
    for p in PROJECTS.values():
        t_count = sum(1 for t in TASKS.values() if t["project_id"] == p["id"])
        res.append({**p, "task_count": t_count})
    return res


@app.post("/projects", status_code=201, response_model=ProjectOut)
def create_project(payload: ProjectCreate, response: Response):
    for p in PROJECTS.values():
        if p["name"] == payload.name:
            raise HTTPException(
                status_code=409, detail="Projekt o takiej nazwie już istnieje"
            )

    p_id = next(next_project_id)
    project = {"id": p_id, **payload.model_dump()}
    PROJECTS[p_id] = project

    response.headers["Location"] = f"/projects/{p_id}"
    return {**project, "task_count": 0}


@app.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: int):
    p = PROJECTS.get(project_id)
    if not p:
        raise HTTPException(
            status_code=404, detail=f"Projekt {project_id} nie istnieje"
        )
    t_count = sum(1 for t in TASKS.values() if t["project_id"] == project_id)
    return {**p, "task_count": t_count}


# Zadanie samodzielne 1: PATCH /projects/{id}
@app.patch("/projects/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, payload: ProjectUpdate):
    p = PROJECTS.get(project_id)
    if not p:
        raise HTTPException(
            status_code=404, detail=f"Projekt {project_id} nie istnieje"
        )

    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes:
        for other_id, other_p in PROJECTS.items():
            if other_id != project_id and other_p["name"] == changes["name"]:
                raise HTTPException(
                    status_code=409,
                    detail="Projekt o takiej nazwie już istnieje",
                )

    p.update(changes)
    t_count = sum(1 for t in TASKS.values() if t["project_id"] == project_id)
    return {**p, "task_count": t_count}


# Zadanie samodzielne 1: DELETE /projects/{id} z 409 jeśli ma zadania
@app.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: int):
    if project_id not in PROJECTS:
        raise HTTPException(
            status_code=404, detail=f"Projekt {project_id} nie istnieje"
        )

    has_tasks = any(t["project_id"] == project_id for t in TASKS.values())
    if has_tasks:
        raise HTTPException(
            status_code=409,
            detail="Nie można usunąć projektu, który posiada zadania",
        )

    del PROJECTS[project_id]
    return Response(status_code=204)


# --- ZADANIA ---
# Zadanie samodzielne 2: dodany filtr ?assignee_id=
@app.get("/tasks")
def list_tasks(
    response: Response,
    status: str | None = None,
    project_id: int | None = None,
    assignee_id: int | None = None,
):
    items = list(TASKS.values())
    if status is not None and status != "":
        items = [t for t in items if t["status"] == status]
    if project_id is not None:
        items = [t for t in items if t["project_id"] == project_id]
    if assignee_id is not None:
        items = [t for t in items if t["assignee_id"] == assignee_id]

    response.headers["X-Total-Count"] = str(len(items))
    return {"items": items, "total": len(items)}


@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int):
    return get_task_or_404(task_id)


@app.post("/tasks", status_code=201, response_model=TaskOut)
def create_task(payload: TaskCreate, response: Response):
    # Krok 3 & Zadanie samodzielne 2: sprawdzanie nieistniejących kluczy obcych -> 422
    if payload.project_id not in PROJECTS:
        raise HTTPException(
            status_code=422, detail=f"Projekt {payload.project_id} nie istnieje"
        )
    if payload.assignee_id is not None and payload.assignee_id not in USERS:
        raise HTTPException(
            status_code=422,
            detail=f"Użytkownik {payload.assignee_id} nie istnieje",
        )

    check_unique_title(payload.project_id, payload.title)

    task_id = next(next_task_id)
    task = {"id": task_id, **payload.model_dump()}
    TASKS[task_id] = task

    response.headers["Location"] = f"/tasks/{task_id}"
    return task


@app.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate):
    task = get_task_or_404(task_id)
    changes = payload.model_dump(exclude_unset=True)

    if (
        "assignee_id" in changes
        and changes["assignee_id"] is not None
        and changes["assignee_id"] not in USERS
    ):
        raise HTTPException(
            status_code=422,
            detail=f"Użytkownik {changes['assignee_id']} nie istnieje",
        )

    if "title" in changes:
        check_unique_title(
            task["project_id"], changes["title"], ignore_task_id=task_id
        )

    task.update(changes)
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    get_task_or_404(task_id)
    del TASKS[task_id]
    return Response(status_code=204)