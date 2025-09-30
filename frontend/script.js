// Healthcare Dashboard JavaScript
const API_BASE = 'http://localhost:8000';
let currentUser = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    
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
    
    console.log('Dashboard initialized successfully');
});

// Debug: Catch any unexpected page refreshes
window.addEventListener('beforeunload', function(e) {
    console.log('Page is about to unload/refresh - this might be the issue!');
    console.trace('Page unload stack trace');
});

// Debug: Catch any navigation
window.addEventListener('popstate', function(e) {
    console.log('Navigation detected:', e);
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
    const loadingId = addMessageToChat('assistant', '<div class="loading"><div class="spinner"></div><div class="agent-indicator">Identifying agent…</div></div>');
    
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
        // Update the specific loader's agent indicator before removing loader
        try {
            if (data.agent) {
                const container = document.getElementById(loadingId);
                const indicator = container ? container.querySelector('.agent-indicator') : null;
                if (indicator) {
                    indicator.textContent = `Working agent: ${data.agent}`;
                }
            }
        } catch (e) {
            console.warn('Agent indicator update failed', e);
        }
        
        if (response.ok) {
            console.log('Chat response received:', data.response.substring(0, 100) + '...');
            const messageId = addMessageToChat('assistant', data.response);
            // Remove loading after showing final message
            const loadingElement = document.getElementById(loadingId);
            if (loadingElement) {
                loadingElement.remove();
            }
            
            // Check if this is a reminder-related response
            if (data.response.includes('Medication Reminder Added') || 
                data.response.includes('Reminder Deleted') || 
                data.response.includes('Reminder Updated')) {
                console.log('Reminder operation detected in chat - NOT refreshing page');
                
                // Highlight the response message to make it more visible
                const messageElement = document.getElementById(messageId);
                if (messageElement) {
                    messageElement.style.border = '2px solid #28a745';
                    messageElement.style.backgroundColor = '#f8fff9';
                    
                    // Remove highlight after 5 seconds
                    setTimeout(() => {
                        messageElement.style.border = '';
                        messageElement.style.backgroundColor = '';
                    }, 5000);
                }
                
                // Show notification that reminders tab has new data
                if (document.getElementById('remindersTab')) {
                    const remindersTab = document.getElementById('remindersTab');
                    remindersTab.style.background = '#e3f2fd';
                    remindersTab.innerHTML = '⏰ Reminders <span style="color: #007bff;">●</span>';
                    
                    setTimeout(() => {
                        remindersTab.style.background = '';
                        remindersTab.innerHTML = '⏰ Reminders';
                    }, 5000);
                }
                
                // Add a persistent success indicator
                showAlert('✅ Reminder operation completed! Check the Reminders tab for updates.', 'success', true);
            }
        } else {
            addMessageToChat('assistant', 'Sorry, I encountered an error processing your request. Please try again.');
        }
    } catch (error) {
        // Remove loading message safely
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) {
            loadingElement.remove();
            console.log('Chat loading removed after error');
        } else {
            console.warn('Chat loading element not found after error:', loadingId);
        }
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
    
    // Convert markdown to HTML for assistant messages
    const processedContent = sender === 'assistant' ? convertMarkdownToHTML(content) : content;
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${processedContent}</div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageId;
}

function convertMarkdownToHTML(text) {
    // Skip conversion if it's already HTML (contains loading spinner)
    if (text.includes('<div class="loading">')) {
        return text;
    }
    
    return text
        // Headers
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^# (.*$)/gm, '<h1>$1</h1>')
        
        // Bold text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        
        // Code blocks
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        
        // Inline code
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        
        // Unordered lists
        .replace(/^\- (.*$)/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
        
        // Line breaks
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>')
        
        // Horizontal rules
        .replace(/^---$/gm, '<hr>');
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
        
        // Remove loading message safely
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) {
            loadingElement.remove();
            console.log('Upload loading removed successfully');
        } else {
            console.warn('Upload loading element not found:', loadingId);
        }
        
        if (response.ok) {
            addMessageToChat('assistant', data.analysis);
        } else {
            addMessageToChat('assistant', data.detail || 'Error analyzing the report. Please try again.');
        }
    } catch (error) {
        // Remove loading message safely
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) {
            loadingElement.remove();
            console.log('Upload loading removed after error');
        } else {
            console.warn('Upload loading element not found after error:', loadingId);
        }
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
            if (data.success) {
                // Clear form
                document.getElementById('reminderForm').reset();
                
                // Reload reminders
                loadReminders();
                
                // Show success message
                showAlert('✅ Reminder added successfully!', 'success');
            } else if (data.interaction_warning) {
                // Show interaction warning with options
                showInteractionWarning(data, {
                    medicine_name: medicineName,
                    dosage: dosage,
                    frequency: frequency,
                    time: time
                });
            }
        } else {
            showAlert(data.detail || 'Error adding reminder', 'danger');
        }
    } catch (error) {
        showAlert('Connection error. Please try again.', 'danger');
        console.error('Add reminder error:', error);
    }
}

