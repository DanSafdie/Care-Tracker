/**
 * Pet Care Tracker - Frontend JavaScript
 * Handles task completion, undo actions, and UI interactions
 */

// Modal state
let pendingAction = null;

/**
 * Complete a task with confirmation
 * @param {number} careItemId - The care item ID
 * @param {string} taskName - The task name for display
 */
function completeTask(careItemId, taskName) {
    // No confirmation needed for completing - do it directly
    submitComplete(careItemId);
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
 */
async function submitComplete(careItemId) {
    try {
        const response = await fetch(`/api/tasks/${careItemId}/complete`, {
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
            alert(`Error: ${error.detail || 'Failed to complete task'}`);
        }
    } catch (err) {
        console.error('Error completing task:', err);
        alert('Network error. Please try again.');
    }
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

/**
 * Close modal when clicking outside
 */
document.addEventListener('click', (e) => {
    const modal = document.getElementById('confirm-modal');
    if (e.target === modal) {
        closeModal();
    }
});

/**
 * Close modal with Escape key
 */
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// Log page load for debugging
console.log('Pet Care Tracker loaded');
