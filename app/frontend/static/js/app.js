/**
 * Care-Tracker - Frontend JavaScript
 * Handles task completion, undo actions, timer logic, and UI interactions.
 *
 * User identity is now managed server-side via JWT cookie.
 * window.CURRENT_USER_NAME and window.CURRENT_USER_ID are set by the
 * base template from the authenticated session.
 */

// Subpath prefix for reverse proxy routing (injected by template, empty string if direct access)
const ROOT = window.ROOT_PATH || '';

// Modal state (for confirmation dialogs)
let pendingAction = null;

// Timer interval handle
let timerInterval = null;

// ============== User Identity (server-provided) ==============

/**
 * Get the current authenticated username.
 * Falls back gracefully if somehow missing (shouldn't happen on protected pages).
 */
function getCurrentUsername() {
    return window.CURRENT_USER_NAME || null;
}

/**
 * Update the user name display in the header.
 * Called on load; the name is rendered server-side so this is just a safety net.
 */
function updateUserDisplay() {
    const name = getCurrentUsername();
    const display = document.getElementById('current-user-name');
    if (display && name) {
        display.textContent = name;
    }
}

/**
 * Ensure a user is authenticated before performing actions.
 * Since pages are now auth-protected, this should always return a name.
 * If it doesn't, something is very wrong and we redirect to login.
 */
function ensureUser() {
    const name = getCurrentUsername();
    if (!name) {
        window.location.href = ROOT + '/login';
        return false;
    }
    return name;
}

// ============== Task Actions ==============

/**
 * Complete a task with confirmation
 * @param {number} careItemId - The care item ID
 * @param {string} taskName - The task name for display
 * @param {number} petId - The pet ID
 */
function completeTask(careItemId, taskName, petId) {
    submitComplete(careItemId, taskName, petId);
}

/**
 * Undo a task with confirmation
 * @param {number} careItemId - The care item ID
 * @param {string} taskName - The task name for display
 */
function undoTask(careItemId, taskName) {
    showModal(
        'Undo Completion?',
        `Are you sure you want to undo "${taskName}"? This will mark it as not complete.`,
        () => submitUndo(careItemId)
    );
}

/**
 * Show the confirmation modal
 */
function showModal(title, message, onConfirm) {
    const modal = document.getElementById('confirm-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalMessage = document.getElementById('modal-message');
    const confirmBtn = document.getElementById('modal-confirm');
    
    modalTitle.textContent = title;
    modalMessage.textContent = message;
    
    pendingAction = onConfirm;
    
    confirmBtn.onclick = () => {
        const action = pendingAction;
        closeModal();
        if (action) {
            action();
        }
    };
    
    modal.style.display = 'flex';
}

/**
 * Close the confirmation modal
 */
function closeModal() {
    const modal = document.getElementById('confirm-modal');
    modal.style.display = 'none';
    pendingAction = null;
}

/**
 * Submit task completion to API
 */
async function submitComplete(careItemId, taskName, petId) {
    const username = ensureUser();
    if (!username) return;

    try {
        const response = await fetch(`${ROOT}/api/tasks/${careItemId}/complete?completed_by=${encodeURIComponent(username)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            await handleTimerPrompts(taskName, petId);
            location.reload();
        } else {
            const error = await response.json();
            alert(`Error: ${error.detail || 'Failed to complete task'}`);
        }
    } catch (err) {
        console.error('Error completing task:', err);
        alert('Network error. Please try again.');
    }
}

/**
 * Handle logic for prompting timers after task completion
 * Centralized timer logic for medication/feeding coordination
 */
async function handleTimerPrompts(taskName, petId) {
    const denaCard = findTaskCard('Denamarin', petId);
    const breakfastCard = findTaskCard('Breakfast', petId);
    const dinnerCard = findTaskCard('Dinner', petId);
    
    const isDenaCompleted = denaCard && denaCard.classList.contains('completed');
    const isBreakfastCompleted = breakfastCard && breakfastCard.classList.contains('completed');
    const isDinnerCompleted = dinnerCard && dinnerCard.classList.contains('completed');
    
    if (taskName === 'Breakfast' || taskName === 'Dinner') {
        if (!isDenaCompleted) {
            const mealName = taskName.toLowerCase();
            if (confirm(`${taskName} done! REMOVE FOOD NOW so she doesn't eat right before her meds. Start 2h timer? (Kitchen LED flashes green when done)`)) {
                await startTimer(petId, 2, 'Empty stomach');
            }
        }
    } 
    else if (taskName === 'Denamarin') {
        const mealsRemaining = !isBreakfastCompleted || !isDinnerCompleted;
        
        if (mealsRemaining) {
            if (confirm('Denamarin given! Start 1h meds absorption timer? (Kitchen LED flashes green when done)')) {
                await startTimer(petId, 1, 'Next meal ready');
            }
        }
    }
}