function showInteractionWarning(interactionData, reminderData) {
    // Create interaction warning modal/alert
    const warningDiv = document.createElement('div');
    warningDiv.className = 'interaction-warning-modal';
    warningDiv.innerHTML = `
        <div class="interaction-warning-content">
            <div class="interaction-warning-header">
                <h4>⚠️ Drug Interaction Warning</h4>
            </div>
            <div class="interaction-warning-body">
                <p><strong>New Medication:</strong> ${reminderData.medicine_name}</p>
                <p><strong>Dosage:</strong> ${reminderData.dosage}</p>
                <p><strong>Frequency:</strong> ${reminderData.frequency}</p>
                <p><strong>Time:</strong> ${reminderData.time}</p>
                
                <div class="interaction-details">
                    <h5>🚨 Interaction Alert:</h5>
                    <div class="interaction-text">${formatInteractionText(interactionData.interaction_details)}</div>
                </div>
                
                <div class="conflicting-drugs">
                    <h5>💊 Current Medications:</h5>
                    <ul>
                        ${interactionData.conflicting_drugs.map(drug => `<li>${drug.charAt(0).toUpperCase() + drug.slice(1)}</li>`).join('')}
                    </ul>
                </div>
                
                <p class="safety-note">
                    <strong>⚠️ This medication may interact with your current medications.</strong>
                </p>
                
                <div class="interaction-options">
                    <h5>Your Options:</h5>
                    <button class="btn btn-danger" onclick="forceAddReminder(${JSON.stringify(reminderData).replace(/"/g, '&quot;')})">
                        ⚠️ Add Anyway (Not Recommended)
                    </button>
                    <button class="btn btn-secondary" onclick="closeInteractionWarning()">
                        🚫 Cancel
                    </button>
                    <button class="btn btn-info" onclick="consultDoctor()">
                        👨‍⚕️ Consult Doctor First
                    </button>
                </div>
                
                <p class="disclaimer">
                    <em>Your safety is important. Please consult a healthcare professional before proceeding.</em>
                </p>
            </div>
        </div>
        <div class="interaction-warning-backdrop" onclick="closeInteractionWarning()"></div>
    `;
    
    document.body.appendChild(warningDiv);
}

function formatInteractionText(interactionDetails) {
    // Convert the interaction details to HTML format
    return interactionDetails
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>')
        .replace(/• /g, '<br>• ');
}

async function forceAddReminder(reminderData) {
    try {
        const response = await fetch(`${API_BASE}/force-add-reminder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: currentUser.id,
                medicine_name: reminderData.medicine_name,
                dosage: reminderData.dosage,
                frequency: reminderData.frequency,
                time: reminderData.time
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Clear form
            document.getElementById('reminderForm').reset();
            
            // Reload reminders
            loadReminders();
            
            // Close warning modal
            closeInteractionWarning();
            
            // Show success message with warning
            showAlert('⚠️ Reminder added despite interaction warning. Please monitor for side effects and consult your healthcare provider.', 'warning', true);
        } else {
            showAlert(data.detail || 'Error adding reminder', 'danger');
        }
    } catch (error) {
        showAlert('Connection error. Please try again.', 'danger');
        console.error('Force add reminder error:', error);
    }
}

function closeInteractionWarning() {
    const warningModal = document.querySelector('.interaction-warning-modal');
    if (warningModal) {
        warningModal.remove();
    }
}

function consultDoctor() {
    closeInteractionWarning();
    showAlert('💡 Good choice! Please consult your doctor or pharmacist about this medication combination before adding the reminder.', 'info', true);
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
function showAlert(message, type, persistent = false) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    
    // Insert at top of current tab content
    const activeContent = document.querySelector('.tab-content.active');
    activeContent.insertBefore(alertDiv, activeContent.firstChild);
    
    // Remove after specified time (longer for persistent alerts)
    const timeout = persistent ? 8000 : 3000;
    setTimeout(() => {
        if (alertDiv.parentElement) {
            alertDiv.remove();
        }
    }, timeout);
}

function logout() {
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}