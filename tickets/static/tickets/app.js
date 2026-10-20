"use strict";

const app = document.getElementById("tickets-app");

const categoriesUrl = app.dataset.categoriesUrl;
const ticketsUrl = app.dataset.ticketsUrl;

const form = document.getElementById("ticket-form");
const formHeading = document.getElementById("form-heading");

const titleInput = document.getElementById("title");
const descriptionInput = document.getElementById("description");
const categorySelect = document.getElementById("category");

const saveButton = document.getElementById("save-button");
const cancelButton = document.getElementById("cancel-button");

const message = document.getElementById("message");
const list = document.getElementById("tickets-list");
const loading = document.getElementById("loading");
const statusFilter = document.getElementById("status-filter");

const csrfToken = document.querySelector(
    "[name=csrfmiddlewaretoken]"
).value;

const statusLabels = {
    new: "Новая",
    progress: "В работе",
    done: "Выполнена",
};

const statusClasses = {
    new: "bg-blue-lt",
    progress: "bg-yellow-lt",
    done: "bg-green-lt",
};

const nextStatuses = {
    new: "progress",
    progress: "done",
};

const fieldLabels = {
    title: "Название",
    description: "Описание",
    category: "Категория",
    status: "Статус",
};

let editingId = null;
let categoriesAvailable = false;
let saving = false;
let latestLoad = 0;


function showMessage(text, isError = false) {
    message.textContent = text;

    message.className = isError
        ? "alert alert-danger"
        : "alert alert-success";

    message.hidden = false;
}


function formatApiError(data) {
    if (typeof data === "string") {
        return data;
    }

    if (Array.isArray(data)) {
        return data.map(formatApiError).filter(Boolean).join(" ");
    }

    if (data && typeof data === "object") {
        return Object.entries(data)
            .map(([field, value]) => {
                const text = formatApiError(value);
                const label = fieldLabels[field];

                return label ? `${label}: ${text}` : text;
            })
            .filter(Boolean)
            .join(" ");
    }

    return "";
}


async function apiRequest(url, options = {}) {
    let response;

    try {
        response = await fetch(url, {
            ...options,
            credentials: "same-origin",
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken,
                ...(options.headers || {}),
            },
        });
    } catch {
        throw new Error(
            "Не удалось связаться с сервером. Проверьте подключение."
        );
    }

    let data = null;

    if (response.status !== 204) {
        data = await response.json().catch(() => null);
    }

    if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
            throw new Error(
                "Нет доступа. Проверьте вход в аккаунт и обновите страницу."
            );
        }

        if (response.status === 404) {
            throw new Error(
                "Заявка не найдена или недоступна вашему аккаунту."
            );
        }

        if (response.status >= 500) {
            throw new Error(
                "Ошибка сервера. Попробуйте повторить действие позже."
            );
        }

        throw new Error(
            formatApiError(data) || "Не удалось выполнить запрос."
        );
    }

    if (response.status !== 204 && data === null) {
        throw new Error("Сервер вернул неожиданный ответ.");
    }

    return data;
}


function ticketUrl(id) {
    return `${ticketsUrl}${id}/`;
}


function updateSaveButton() {
    saveButton.disabled = saving || !categoriesAvailable;

    if (saving) {
        saveButton.textContent = "Сохранение...";
    } else {
        saveButton.textContent = editingId === null
            ? "Создать заявку"
            : "Сохранить изменения";
    }
}


function resetForm() {
    editingId = null;
    form.reset();

    formHeading.textContent = "Новая заявка";
    cancelButton.hidden = true;

    updateSaveButton();
}


function startEditing(ticket) {
    editingId = ticket.id;

    titleInput.value = ticket.title;
    descriptionInput.value = ticket.description;
    categorySelect.value = String(ticket.category);

    formHeading.textContent = `Редактирование заявки №${ticket.id}`;
    cancelButton.hidden = false;

    updateSaveButton();

    form.scrollIntoView({
        behavior: "smooth",
        block: "start",
    });

    titleInput.focus();
}


async function loadCategories() {
    const categories = await apiRequest(categoriesUrl);

    categorySelect.replaceChildren();

    for (const category of categories) {
        const option = document.createElement("option");

        option.value = String(category.id);
        option.textContent = category.name;

        categorySelect.append(option);
    }

    categoriesAvailable = categories.length > 0;

    if (!categoriesAvailable) {
        const option = document.createElement("option");

        option.value = "";
        option.textContent = "Сначала добавьте категории в админке";

        categorySelect.append(option);
    }

    updateSaveButton();
}


function createButton(text, className) {
    const button = document.createElement("button");

    button.type = "button";
    button.textContent = text;
    button.className = className;

    return button;
}


async function runRowAction(row, action) {
    const controls = Array.from(
        row.querySelectorAll("button, select")
    );

    const previousStates = controls.map(control => control.disabled);

    controls.forEach(control => {
        control.disabled = true;
    });

    try {
        await action();
    } catch (error) {
        showMessage(error.message, true);
    } finally {
        controls.forEach((control, index) => {
            control.disabled = previousStates[index];
        });
    }
}


async function refreshAfterMutation(successText) {
    try {
        await loadTickets();
        showMessage(successText);
    } catch (error) {
        showMessage(
            `${successText} Но список обновить не удалось: ${error.message}`,
            true
        );
    }
}


