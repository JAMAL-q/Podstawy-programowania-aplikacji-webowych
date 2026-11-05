import { ApiError, createTask, deleteTask, fetchTasks } from "./api.js";
import {
  hideFormError,
  hideListStatus,
  renderTasks,
  showFormError,
  showListError,
  showListLoading,
} from "./ui.js";

const form = document.querySelector("#task-form");
const reloadButton = document.querySelector("#reload-button");
const statusFilter = document.querySelector("#status-filter");
const taskList = document.querySelector("#task-list");
const totalElement = document.querySelector("#total");

function describeError(error) {
  if (error instanceof ApiError) {
    let msg = `Serwer odrzucił żądanie (${error.status}): ${error.message}`;
    // Zadanie 3: Wyświetlanie szczegółowych błędów walidacji pól z problem.errors
    if (error.errors && error.errors.length > 0) {
      const fieldMsgs = error.errors.map(e => `${e.loc.join('.')}: ${e.msg}`).join("; ");
      msg += ` [Błędy pól: ${fieldMsgs}]`;
    }
    return msg;
  }
  return "Brak połączenia z API. Sprawdź, czy serwer działa.";
}

async function loadTasks() {
  showListLoading();
  try {
    const status = statusFilter ? statusFilter.value : "";
    const { items, totalHeader } = await fetchTasks(status);
    renderTasks(items);
    renderTotal(totalHeader);
    hideListStatus();
  } catch (error) {
    showListError(describeError(error));
  }
}

function renderTotal(totalHeader) {
  if (!totalElement) return;
  totalElement.textContent = totalHeader !== null ? totalHeader : "";
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideFormError();

  const formData = new FormData(form);
  const payload = {
    project_id: 1, // Wymagane w nowym kontrakcie API
    title: formData.get("title"),
    priority: formData.get("priority") || "medium",
  };

  try {
    await createTask(payload);
    form.reset();
    await loadTasks();
  } catch (error) {
    showFormError(describeError(error));
  }
});

taskList?.addEventListener("click", async (event) => {
  const target = event.target;
  if (!target.matches(".delete-button")) return;

  const id = target.dataset.id;
  if (!id) return;

  try {
    await deleteTask(id);
    await loadTasks();
  } catch (error) {
    showListError(describeError(error));
  }
});

reloadButton?.addEventListener("click", loadTasks);
statusFilter?.addEventListener("change", loadTasks);

loadTasks();