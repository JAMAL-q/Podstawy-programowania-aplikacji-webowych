# TaskBoard API

## Tabela zasobów i punktów końcowych

| Metoda | Ścieżka | Sukces | Błędy | Opis |
|---|---|---|---|---|
| GET, POST | `/projects` | 200, 201 | 409, 422 | Pobieranie listy i tworzenie projektów |
| GET, PATCH, DELETE | `/projects/{id}` | 200, 204 | 404, 409, 422 | Szczegóły, edycja i usuwanie projektu |
| GET | `/users`, `/users/{id}` | 200 | 404 | Lista i szczegóły użytkowników |
| GET, POST | `/tasks` | 200, 201 | 400, 409, 422 | Pobieranie i dodawanie zadań |
| GET, PATCH, DELETE | `/tasks/{id}` | 200, 204 | 400, 404, 409, 422 | Szczegóły, zmiana i usuwanie zadania |