/**
 * Find a task card in the DOM by task name and pet section
 */
function findTaskCard(taskName, petId) {
    const petSections = document.querySelectorAll('.pet-section');
    for (const section of petSections) {
        const timerContainer = section.querySelector(`[id^="pet-timer-${petId}"]`);
        if (timerContainer) {
            const cards = section.querySelectorAll('.task-card');
            for (const card of cards) {
                const nameElement = card.querySelector('.task-name');
                if (nameElement) {
                    // Clone and strip child elements to get only the direct text content
                    const clone = nameElement.cloneNode(true);
                    while (clone.children.length > 0) {
                        clone.removeChild(clone.children[0]);
                    }
                    const directText = clone.textContent.trim();
                    if (directText === taskName) {
                        return card;
                    }
                }
            }
        }
    }
    return null;
}

/**
 * Submit task undo to API
 */
async function submitUndo(careItemId) {
    const username = ensureUser();
    if (!username) return;

    try {
        const response = await fetch(`${ROOT}/api/tasks/${careItemId}/undo?completed_by=${encodeURIComponent(username)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            location.reload();
        } else {
            const error = await response.json();
            alert(`Error: ${error.detail || 'Failed to undo task'}`);
        }
    } catch (err) {
        console.error('Error undoing task:', err);
        alert('Network error. Please try again.');
    }
}

// ============== Timer Logic ==============

/**
 * Start a timer and persist to backend
 */
async function startTimer(petId, hours, label) {
    try {
        const response = await fetch(`${ROOT}/api/pets/${petId}/timer?hours=${hours}&label=${encodeURIComponent(label)}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            return await response.json();
        } else {
            console.error('Failed to set timer on server');
        }
    } catch (err) {
        console.error('Error setting timer:', err);
    }
}

/**
 * Clear a timer on backend
 */
async function clearTimer(petId) {
    try {
        const response = await fetch(`${ROOT}/api/pets/${petId}/timer`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            const timerEl = document.getElementById(`pet-timer-${petId}`);
            if (timerEl) {
                timerEl.style.display = 'none';
            }
            checkAnyActiveTimers();
        }
    } catch (err) {
        console.error('Error clearing timer:', err);
    }
}

/**
 * Initialize timer display and interval
 */
function initTimerDisplay(petId, label, endTimeStr) {
    const timerEl = document.getElementById(`pet-timer-${petId}`);
    const labelEl = document.getElementById(`timer-label-${petId}`);
    const displayEl = document.getElementById(`timer-display-${petId}`);
    
    if (!timerEl || !labelEl || !displayEl || !endTimeStr) return;
    
    // Safely parse local naive datetime string across all browsers
    let safeTimeStr = endTimeStr;
    if (!/Z|[+-]\d{2}:\d{2}$/.test(endTimeStr)) {
        safeTimeStr = endTimeStr.split('.')[0].replace('T', ' ').replace(/-/g, '/');
    }
    const endTime = new Date(safeTimeStr).getTime();
    
    labelEl.textContent = label;
    timerEl.style.display = 'block';
    timerEl.dataset.endTime = endTime;
    
    updateTimerTick(petId, endTime);
    
    if (!timerInterval) {
        timerInterval = setInterval(tickAllTimers, 1000);
    }
}

