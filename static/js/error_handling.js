/**
 * Enhanced Error Handling for Private AI Proxy UI
 * 
 * This script provides improved error handling and user feedback
 * for the Private AI Proxy UI.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize error handling
    initErrorHandling();
});

/**
 * Initialize error handling functionality
 */
function initErrorHandling() {
    // Add error handling for proxy control buttons
    setupProxyControlErrorHandling();
    
    // Add error handling for settings forms
    setupSettingsFormErrorHandling();
    
    // Add error handling for domain management
    setupDomainManagementErrorHandling();
    
    // Add error recovery suggestions
    enhanceFlashMessages();
}

/**
 * Setup error handling for proxy control buttons
 */
function setupProxyControlErrorHandling() {
    // Get proxy control form
    const proxyControlForm = document.getElementById('proxy-control-form');
    if (!proxyControlForm) return;
    
    // Add error handling for form submission
    proxyControlForm.addEventListener('submit', function(event) {
        const button = this.querySelector('button[type="submit"]');
        const isStarting = button.textContent.includes('Start');
        
        // Add loading state
        button.disabled = true;
        const originalText = button.textContent;
        button.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ${isStarting ? 'Starting...' : 'Stopping...'}`;
        
        // Set a timeout to detect if the operation is taking too long
        setTimeout(function() {
            if (button.disabled) {
                // Create a warning message
                const warningDiv = document.createElement('div');
                warningDiv.className = 'alert alert-warning mt-2';
                warningDiv.textContent = `${isStarting ? 'Starting' : 'Stopping'} the proxy is taking longer than expected. This might indicate an issue.`;
                
                // Add the warning near the button
                const container = button.closest('.card-body');
                if (container && !container.querySelector('.timeout-warning')) {
                    warningDiv.classList.add('timeout-warning');
                    container.appendChild(warningDiv);
                }
            }
        }, 5000); // 5 seconds timeout
    });
    
    // Add error handling for test connection button
    const testButton = document.getElementById('test-proxy');
    if (testButton) {
        testButton.addEventListener('click', function() {
            // The existing code already handles most of this,
            // but we'll add a timeout warning
            setTimeout(function() {
                if (testButton.disabled) {
                    // Create a warning message
                    const warningDiv = document.createElement('div');
                    warningDiv.className = 'alert alert-warning mt-2';
                    warningDiv.textContent = 'Connection test is taking longer than expected. The proxy might not be running properly.';
                    
                    // Add the warning near the button
                    const container = testButton.closest('.card-body');
                    if (container && !container.querySelector('.timeout-warning')) {
                        warningDiv.classList.add('timeout-warning');
                        container.appendChild(warningDiv);
                    }
                }
            }, 3000); // 3 seconds timeout
        });
    }
}

/**
 * Setup error handling for settings forms
 */
function setupSettingsFormErrorHandling() {
    // Get settings save button
    const saveSettingsButton = document.getElementById('save-settings');
    if (!saveSettingsButton) return;
    
    saveSettingsButton.addEventListener('click', function() {
        // Add loading state
        this.disabled = true;
        const originalText = this.textContent;
        this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
        
        // Collect settings
        const settings = {
            pii_protection: document.getElementById('pii-protection')?.checked || false,
            domain_protection: document.getElementById('domain-protection')?.checked || false,
            security_protection: document.getElementById('security-protection')?.checked || false,
            api_protection: document.getElementById('api-protection')?.checked || false,
            inference_protection: document.getElementById('inference-protection')?.checked || false,
            code_protection: document.getElementById('code-protection')?.checked || false
        };
        
        // Send settings to server
        fetch('/api/update_privacy_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())
        .then(data => {
            // Reset button state
            this.disabled = false;
            this.textContent = originalText;
            
            // Show success or error message
            const alertDiv = document.createElement('div');
            alertDiv.className = data.success ? 'alert alert-success' : 'alert alert-danger';
            alertDiv.textContent = data.message || (data.success ? 'Settings saved successfully' : 'Failed to save settings');
            
            // Add close button
            const closeButton = document.createElement('button');
            closeButton.type = 'button';
            closeButton.className = 'btn-close';
            closeButton.setAttribute('data-bs-dismiss', 'alert');
            alertDiv.appendChild(closeButton);
            
            // Find the container and insert the alert
            const container = this.closest('.card-body');
            
            // Remove any existing alerts
            const existingAlerts = container.querySelectorAll('.alert:not(.timeout-warning)');
            existingAlerts.forEach(alert => alert.remove());
            
            // Add the new alert
            container.appendChild(alertDiv);
            
            // Auto dismiss after 5 seconds
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        })
        .catch(error => {
            // Reset button state
            this.disabled = false;
            this.textContent = originalText;
            
            // Show error message
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-danger';
            alertDiv.textContent = 'Error saving settings: ' + error.message;
            
            // Add close button
            const closeButton = document.createElement('button');
            closeButton.type = 'button';
            closeButton.className = 'btn-close';
            closeButton.setAttribute('data-bs-dismiss', 'alert');
            alertDiv.appendChild(closeButton);
            
            // Find the container and insert the alert
            const container = this.closest('.card-body');
            
            // Remove any existing alerts
            const existingAlerts = container.querySelectorAll('.alert:not(.timeout-warning)');
            existingAlerts.forEach(alert => alert.remove());
            
            // Add the new alert
            container.appendChild(alertDiv);
        });
    });
}

/**
 * Setup error handling for domain management
 */
function setupDomainManagementErrorHandling() {
    // Get domain save button
    const saveDomainsButton = document.getElementById('save-domains');
    if (!saveDomainsButton) return;
    
    saveDomainsButton.addEventListener('click', function() {
        // Add loading state
        this.disabled = true;
        const originalText = this.textContent;
        this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
        
        // Reset button state after a timeout (this is just a demo)
        setTimeout(() => {
            this.disabled = false;
            this.textContent = originalText;
            
            // Show success message (in a real app, this would be based on the server response)
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-success';
            alertDiv.textContent = 'Domains saved successfully';
            
            // Add close button
            const closeButton = document.createElement('button');
            closeButton.type = 'button';
            closeButton.className = 'btn-close';
            closeButton.setAttribute('data-bs-dismiss', 'alert');
            alertDiv.appendChild(closeButton);
            
            // Find the container and insert the alert
            const container = this.closest('.card-body');
            
            // Remove any existing alerts
            const existingAlerts = container.querySelectorAll('.alert');
            existingAlerts.forEach(alert => alert.remove());
            
            // Add the new alert
            container.appendChild(alertDiv);
            
            // Auto dismiss after 5 seconds
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }, 1000);
    });
}

/**
 * Enhance flash messages with more detailed error information and recovery suggestions
 */
function enhanceFlashMessages() {
    // Get all flash messages
    const flashMessages = document.querySelectorAll('.alert');
    
    flashMessages.forEach(message => {
        // Only enhance error messages
        if (!message.classList.contains('alert-danger')) return;
        
        // Get the error message text
        const errorText = message.textContent.trim();
        
        // Add recovery suggestions based on the error message
        if (errorText.includes('proxy') && (errorText.includes('start') || errorText.includes('launch'))) {
            addRecoverySuggestion(message, [
                'Check if another proxy is already running on the same port',
                'Verify that you have the necessary permissions to start the proxy',
                'Check the logs for more detailed error information'
            ]);
        } else if (errorText.includes('proxy') && errorText.includes('stop')) {
            addRecoverySuggestion(message, [
                'The proxy process might be stuck. Try stopping it manually',
                'Restart the application if the issue persists',
                'Check the logs for more detailed error information'
            ]);
        } else if (errorText.includes('certificate')) {
            addRecoverySuggestion(message, [
                'Make sure you have the necessary permissions to install certificates',
                'Try running the certificate installation script manually',
                'Check if your system supports the certificate format being used'
            ]);
        } else if (errorText.includes('database')) {
            addRecoverySuggestion(message, [
                'Verify that the database file exists and is not corrupted',
                'Check if you have write permissions to the database directory',
                'Restart the application to reinitialize the database connection'
            ]);
        }
    });
}

/**
 * Add recovery suggestions to an error message
 * 
 * @param {HTMLElement} messageElement - The error message element
 * @param {string[]} suggestions - Array of recovery suggestions
 */
function addRecoverySuggestion(messageElement, suggestions) {
    // Create a container for the suggestions
    const suggestionsContainer = document.createElement('div');
    suggestionsContainer.className = 'recovery-suggestions mt-2';
    
    // Add a heading
    const heading = document.createElement('strong');
    heading.textContent = 'Recovery suggestions:';
    suggestionsContainer.appendChild(heading);
    
    // Add the suggestions as a list
    const list = document.createElement('ul');
    list.className = 'mb-0 mt-1';
    
    suggestions.forEach(suggestion => {
        const item = document.createElement('li');
        item.textContent = suggestion;
        list.appendChild(item);
    });
    
    suggestionsContainer.appendChild(list);
    
    // Add the suggestions to the message
    messageElement.appendChild(suggestionsContainer);
}