/**
 * Pet Care Tracker - Frontend JavaScript
 * Handles task completion, undo actions, and UI interactions
 */

// Modal state
let pendingAction = null;

// Timer interval
let timerInterval = null;

/**
 * Complete a task with confirmation
 * @param {number} careItemId - The care item ID
 * @param {string} taskName - The task name for display
 * @param {number} petId - The pet ID
 */
function completeTask(careItemId, taskName, petId) {
    // No confirmation needed for completing - do it directly
    submitComplete(careItemId, taskName, petId);
}

/**
 * Undo a task with confirmation
 * @param {number} careItemId - The care item ID
 * @param {string} taskName - The task name for display
 */
function undoTask(careItemId, taskName) {
    // Show confirmation modal for undo actions
    showModal(
        'Undo Completion?',
        `Are you sure you want to undo "${taskName}"? This will mark it as not complete.`,
        () => submitUndo(careItemId)
    );
}

/**
 * Show the confirmation modal
 * @param {string} title - Modal title
 * @param {string} message - Modal message
 * @param {function} onConfirm - Callback for confirm action
 */
function showModal(title, message, onConfirm) {
    const modal = document.getElementById('confirm-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalMessage = document.getElementById('modal-message');
    const confirmBtn = document.getElementById('modal-confirm');
    
    modalTitle.textContent = title;
    modalMessage.textContent = message;
    
    // Store the pending action
    pendingAction = onConfirm;
    
    // Set up confirm button
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
 * @param {number} careItemId - The care item ID
 * @param {string} taskName - The task name
 * @param {number} petId - The pet ID
 */
async function submitComplete(careItemId, taskName, petId) {
    try {
        const response = await fetch(`/api/tasks/${careItemId}/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            // Check if we should prompt for a timer
            handleTimerPrompts(taskName, petId);
            
            // Refresh the page to show updated status
            // Delay slightly if a prompt was shown so it doesn't interrupt
            setTimeout(() => {
                location.reload();
            }, 500);
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
 * @param {string} taskName - The completed task name
 * @param {number} petId - The pet ID
 */
function handleTimerPrompts(taskName, petId) {
    if (taskName === 'Breakfast') {
        // Check if Denamarin is already completed
        const denaCard = findTaskCard('Denamarin', petId);
        const isDenaCompleted = denaCard && denaCard.classList.contains('completed');
        
        if (!isDenaCompleted) {
            if (confirm('Breakfast complete! Set a 2-hour timer to know when she has an empty stomach for Denamarin?')) {
                startTimer(petId, 2, 'Empty stomach for Denamarin');
            }
        }
    } else if (taskName === 'Denamarin') {
        if (confirm('Denamarin given! Set a 1-hour timer to know when she can have her next meal?')) {
            startTimer(petId, 1, 'Ready for next meal');
        }
    }
}

/**
 * Find a task card in the DOM by task name and pet section
 */
function findTaskCard(taskName, petId) {
    const petSection = document.querySelector(`.pet-section`); // Simplified for now, could be more specific
    if (!petSection) return null;
    
    const cards = petSection.querySelectorAll('.task-card');
    for (const card of cards) {
        const nameElement = card.querySelector('.task-name');
        if (nameElement && nameElement.textContent.trim() === taskName) {
            return card;
        }
    }
    return null;
}

/**
 * Submit task undo to API
 * @param {number} careItemId - The care item ID
 */
async function submitUndo(careItemId) {
    try {
        const response = await fetch(`/api/tasks/${careItemId}/undo`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            // Refresh the page to show updated status
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
 * Start a timer and persist to localStorage
 */
function startTimer(petId, hours, label) {
    const durationMs = hours * 60 * 60 * 1000;
    const endTime = Date.now() + durationMs;
    
    const timerData = {
        petId,
        endTime,
        label,
        active: true
    };
    
    localStorage.setItem(`pet_timer_${petId}`, JSON.stringify(timerData));
    initTimerDisplay(petId, timerData);
}

/**
 * Clear a timer
 */
function clearTimer(petId) {
    localStorage.removeItem(`pet_timer_${petId}`);
    const timerEl = document.getElementById(`pet-timer-${petId}`);
    if (timerEl) {
        timerEl.style.display = 'none';
    }
    
    // Check if any other timers are active to keep interval running or not
    checkAnyActiveTimers();
}

/**
 * Initialize timer display and interval
 */
function initTimerDisplay(petId, timerData) {
    const timerEl = document.getElementById(`pet-timer-${petId}`);
    const labelEl = document.getElementById(`timer-label-${petId}`);
    const displayEl = document.getElementById(`timer-display-${petId}`);
    
    if (!timerEl || !labelEl || !displayEl) return;
    
    labelEl.textContent = timerData.label;
    timerEl.style.display = 'block';
    
    updateTimerTick(petId, timerData.endTime);
    
    if (!timerInterval) {
        timerInterval = setInterval(tickAllTimers, 1000);
    }
}

/**
 * Update a specific timer's countdown
 */
function updateTimerTick(petId, endTime) {
    const displayEl = document.getElementById(`timer-display-${petId}`);
    if (!displayEl) return;
    
    const now = Date.now();
    const remaining = endTime - now;
    
    if (remaining <= 0) {
        displayEl.textContent = "00:00:00 - READY!";
        displayEl.style.color = "var(--success)";
        // We keep it visible so user sees it's ready
        return;
    }
    
    const h = Math.floor(remaining / 3600000);
    const m = Math.floor((remaining % 3600000) / 60000);
    const s = Math.floor((remaining % 60000) / 1000);
    
    displayEl.textContent = `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    displayEl.style.color = "";
}

/**
 * Tick loop for all active timers
 */
function tickAllTimers() {
    let hasActive = false;
    
    // Check all possible timers in localStorage
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith('pet_timer_')) {
            const data = JSON.parse(localStorage.getItem(key));
            if (data && data.active) {
                updateTimerTick(data.petId, data.endTime);
                hasActive = true;
            }
        }
    }
    
    if (!hasActive && timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

/**
 * Check if any timers are still active
 */
function checkAnyActiveTimers() {
    let hasActive = false;
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith('pet_timer_')) {
            hasActive = true;
            break;
        }
    }
    if (!hasActive && timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

/**
 * Initialize timers from localStorage on page load
 */
function checkTimers() {
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith('pet_timer_')) {
            try {
                const data = JSON.parse(localStorage.getItem(key));
                if (data && data.active) {
                    initTimerDisplay(data.petId, data);
                }
            } catch (e) {
                console.error("Error parsing timer data", e);
            }
        }
    }
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('confirm-modal');
    if (e.target === modal) {
        closeModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// Initialize on load
window.addEventListener('load', () => {
    console.log('Pet Care Tracker loaded');
    checkTimers();
});
