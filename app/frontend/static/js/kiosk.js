/**
 * Care-Tracker Kiosk Dashboard
 *
 * Single-page JS app for an always-on Fire HD 10 kiosk.
 * Fetches data from the existing Care-Tracker API, renders a dark
 * touch-friendly dashboard, and auto-refreshes every 30 seconds.
 *
 * Relies on JWT cookie auth (set via normal login flow).
 * window.CURRENT_USER_NAME is injected by the Jinja template.
 */

// ============== Constants ==============

const REFRESH_INTERVAL_MS = 30000;
const PILL_POCKET_ITEMS = ['Denamarin', 'Ursodiol'];
const MEAL_ITEMS = ['Breakfast', 'Dinner'];
const DENA_ITEM = 'Denamarin';

// ============== State ==============

let lastData = null;       // Most recent API response
let isOffline = false;
let tickInterval = null;   // 1-second clock + timer tick
let refreshInterval = null;
let modalResolver = null;  // Promise resolve for current modal
let toastTimeout = null;

// ============== Initialization ==============

document.addEventListener('DOMContentLoaded', function () {
    startTick();
    fetchAndRender();
    refreshInterval = setInterval(fetchAndRender, REFRESH_INTERVAL_MS);
});

// ============== Clock & Timer Tick (every second) ==============

function startTick() {
    tick();
    tickInterval = setInterval(tick, 1000);
}

function tick() {
    updateClock();
    updateTimerCountdowns();
}

function updateClock() {
    var now = new Date();
    var clockEl = document.getElementById('kiosk-clock');
    var dateEl = document.getElementById('kiosk-date');
    if (clockEl) {
        clockEl.textContent = now.toLocaleTimeString('en-US', {
            hour: 'numeric', minute: '2-digit', hour12: true
        });
    }
    if (dateEl) {
        dateEl.textContent = now.toLocaleDateString('en-US', {
            weekday: 'short', month: 'short', day: 'numeric'
        });
    }
}

// ============== Data Fetching ==============

function fetchAndRender() {
    fetch('/api/status')
        .then(function (res) {
            if (res.status === 401) {
                window.location.href = '/login';
                return null;
            }
            if (!res.ok) throw new Error('API ' + res.status);
            return res.json();
        })
        .then(function (data) {
            if (!data) return;
            lastData = data;
            setOnline();
            render(data);
        })
        .catch(function () {
            setOffline();
        });
}

// ============== Rendering ==============

function render(data) {
    var pets = data.pets || [];
    var allTasks = [];
    var multiPet = pets.length > 1;

    // Flatten all pets' tasks into a single list for the grid
    pets.forEach(function (petData) {
        var pet = petData.pet;
        var tasks = petData.tasks || [];
        tasks.forEach(function (task) {
            allTasks.push({ task: task, pet: pet, multiPet: multiPet });
        });
    });

    renderHeader(pets);
    renderTimerBanner(pets);
    renderGrid(allTasks);
    renderProgress(allTasks);
}

function renderHeader(pets) {
    var nameEl = document.getElementById('kiosk-pet-name');
    if (!nameEl) return;
    if (pets.length === 0) {
        nameEl.textContent = 'No Pets';
    } else if (pets.length === 1) {
        nameEl.textContent = pets[0].pet.name;
    } else {
        nameEl.textContent = pets.map(function (p) { return p.pet.name; }).join(' & ');
    }
}

