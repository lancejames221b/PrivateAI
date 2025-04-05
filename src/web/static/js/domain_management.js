/**
 * Domain Management JavaScript
 * 
 * This file contains the JavaScript code for the domain management functionality
 * in the Private AI proxy.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const categorySelect = document.getElementById('categoryFilter');
    const domainsList = document.getElementById('domainsList');
    const addDomainForm = document.getElementById('addDomainForm');
    const saveDomainBtn = document.getElementById('saveDomainBtn');
    
    // Load domains based on selected category
    function loadDomainsByCategory(category) {
        // Show loading indicator
        domainsList.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p>Loading domains...</p></div>';
        
        // Fetch domains for the selected category
        fetch(`/ai_domains/category/${category}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.text();
            })
            .then(html => {
                // Replace the domains list with the new HTML
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = html;
                
                // Extract the domains table from the response
                const domainsTable = tempDiv.querySelector('.table-responsive');
                if (domainsTable) {
                    domainsList.innerHTML = '';
                    domainsList.appendChild(domainsTable);
                } else {
                    domainsList.innerHTML = '<div class="alert alert-info">No domains found for this category.</div>';
                }
                
                // Set up event listeners for the remove buttons
                setupRemoveButtons();
            })
            .catch(error => {
                console.error('Error loading domains:', error);
                domainsList.innerHTML = `<div class="alert alert-danger">Error loading domains: ${error.message}</div>`;
            });
    }
    
    // Setup event listeners for remove buttons
    function setupRemoveButtons() {
        const removeButtons = domainsList.querySelectorAll('.btn-outline-danger');
        removeButtons.forEach(button => {
            button.addEventListener('click', function(event) {
                event.preventDefault();
                const form = this.closest('form');
                const domain = form.querySelector('input[name="domain"]').value;
                
                if (confirm(`Are you sure you want to remove the domain "${domain}"?`)) {
                    fetch(form.action, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-CSRFToken': getCsrfToken()
                        }
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        // Reload the current category
                        loadDomainsByCategory(categorySelect.value);
                    })
                    .catch(error => {
                        console.error('Error removing domain:', error);
                        alert(`Error removing domain: ${error.message}`);
                    });
                }
            });
        });
    }
    
    // Get CSRF token from cookie
    function getCsrfToken() {
        const name = 'csrf_token=';
        const decodedCookie = decodeURIComponent(document.cookie);
        const cookieArray = decodedCookie.split(';');
        
        for (let i = 0; i < cookieArray.length; i++) {
            let cookie = cookieArray[i].trim();
            if (cookie.indexOf(name) === 0) {
                return cookie.substring(name.length, cookie.length);
            }
        }
        return '';
    }
    
    // Add domain event handler
    if (addDomainForm) {
        addDomainForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            const formData = new FormData(addDomainForm);
            
            fetch('/ai_domains/add', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCsrfToken()
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                // Reset form and reload domains
                addDomainForm.reset();
                // Reload the current category
                loadDomainsByCategory(categorySelect.value);
            })
            .catch(error => {
                console.error('Error adding domain:', error);
                alert(`Error adding domain: ${error.message}`);
            });
        });
    }
    
    // Category filter change event
    if (categorySelect) {
        categorySelect.addEventListener('change', function() {
            const selectedCategory = this.value;
            loadDomainsByCategory(selectedCategory);
        });
        
        // Load domains for the initially selected category
        loadDomainsByCategory(categorySelect.value);
    }
    
    // Save domains button event
    if (saveDomainBtn) {
        saveDomainBtn.addEventListener('click', function() {
            // Show saving indicator
            const originalText = saveDomainBtn.innerHTML;
            saveDomainBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
            saveDomainBtn.disabled = true;
            
            fetch('/ai_domains/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Show success message
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert alert-success alert-dismissible fade show';
                    alertDiv.innerHTML = `
                        <strong>Success!</strong> ${data.message}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    `;
                    document.querySelector('.container').prepend(alertDiv);
                    
                    // Auto-dismiss after 3 seconds
                    setTimeout(() => {
                        alertDiv.classList.remove('show');
                        setTimeout(() => alertDiv.remove(), 150);
                    }, 3000);
                } else {
                    throw new Error(data.message || 'Unknown error');
                }
            })
            .catch(error => {
                console.error('Error saving domains:', error);
                alert(`Error saving domains: ${error.message}`);
            })
            .finally(() => {
                // Restore button state
                saveDomainBtn.innerHTML = originalText;
                saveDomainBtn.disabled = false;
            });
        });
    }
    
    // Initial setup
    setupRemoveButtons();
});