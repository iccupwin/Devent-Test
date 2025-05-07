// Мини‑хелп для $(selector)
const $ = sel => document.querySelector(sel);

// --- Элементы -------------------------------------------------------------
const modal        = $("#taskModal");
const overlay      = modal.querySelector(".apple-modal__overlay");
const closeBtn     = modal.querySelector(".apple-modal__close");
const titleElement = $("#modalTitle");
const bodyElement  = $("#modalBody");

// --- Открытие -------------------------------------------------------------
function openModal(taskId) {
  // Показ модального окна
  modal.classList.remove("hidden");
  requestAnimationFrame(() => modal.classList.add("visible")); // плавная анимация

  // Шаблон «скелетона» пока грузится контент
  titleElement.textContent = "Загрузка…";
  bodyElement.innerHTML = "<p class='skeleton-line w-80'></p><p class='skeleton-line'></p>";

  fetch(`/api/tasks/${taskId}/`)
    .then(r => {
      if (!r.ok) throw Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then(data => {
      titleElement.textContent = data.name;
      bodyElement.innerHTML = `
        <p class="desc">${data.description || "Без описания"}</p>
        <ul class="task-meta">
          <li><strong>Статус:</strong> ${data.status}</li>
          <li><strong>Проект:</strong> ${data.project}</li>
          <li><strong>Постановщик:</strong> ${data.assigner}</li>
          <li><strong>Срок:</strong> ${data.deadline}</li>
        </ul>`;
    })
    .catch(err => {
      titleElement.textContent = "Ошибка";
      bodyElement.innerHTML = `<p class="error">Не удалось получить данные (${err})</p>`;
    });
}

// --- Закрытие -------------------------------------------------------------
function closeModal() {
  modal.classList.remove("visible");
  modal.addEventListener("transitionend", () => modal.classList.add("hidden"),
                         { once: true });
}

// --- Слушатели ------------------------------------------------------------
document.addEventListener("click", e => {
  const row = e.target.closest(".task-row");
  if (row) {
    openModal(row.dataset.taskId);
  }
});
overlay .addEventListener("click", closeModal);
closeBtn.addEventListener("click", closeModal);
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && modal.classList.contains("visible")) closeModal();
});