function renderTimerBanner(pets) {
    var banner = document.getElementById('kiosk-timer');
    if (!banner) return;

    var timers = [];
    pets.forEach(function (petData) {
        var pet = petData.pet;
        if (pet.timer_end_time) {
            timers.push({
                petId: pet.id,
                petName: pet.name,
                endTime: parseApiTime(pet.timer_end_time),
                label: pet.timer_label || 'Timer'
            });
        }
    });

    if (timers.length === 0) {
        banner.classList.remove('active');
        return;
    }

    banner.classList.add('active');
    banner.innerHTML = timers.map(function (t) {
        var remaining = t.endTime.getTime() - Date.now();
        var isReady = remaining <= 0;
        return '<div class="timer-item' + (isReady ? ' ready' : '') + '" data-end="' + t.endTime.getTime() + '">' +
            '<span class="timer-icon">' + (isReady ? '✅' : '⏱️') + '</span>' +
            '<span class="timer-label">' + escapeHtml(t.label) + '</span>' +
            '<span class="timer-countdown' + (isReady ? ' ready' : '') + '">' + formatCountdown(remaining) + '</span>' +
            '<button class="timer-clear-btn" onclick="event.stopPropagation(); clearKioskTimer(' + t.petId + ')">✕</button>' +
            '</div>';
    }).join('<span style="color:var(--k-border);margin:0 12px">|</span>');
}

function renderGrid(allTasks) {
    var grid = document.getElementById('kiosk-grid');
    if (!grid) return;

    if (allTasks.length === 0) {
        grid.innerHTML = '<div class="kiosk-empty">No care tasks configured</div>';
        return;
    }

    grid.innerHTML = allTasks.map(function (item) {
        return renderCard(item.task, item.pet, item.multiPet);
    }).join('');
}

function renderCard(task, pet, showPetName) {
    var ci = task.care_item;
    var cat = ci.category || 'other';
    var done = task.is_completed;
    var hasPillPocket = PILL_POCKET_ITEMS.indexOf(ci.name) !== -1;

    var footerText = '';
    if (done) {
        var timeStr = formatTime(parseApiTime(task.completed_at));
        var who = task.completed_by || '';
        footerText = timeStr + (who ? ' · ' + escapeHtml(who) : '');
    } else {
        footerText = 'Tap to complete';
    }

    var petLabel = '';
    if (showPetName) {
        petLabel = '<div class="kiosk-card-pet">' + escapeHtml(pet.name) + '</div>';
    }

    return '<div class="kiosk-card' + (done ? ' completed' : '') + '"' +
        ' data-cat="' + cat + '"' +
        ' data-care-id="' + ci.id + '"' +
        ' onclick="onCardTap(' + ci.id + ',\'' + escapeAttr(ci.name) + '\',' + done + ',' + pet.id + ')">' +
        '<div class="kiosk-card-header">' +
            '<span class="kiosk-card-name">' + escapeHtml(ci.name) +
                (hasPillPocket ? '<span class="kiosk-pill-badge">PILL POCKET</span>' : '') +
            '</span>' +
            '<span class="kiosk-cat-badge ' + cat + '">' + cat.toUpperCase() + '</span>' +
        '</div>' +
        petLabel +
        '<div class="kiosk-card-body">' +
            '<div class="kiosk-status-icon ' + (done ? 'done' : 'pending') + '">' +
                (done ? '✓' : '') +
            '</div>' +
        '</div>' +
        '<div class="kiosk-card-footer">' + footerText + '</div>' +
    '</div>';
}

function renderProgress(allTasks) {
    var total = allTasks.length;
    var completed = allTasks.filter(function (t) { return t.task.is_completed; }).length;
    var pct = total > 0 ? (completed / total * 100) : 0;

    var fill = document.getElementById('progress-fill');
    var text = document.getElementById('progress-text');
    var bar = document.querySelector('.kiosk-progress');

    if (fill) fill.style.width = pct + '%';
    if (text) text.textContent = completed + ' of ' + total + ' Complete';
    if (bar) {
        if (completed === total && total > 0) {
            bar.classList.add('all-done');
        } else {
            bar.classList.remove('all-done');
        }
    }
}

// ============== Timer Countdowns (updated every second) ==============

function updateTimerCountdowns() {
    var items = document.querySelectorAll('.timer-item');
    for (var i = 0; i < items.length; i++) {
        var el = items[i];
        var endMs = parseInt(el.getAttribute('data-end'), 10);
        if (!endMs) continue;

        var remaining = endMs - Date.now();
        var isReady = remaining <= 0;

        var cdEl = el.querySelector('.timer-countdown');
        var iconEl = el.querySelector('.timer-icon');
        if (cdEl) {
            cdEl.textContent = formatCountdown(remaining);
            if (isReady) {
                cdEl.classList.add('ready');
                el.classList.add('ready');
            }
        }
        if (iconEl && isReady) {
            iconEl.textContent = '✅';
        }
    }
}

