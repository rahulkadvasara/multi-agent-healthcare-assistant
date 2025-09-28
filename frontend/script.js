// Healthcare Dashboard JavaScript
const API_BASE = 'http://localhost:8000';
let currentUser = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    const userData = localStorage.getItem('user');
    if (!userData) {
        window.location.href = 'login.html';
        return;
    }
    
    currentUser = JSON.parse(userData);
    document.getElementById('username').textContent = currentUser.username;
    
    // Initialize event listeners
    initializeEventListeners();
    
    // Load reminders
    loadReminders();
});

function initializeEventListeners() {
    // Chat input handling
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    sendBtn.addEventListener('click', sendMessage);
    
    // File upload handling
    const fileUploadArea = document.getElementById('fileUploadArea');
    const fileInput = document.getElementById('fileInput');
    
    fileUploadArea.addEventListener('click', () => fileInput.click());
    fileUploadArea.addEventListener('dragover', handleDragOver);
    fileUploadArea.addEventListener('drop', handleFileDrop);
    fileInput.addEventListener('change', handleFileSelect);
    
    // Reminder form
    document.getElementById('reminderForm').addEventListener('submit', addReminder);
}

// Tab switching
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.nav-tabs button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(tabName + 'Tab').classList.add('active');
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName + 'Content').classList.add('active');
    
    // Load data if needed
    if (tabName === 'reminders') {
        loadReminders();
    }
}

// Chat functionality
async function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat('user', message);
    chatInput.value = '';
    
    // Show loading
    const loadingId = addMessageToChat('assistant', '<div class="loading"><div class="spinner"></div></div>');
    
    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                user_id: currentUser.id
            })
        });
        
        const data = await response.json();
        
        // Remove loading message
        document.getElementById(loadingId).remove();
        
        if (response.ok) {
            addMessageToChat('assistant', data.response);
        } else {
            addMessageToChat('assistant', 'Sorry, I encountered an error processing your request. Please try again.');
        }
    } catch (error) {
        document.getElementById(loadingId).remove();
        addMessageToChat('assistant', 'Connection error. Please check if the server is running.');
        console.error('Chat error:', error);
    }
}

function addMessageToChat(sender, content) {
    const chatMessages = document.getElementById('chatMessages');
    const messageId = 'msg-' + Date.now();
    
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `message ${sender}`;
    
    const avatar = sender === 'user' ? currentUser.username.charAt(0).toUpperCase() : '🤖';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${content}</div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageId;
}

// File upload handling
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleFileDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFileUpload(file);
    }
}

async function handleFileUpload(file) {
    // Validate file type
    if (!file.type.startsWith('image/')) {
        addMessageToChat('assistant', 'Please upload an image file (JPG, PNG, etc.)');
        return;
    }
    
    // Add user message showing file upload
    addMessageToChat('user', `📎 Uploaded: ${file.name}`);
    
    // Show loading
    const loadingId = addMessageToChat('assistant', '<div class="loading"><div class="spinner"></div><p>Analyzing your medical report...</p></div>');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', currentUser.id);
        
        const response = await fetch(`${API_BASE}/upload-report`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // Remove loading message
        document.getElementById(loadingId).remove();
        
        if (response.ok) {
            addMessageToChat('assistant', data.analysis);
        } else {
            addMessageToChat('assistant', data.detail || 'Error analyzing the report. Please try again.');
        }
    } catch (error) {
        document.getElementById(loadingId).remove();
        addMessageToChat('assistant', 'Error uploading file. Please try again.');
        console.error('Upload error:', error);
    }
    
    // Clear file input
    document.getElementById('fileInput').value = '';
}

// Reminders functionality
async function addReminder(e) {
    e.preventDefault();
    
    const medicineName = document.getElementById('medicineName').value;
    const dosage = document.getElementById('dosage').value;
    const frequency = document.getElementById('frequency').value;
    const time = document.getElementById('reminderTime').value;
    
    try {
        const response = await fetch(`${API_BASE}/add-reminder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: currentUser.id,
                medicine_name: medicineName,
                dosage: dosage,
                frequency: frequency,
                time: time
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Clear form
            document.getElementById('reminderForm').reset();
            
            // Reload reminders
            loadReminders();
            
            // Show success message
            showAlert('Reminder added successfully!', 'success');
        } else {
            showAlert(data.detail || 'Error adding reminder', 'danger');
        }
    } catch (error) {
        showAlert('Connection error. Please try again.', 'danger');
        console.error('Add reminder error:', error);
    }
}

async function loadReminders() {
    try {
        const response = await fetch(`${API_BASE}/get-reminders?user_id=${currentUser.id}`);
        const data = await response.json();
        
        if (response.ok) {
            displayReminders(data.reminders);
        } else {
            console.error('Error loading reminders:', data.detail);
        }
    } catch (error) {
        console.error('Load reminders error:', error);
    }
}

function displayReminders(reminders) {
    const remindersList = document.getElementById('remindersList');
    
    if (reminders.length === 0) {
        remindersList.innerHTML = `
            <div class="text-center p-4 text-muted">
                No reminders yet. Add your first medication reminder above.
            </div>
        `;
        return;
    }
    
    remindersList.innerHTML = reminders.map(reminder => `
        <div class="reminder-item">
            <div class="reminder-info">
                <h4>💊 ${reminder.medicine_name}</h4>
                <div class="reminder-details">
                    <span>📏 ${reminder.dosage}</span> • 
                    <span>🔄 ${reminder.frequency}</span> • 
                    <span>⏰ ${reminder.time}</span>
                </div>
            </div>
            <div class="reminder-actions">
                <button class="btn btn-danger btn-sm" onclick="deleteReminder(${reminder.id})">
                    🗑️ Delete
                </button>
            </div>
        </div>
    `).join('');
}

async function deleteReminder(reminderId) {
    if (!confirm('Are you sure you want to delete this reminder?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/delete-reminder`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                reminder_id: reminderId,
                user_id: currentUser.id
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            loadReminders();
            showAlert('Reminder deleted successfully!', 'success');
        } else {
            showAlert(data.detail || 'Error deleting reminder', 'danger');
        }
    } catch (error) {
        showAlert('Connection error. Please try again.', 'danger');
        console.error('Delete reminder error:', error);
    }
}

// Utility functions
function showAlert(message, type) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    // Insert at top of current tab content
    const activeContent = document.querySelector('.tab-content.active');
    activeContent.insertBefore(alertDiv, activeContent.firstChild);
    
    // Remove after 3 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

function logout() {
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}