function renderTicket(ticket) {
    const row = document.createElement("article");
    row.className = "border rounded p-3 mb-3";

    const header = document.createElement("div");
    header.className = (
        "d-flex justify-content-between align-items-start gap-3 mb-2"
    );

    const title = document.createElement("h3");
    title.className = "h3 mb-0";
    title.textContent = `№${ticket.id}. ${ticket.title}`;

    const badge = document.createElement("span");
    badge.className = `badge ${statusClasses[ticket.status] || ""}`;
    badge.textContent = statusLabels[ticket.status] || ticket.status;

    header.append(title, badge);

    const details = document.createElement("div");
    details.className = "text-secondary mb-2";

    const createdAt = new Date(ticket.created_at).toLocaleString("ru-RU");

    details.textContent = (
        `${ticket.category_name} · Создана: ${createdAt}`
    );

    const description = document.createElement("p");
    description.className = "mb-3";
    description.style.whiteSpace = "pre-wrap";
    description.textContent = ticket.description || "Без описания";

    const actions = document.createElement("div");
    actions.className = "d-flex flex-wrap align-items-center gap-2";

    const editButton = createButton(
        "Редактировать",
        "btn btn-outline-primary btn-sm"
    );

    editButton.addEventListener("click", () => {
        startEditing(ticket);
    });

    actions.append(editButton);

    const nextStatus = nextStatuses[ticket.status];

    if (nextStatus) {
        const select = document.createElement("select");

        select.className = "form-select form-select-sm w-auto";
        select.setAttribute(
            "aria-label",
            `Новый статус заявки №${ticket.id}`
        );

        const option = document.createElement("option");

        option.value = nextStatus;
        option.textContent = statusLabels[nextStatus];

        select.append(option);

        const statusButton = createButton(
            "Изменить статус",
            "btn btn-outline-warning btn-sm"
        );

        statusButton.addEventListener("click", () => {
            runRowAction(row, async () => {
                await apiRequest(ticketUrl(ticket.id), {
                    method: "PATCH",
                    body: JSON.stringify({
                        status: select.value,
                    }),
                });

                await refreshAfterMutation("Статус заявки изменён.");
            });
        });

        actions.append(select, statusButton);
    } else {
        const completed = document.createElement("span");

        completed.className = "text-success small";
        completed.textContent = "Работа завершена";

        actions.append(completed);
    }

    const deleteButton = createButton(
        "Удалить",
        "btn btn-outline-danger btn-sm"
    );

    deleteButton.addEventListener("click", () => {
        const confirmed = window.confirm(
            `Удалить заявку «${ticket.title}»?`
        );

        if (!confirmed) {
            return;
        }

        runRowAction(row, async () => {
            await apiRequest(ticketUrl(ticket.id), {
                method: "DELETE",
            });

            if (editingId === ticket.id) {
                resetForm();
            }

            await refreshAfterMutation("Заявка удалена.");
        });
    });

    actions.append(deleteButton);

    row.append(header, details, description, actions);

    return row;
}


async function loadTickets() {
    const currentLoad = ++latestLoad;

    loading.hidden = false;

    const url = new URL(ticketsUrl, window.location.origin);

    if (statusFilter.value) {
        url.searchParams.set("status", statusFilter.value);
    }

    try {
        const tickets = await apiRequest(url);

        // Более старый ответ не должен перезаписать новый результат.
        if (currentLoad !== latestLoad) {
            return;
        }

        list.replaceChildren();

        if (tickets.length === 0) {
            const empty = document.createElement("p");

            empty.className = "text-secondary mb-0";
            empty.textContent = "Заявки не найдены.";

            list.append(empty);
            return;
        }

        for (const ticket of tickets) {
            list.append(renderTicket(ticket));
        }
    } catch (error) {
        if (currentLoad === latestLoad) {
            throw error;
        }
    } finally {
        if (currentLoad === latestLoad) {
            loading.hidden = true;
        }
    }
}


form.addEventListener("submit", async event => {
    event.preventDefault();

    if (saving || !categoriesAvailable) {
        return;
    }

    const isEditing = editingId !== null;

    const url = isEditing
        ? ticketUrl(editingId)
        : ticketsUrl;

    const payload = {
        title: titleInput.value,
        description: descriptionInput.value,
        category: Number(categorySelect.value),
    };

    saving = true;
    updateSaveButton();

    const controls = Array.from(form.elements);
    const previousStates = controls.map(control => control.disabled);

    controls.forEach(control => {
        control.disabled = true;
    });

    try {
        await apiRequest(url, {
            method: isEditing ? "PATCH" : "POST",
            body: JSON.stringify(payload),
        });

        resetForm();

        // После создания показываем все записи, чтобы новая была видна.
        if (!isEditing) {
            statusFilter.value = "";
        }

        await refreshAfterMutation(
            isEditing
                ? "Изменения сохранены."
                : "Заявка создана."
        );
    } catch (error) {
        showMessage(error.message, true);
    } finally {
        controls.forEach((control, index) => {
            control.disabled = previousStates[index];
        });

        saving = false;
        updateSaveButton();
    }
});


cancelButton.addEventListener("click", resetForm);


statusFilter.addEventListener("change", async () => {
    try {
        await loadTickets();
    } catch (error) {
        showMessage(error.message, true);
    }
});


async function initialize() {
    try {
        await loadCategories();
        await loadTickets();

        if (!categoriesAvailable) {
            showMessage(
                "Добавьте минимум три категории через административную панель.",
                true
            );
        }
    } catch (error) {
        showMessage(error.message, true);
    }
}


initialize();