// ============== Card Actions ==============

function onCardTap(careItemId, taskName, isCompleted, petId) {
    if (isCompleted) {
        showModal('Undo?', 'Undo "' + taskName + '"?', 'Undo', 'Cancel', true)
            .then(function (confirmed) {
                if (confirmed) submitUndo(careItemId);
            });
    } else {
        submitComplete(careItemId, taskName, petId);
    }
}

function submitComplete(careItemId, taskName, petId) {
    var username = window.CURRENT_USER_NAME || 'Kiosk';
    var card = document.querySelector('[data-care-id="' + careItemId + '"]');
    if (card) card.classList.add('tapped');

    fetch('/api/tasks/' + careItemId + '/complete?completed_by=' + encodeURIComponent(username), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(function (res) {
        if (!res.ok) throw new Error('API ' + res.status);
        return handleTimerPrompts(taskName, petId);
    })
    .then(function () {
        return fetchAndRender();
    })
    .catch(function () {
        if (card) card.classList.remove('tapped');
        showToast('Failed to complete task', 'error');
    });
}

function submitUndo(careItemId) {
    var username = window.CURRENT_USER_NAME || 'Kiosk';
    fetch('/api/tasks/' + careItemId + '/undo?completed_by=' + encodeURIComponent(username), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(function (res) {
        if (!res.ok) throw new Error('API ' + res.status);
        fetchAndRender();
    })
    .catch(function () {
        showToast('Failed to undo task', 'error');
    });
}

// ============== Timer Prompts (meal/Denamarin coordination) ==============

/**
 * After completing a task, check if a timer prompt is appropriate.
 * Mirrors the logic in app.js but uses custom kiosk modals.
 */
function handleTimerPrompts(taskName, petId) {
    if (!lastData) return Promise.resolve();

    var petData = null;
    for (var i = 0; i < lastData.pets.length; i++) {
        if (lastData.pets[i].pet.id === petId) {
            petData = lastData.pets[i];
            break;
        }
    }
    if (!petData) return Promise.resolve();

    var tasks = petData.tasks;
    var isDenaCompleted = isTaskCompleted(tasks, DENA_ITEM);
    var isBreakfastCompleted = isTaskCompleted(tasks, 'Breakfast');
    var isDinnerCompleted = isTaskCompleted(tasks, 'Dinner');

    // Meal completed but Denamarin hasn't been given yet → empty stomach timer
    if (MEAL_ITEMS.indexOf(taskName) !== -1 && !isDenaCompleted) {
        return showModal(
            'Start Timer?',
            taskName + ' done! REMOVE FOOD so she eats on an empty stomach before meds. Start 2h timer?',
            'Start Timer', 'Skip', false
        ).then(function (confirmed) {
            if (confirmed) return startKioskTimer(petId, 2, 'Empty stomach');
        });
    }

    // Denamarin given and meals remain → absorption timer
    if (taskName === DENA_ITEM && (!isBreakfastCompleted || !isDinnerCompleted)) {
        return showModal(
            'Start Timer?',
            'Denamarin given! Start 1h absorption timer before next meal?',
            'Start Timer', 'Skip', false
        ).then(function (confirmed) {
            if (confirmed) return startKioskTimer(petId, 1, 'Next meal ready');
        });
    }

    return Promise.resolve();
}

function isTaskCompleted(tasks, name) {
    for (var i = 0; i < tasks.length; i++) {
        if (tasks[i].care_item.name === name) return tasks[i].is_completed;
    }
    return false;
}

// ============== Timer API ==============

function startKioskTimer(petId, hours, label) {
    return fetch('/api/pets/' + petId + '/timer?hours=' + hours + '&label=' + encodeURIComponent(label), {
        method: 'POST'
    }).then(function (res) {
        if (!res.ok) showToast('Failed to start timer', 'error');
    }).catch(function () {
        showToast('Network error', 'error');
    });
}

function clearKioskTimer(petId) {
    fetch('/api/pets/' + petId + '/timer', { method: 'DELETE' })
        .then(function (res) {
            if (res.ok) fetchAndRender();
            else showToast('Failed to clear timer', 'error');
        })
        .catch(function () {
            showToast('Network error', 'error');
        });
}

// ============== Modal (Promise-based) ==============

function showModal(title, message, confirmText, cancelText, isDanger) {
    return new Promise(function (resolve) {
        var modal = document.getElementById('kiosk-modal');
        var titleEl = document.getElementById('modal-title');
        var msgEl = document.getElementById('modal-message');
        var confirmBtn = document.getElementById('modal-confirm');
        var cancelBtn = document.getElementById('modal-cancel');

        titleEl.textContent = title;
        msgEl.textContent = message;
        confirmBtn.textContent = confirmText || 'Confirm';
        cancelBtn.textContent = cancelText || 'Cancel';

        confirmBtn.className = 'kiosk-btn ' + (isDanger ? 'kiosk-btn-danger' : 'kiosk-btn-confirm');

        // Clean up any previous resolver
        if (modalResolver) modalResolver(false);
        modalResolver = resolve;

        function onConfirm() {
            cleanup();
            resolve(true);
        }
        function onCancel() {
            cleanup();
            resolve(false);
        }
        function onBackdrop(e) {
            if (e.target === modal) onCancel();
        }
        function cleanup() {
            modal.style.display = 'none';
            confirmBtn.removeEventListener('click', onConfirm);
            cancelBtn.removeEventListener('click', onCancel);
            modal.removeEventListener('click', onBackdrop);
            modalResolver = null;
        }

        confirmBtn.addEventListener('click', onConfirm);
        cancelBtn.addEventListener('click', onCancel);
        modal.addEventListener('click', onBackdrop);
        modal.style.display = 'flex';
    });
}

// ============== Toast ==============

function showToast(message, type, duration) {
    duration = duration || 3000;
    var toast = document.getElementById('kiosk-toast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = 'kiosk-toast visible ' + (type || 'error');
    if (toastTimeout) clearTimeout(toastTimeout);
    toastTimeout = setTimeout(function () {
        toast.classList.remove('visible');
    }, duration);
}

// ============== Online / Offline ==============

function setOnline() {
    if (!isOffline) return;
    isOffline = false;
    var dot = document.getElementById('kiosk-status');
    var banner = document.getElementById('offline-banner');
    if (dot) dot.classList.remove('disconnected');
    if (banner) banner.classList.remove('visible');
}

function setOffline() {
    isOffline = true;
    var dot = document.getElementById('kiosk-status');
    var banner = document.getElementById('offline-banner');
    if (dot) dot.classList.add('disconnected');
    if (banner) banner.classList.add('visible');
}

// ============== Utilities ==============

/** Parse an API datetime string, treating naive datetimes as UTC */
function parseApiTime(isoString) {
    if (!isoString) return null;
    var hasTimezone = /Z|[+-]\d{2}:\d{2}$/.test(isoString);
    if (!hasTimezone) isoString += 'Z';
    return new Date(isoString);
}

function formatTime(dt) {
    if (!dt) return '';
    return dt.toLocaleTimeString('en-US', {
        hour: 'numeric', minute: '2-digit', hour12: true
    });
}

function formatCountdown(ms) {
    if (ms <= 0) return 'READY!';
    var h = Math.floor(ms / 3600000);
    var m = Math.floor((ms % 3600000) / 60000);
    var s = Math.floor((ms % 60000) / 1000);
    return pad2(h) + ':' + pad2(m) + ':' + pad2(s);
}

function pad2(n) {
    return n < 10 ? '0' + n : '' + n;
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function escapeAttr(str) {
    return escapeHtml(str).replace(/'/g, "\\'");
}