function updateTimerTick(petId, endTime) {
    const displayEl = document.getElementById(`timer-display-${petId}`);
    const timerEl = document.getElementById(`pet-timer-${petId}`);
    if (!displayEl || !timerEl) return;
    
    const now = Date.now();
    const remaining = endTime - now;
    
    if (remaining <= 0) {
        displayEl.textContent = "00:00:00 - READY!";
        displayEl.style.color = "var(--success)";
        timerEl.classList.add('timer-ready');
        return;
    }
    
    const h = Math.floor(remaining / 3600000);
    const m = Math.floor((remaining % 3600000) / 60000);
    const s_val = Math.floor((remaining % 60000) / 1000);
    
    displayEl.textContent = `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s_val.toString().padStart(2, '0')}`;
    displayEl.style.color = "";
    timerEl.classList.remove('timer-ready');
}

function tickAllTimers() {
    let hasActive = false;
    
    const timerElements = document.querySelectorAll('.pet-timer');
    timerElements.forEach(el => {
        if (el.style.display !== 'none' && el.dataset.endTime) {
            const petId = el.id.replace('pet-timer-', '');
            updateTimerTick(petId, parseInt(el.dataset.endTime));
            hasActive = true;
        }
    });
    
    if (!hasActive && timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function checkAnyActiveTimers() {
    let hasActive = false;
    const timerElements = document.querySelectorAll('.pet-timer');
    timerElements.forEach(el => {
        if (el.style.display !== 'none') {
            hasActive = true;
        }
    });
    if (!hasActive && timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function checkTimers() {
    if (typeof serverPetTimers !== 'undefined') {
        Object.keys(serverPetTimers).forEach(petId => {
            const timer = serverPetTimers[petId];
            if (timer && timer.endTime) {
                initTimerDisplay(petId, timer.label, timer.endTime);
            }
        });
    }
}

// ============== Modal Close Handlers ==============

document.addEventListener('click', (e) => {
    const confirmModal = document.getElementById('confirm-modal');
    if (e.target === confirmModal) {
        closeModal();
    }
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// ============== Auto-refresh ==============

/**
 * Periodically refresh the dashboard to keep status current,
 * but only if the user isn't currently interacting with a modal.
 */
function setupAutoRefresh() {
    setInterval(() => {
        if (window.location.pathname !== ROOT + '/') return;

        const confirmModal = document.getElementById('confirm-modal');
        const isConfirmModalOpen = confirmModal && confirmModal.style.display === 'flex';

        if (isConfirmModalOpen) {
            console.log('Auto-refresh skipped: Modal is open');
            return;
        }

        console.log('Auto-refreshing dashboard...');
        location.reload();
    }, 60000);
}

// ============== All-Tasks-Done Confetti ==============

/**
 * Check if every Chessie task on the dashboard is completed.
 * Uses sessionStorage keyed to the care day so confetti only fires
 * once per completion cycle (clears if a task is undone).
 */
function checkAllTasksDone() {
    if (window.location.pathname !== ROOT + '/') return;

    const cards = document.querySelectorAll('.task-card');
    if (cards.length === 0) return;

    const allDone = Array.from(cards).every(c => c.classList.contains('completed'));
    const storageKey = 'confetti-shown-' + (typeof careDay !== 'undefined' ? careDay : 'unknown');

    if (allDone) {
        if (!sessionStorage.getItem(storageKey)) {
            sessionStorage.setItem(storageKey, '1');
            if (typeof launchConfetti === 'function') {
                launchConfetti();
            }
        }
    } else {
        // Reset so confetti fires again if user undoes then re-completes all
        sessionStorage.removeItem(storageKey);
    }
}

// ============== Initialization ==============

window.addEventListener('load', () => {
    console.log('Care-Tracker loaded');
    updateUserDisplay();
    checkTimers();
    setupAutoRefresh();
    checkAllTasksDone();
});
