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
const submitButton = document.querySelector("#submit-button");
const reloadButton = document.querySelector("#reload-button");
const statusFilter = document.querySelector("#status-filter");
const taskList = document.querySelector("#task-list");
const totalElement = document.querySelector("#total");

function describeError(error) {
  if (error instanceof ApiError) {
    return `Serwer odrzucił żądanie (${error.status}): ${error.message}`;
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
  if (totalHeader !== null) {
    totalElement.textContent = `Pasujących zadań: ${totalHeader}`;
  } else {
    totalElement.textContent = "";
  }
}

// Obsługa formularza (POST nowatorskie dodawanie)
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideFormError();
  const data = new FormData(form);
  submitButton.disabled = true; // Blokada przycisku podczas wysyłania
  try {
    await createTask({
      title: data.get("title"),
      priority: data.get("priority"),
    });
    form.reset();
    await loadTasks();
  } catch (error) {
    showFormError(describeError(error));
  } finally {
    submitButton.disabled = false; // Odblokowanie zawsze (sukces lub błąd)
  }
});

// Event Delegation do usuwania zadań (Zadanie 1)
taskList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-action='delete']");
  if (button === null) {
    return;
  }
  const taskItem = button.closest(".task");
  const taskId = taskItem.dataset.id;

  button.disabled = true;
  try {
    await deleteTask(taskId);
    await loadTasks();
  } catch (error) {
    showListError(describeError(error));
    button.disabled = false;
  }
});

// Obsługa zmiany filtra statusu (Zadanie 2)
if (statusFilter) {
  statusFilter.addEventListener("change", loadTasks);
}

// Przycisk ręcznego odświeżania
if (reloadButton) {
  reloadButton.addEventListener("click", loadTasks);
}

// Inicjalizacja przy załadowaniu strony
loadTasks();