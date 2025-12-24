/**
 * Care-Tracker - Frontend JavaScript
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
            await handleTimerPrompts(taskName, petId);
            
            // Refresh the page to show updated status
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
 * 
 * @param {string} taskName - The completed task name
 * @param {number} petId - The pet ID
 */
async function handleTimerPrompts(taskName, petId) {
    // Check status of Denamarin and meals
    const denaCard = findTaskCard('Denamarin', petId);
    const breakfastCard = findTaskCard('Breakfast', petId);
    const dinnerCard = findTaskCard('Dinner', petId);
    
    const isDenaCompleted = denaCard && denaCard.classList.contains('completed');
    const isBreakfastCompleted = breakfastCard && breakfastCard.classList.contains('completed');
    const isDinnerCompleted = dinnerCard && dinnerCard.classList.contains('completed');
    
    // === MEAL COMPLETION: Check if we need empty stomach timer for Denamarin ===
    if (taskName === 'Breakfast' || taskName === 'Dinner') {
        // Only prompt if Denamarin hasn't been given yet
        if (!isDenaCompleted) {
            const mealName = taskName.toLowerCase();
            if (confirm(`${taskName} complete! Set a 2-hour timer to know when she has an empty stomach for Denamarin?`)) {
                await startTimer(petId, 2, 'Empty stomach');
            }
        }
    } 
    
    // === DENAMARIN COMPLETION: Check if we need timer for next meal ===
    else if (taskName === 'Denamarin') {
        // Only prompt if there's still a meal to come
        const mealsRemaining = !isBreakfastCompleted || !isDinnerCompleted;
        
        if (mealsRemaining) {
            if (confirm('Denamarin given! Set a 1-hour timer to know when she can have her next meal?')) {
                await startTimer(petId, 1, 'Next meal ready');
            }
        }
        // If both meals are done, no timer needed - she's set for the night!
    }
}

/**
 * Find a task card in the DOM by task name and pet section
 */
function findTaskCard(taskName, petId) {
    // Look for the specific pet section
    const petSections = document.querySelectorAll('.pet-section');
    for (const section of petSections) {
        // Find the pet-timer or pet-header to identify the pet ID
        const timerContainer = section.querySelector(`[id^="pet-timer-${petId}"]`);
        if (timerContainer) {
            const cards = section.querySelectorAll('.task-card');
            for (const card of cards) {
                const nameElement = card.querySelector('.task-name');
                if (nameElement && nameElement.textContent.trim() === taskName) {
                    return card;
                }
            }
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
 * Start a timer and persist to backend
 */
async function startTimer(petId, hours, label) {
    try {
        const response = await fetch(`/api/pets/${petId}/timer?hours=${hours}&label=${encodeURIComponent(label)}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            // The reload in submitComplete will handle showing the timer
            return data;
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
        const response = await fetch(`/api/pets/${petId}/timer`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            const timerEl = document.getElementById(`pet-timer-${petId}`);
            if (timerEl) {
                timerEl.style.display = 'none';
            }
            // Check if any other timers are active to keep interval running or not
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
    
    const endTime = new Date(endTimeStr).getTime();
    
    labelEl.textContent = label;
    timerEl.style.display = 'block';
    
    // Store endTime on the element for easy access during ticks
    timerEl.dataset.endTime = endTime;
    
    updateTimerTick(petId, endTime);
    
    if (!timerInterval) {
        timerInterval = setInterval(tickAllTimers, 1000);
    }
}

/**
 * Update a specific timer's countdown
 */
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
    const s = Math.floor((remaining % 60000) / 10000); // Note: Fix for formatting
    const s_val = Math.floor((remaining % 60000) / 1000);
    
    displayEl.textContent = `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s_val.toString().padStart(2, '0')}`;
    displayEl.style.color = "";
    timerEl.classList.remove('timer-ready');
}

/**
 * Tick loop for all active timers
 */
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

/**
 * Check if any timers are still active
 */
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

/**
 * Initialize timers from server data on page load
 */
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
    console.log('Care-Tracker loaded');
    checkTimers();
});
