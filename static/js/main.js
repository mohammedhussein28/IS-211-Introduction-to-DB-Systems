function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

function openEditModal(id, data) {
    const modal = document.getElementById('editModal');
    
    if (!modal) return;
    
    const form = modal.querySelector('form');
    
    if (!form) return;
    
    // Technician page
    if (document.title.includes('Technicians')) {
        form.action = '/technicians/edit/' + id;
    }
    // Power Units page
    else if (document.title.includes('Power Units')) {
        form.action = '/power-units/edit/' + id;
    }
    
    for (let key in data) {
        const input = modal.querySelector(`[name="${key}"]`);
        if (input) {
            input.value = data[key];
        }
    }
    
    modal.classList.add('active');
}

function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this record?');
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
}

// Add delete confirmation to all delete buttons
document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirmDelete()) {
                e.preventDefault();
            }
        });
    });
});