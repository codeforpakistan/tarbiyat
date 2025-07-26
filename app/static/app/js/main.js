/**
 * Tarbiyat Platform - Main JavaScript Module
 * Centralized collection of reusable JavaScript functions
 */

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Format file size for display
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size string
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Debounce function for search inputs
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Format dates for display
 * @param {string} dateString - Date string to format
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// =============================================================================
// DOM MANIPULATION HELPERS
// =============================================================================

/**
 * Show element with fade-in animation
 * @param {HTMLElement} element - Element to show
 * @param {string} display - Display style (default: 'block')
 */
function showElement(element, display = 'block') {
    element.style.display = display;
    element.style.opacity = '0';
    element.style.transition = 'opacity 0.3s ease';
    setTimeout(() => {
        element.style.opacity = '1';
    }, 10);
}

/**
 * Hide element with fade-out animation
 * @param {HTMLElement} element - Element to hide
 */
function hideElement(element) {
    element.style.opacity = '0';
    element.style.transition = 'opacity 0.3s ease';
    setTimeout(() => {
        element.style.display = 'none';
    }, 300);
}

/**
 * Create and show notification toast
 * @param {string} message - Toast message
 * @param {string} type - Toast type: 'info', 'success', 'error'
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    const bgColor = type === 'error' ? 'bg-red-500' : type === 'success' ? 'bg-green-500' : 'bg-blue-500';
    
    toast.className = `fixed top-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 transform translate-x-full transition-transform duration-300`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Slide in
    setTimeout(() => {
        toast.classList.remove('translate-x-full');
    }, 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.classList.add('translate-x-full');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 5000);
}

/**
 * Show loading state on element
 * @param {HTMLElement} element - Element to show loading state
 * @param {string} loadingText - Loading text (default: 'Loading...')
 */
function showLoading(element, loadingText = 'Loading...') {
    element.disabled = true;
    element.setAttribute('data-original-text', element.textContent);
    element.textContent = loadingText;
}

/**
 * Hide loading state on element
 * @param {HTMLElement} element - Element to hide loading state
 */
function hideLoading(element) {
    element.disabled = false;
    const originalText = element.getAttribute('data-original-text');
    if (originalText) {
        element.textContent = originalText;
        element.removeAttribute('data-original-text');
    }
}

// =============================================================================
// FORM VALIDATION
// =============================================================================

/**
 * Generic form validation for required fields
 * @param {string} formId - Form element ID
 * @returns {boolean} True if all required fields are valid
 */
function validateRequired(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('border-red-500', 'bg-red-50');
            isValid = false;
        } else {
            field.classList.remove('border-red-500', 'bg-red-50');
        }
    });
    
    return isValid;
}

/**
 * File upload validation and display
 * @param {HTMLInputElement} input - File input element
 * @param {number} maxSizeMB - Maximum file size in MB (default: 5)
 */
function updateFileName(input, maxSizeMB = 5) {
    const fileNameElement = document.getElementById('file-name');
    if (!fileNameElement) return;
    
    if (input.files.length > 0) {
        const file = input.files[0];
        const fileName = file.name;
        const fileSize = (file.size / (1024 * 1024)).toFixed(2); // Size in MB
        const maxBytes = maxSizeMB * 1024 * 1024;
        
        if (file.size > maxBytes) {
            fileNameElement.innerHTML = `<span class="text-red-600">⚠️ File "${fileName}" is too large (${fileSize} MB). Maximum size: ${maxSizeMB}MB.</span>`;
            fileNameElement.className = 'text-red-500 mt-1';
        } else {
            fileNameElement.innerHTML = `📄 Selected: ${fileName} (${fileSize} MB)`;
            fileNameElement.className = 'text-green-600 mt-1';
        }
    } else {
        fileNameElement.innerHTML = `Upload your file in PDF, DOC, or DOCX format. Maximum file size: ${maxSizeMB}MB.`;
        fileNameElement.className = 'text-gray-500 mt-1';
    }
}

// =============================================================================
// DATE VALIDATION
// =============================================================================

/**
 * Update end date minimum based on start date
 * @param {string} startDateId - Start date input ID
 * @param {string} endDateId - End date input ID
 */
function updateEndDate(startDateId = 'start_date', endDateId = 'end_date') {
    const startDateInput = document.getElementById(startDateId);
    const endDateInput = document.getElementById(endDateId);
    
    if (!startDateInput || !endDateInput) return;
    
    if (startDateInput.value) {
        // Set minimum end date to start date
        endDateInput.min = startDateInput.value;
        
        // If end date is before start date, update it
        if (endDateInput.value && endDateInput.value < startDateInput.value) {
            endDateInput.value = startDateInput.value;
        }
    }
}

/**
 * Initialize date inputs with validation
 * @param {string} startDateId - Start date input ID
 * @param {string} endDateId - End date input ID
 */
function initializeDateValidation(startDateId = 'start_date', endDateId = 'end_date') {
    const startDateInput = document.getElementById(startDateId);
    const endDateInput = document.getElementById(endDateId);
    
    if (startDateInput) {
        startDateInput.addEventListener('change', () => updateEndDate(startDateId, endDateId));
    }
    
    // Set initial minimum dates to today
    const today = new Date().toISOString().split('T')[0];
    if (startDateInput) startDateInput.min = today;
    if (endDateInput) endDateInput.min = today;
    
    // Initial validation
    updateEndDate(startDateId, endDateId);
}

// =============================================================================
// MODAL MANAGEMENT
// =============================================================================

/**
 * Generic modal show function
 * @param {string} modalId - Modal element ID
 */
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
    }
}

/**
 * Generic modal hide function
 * @param {string} modalId - Modal element ID
 */
function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
    }
}

/**
 * Initialize modal with click outside and escape key handling
 * @param {string} modalId - Modal element ID
 * @param {string} closeButtonId - Close button ID (optional)
 */
function initializeModal(modalId, closeButtonId = null) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    // Close when clicking outside
    modal.addEventListener('click', function(e) {
        if (e.target === this) {
            hideModal(modalId);
        }
    });
    
    // Close with close button
    if (closeButtonId) {
        const closeButton = document.getElementById(closeButtonId);
        if (closeButton) {
            closeButton.addEventListener('click', () => hideModal(modalId));
        }
    }
    
    // Close with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            hideModal(modalId);
        }
    });
}

// =============================================================================
// AJAX HELPERS
// =============================================================================

/**
 * Make AJAX request with CSRF protection
 * @param {string} url - Request URL
 * @param {Object} data - Request data
 * @param {string} method - HTTP method (default: 'POST')
 * @returns {Promise} Fetch promise
 */
function makeAjaxRequest(url, data, method = 'POST') {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    
    return fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken ? csrfToken.value : '',
        },
        body: JSON.stringify(data)
    });
}

// =============================================================================
// URL HELPERS
// =============================================================================

/**
 * Build URL from pattern and parameters
 * @param {string} pattern - URL pattern with placeholders
 * @param {Object} params - Parameters to replace in pattern
 * @returns {string} Built URL
 */
function buildUrl(pattern, params) {
    let url = pattern;
    for (const [key, value] of Object.entries(params)) {
        url = url.replace(`<${key}>`, value);
    }
    return url;
}

// =============================================================================
// DOMAIN VERIFICATION
// =============================================================================

/**
 * Initialize domain verification warning for institute selection
 * @param {string} userEmail - User's email address
 * @param {string} selectId - Institute select element ID
 * @param {string} warningId - Warning element ID
 * @param {string} domainSpanId - Required domain span ID
 */
function initializeDomainVerification(userEmail, selectId = 'institute', warningId = 'domain-warning', domainSpanId = 'required-domain') {
    const instituteSelect = document.getElementById(selectId);
    const domainWarning = document.getElementById(warningId);
    const requiredDomainSpan = document.getElementById(domainSpanId);
    
    if (!instituteSelect || !domainWarning || !requiredDomainSpan) return;
    
    const userDomain = userEmail.split('@')[1];

    function checkDomainMatch() {
        const selectedOption = instituteSelect.selectedOptions[0];
        if (selectedOption) {
            const instituteDomain = selectedOption.dataset.domain;
            const isDomainVerified = selectedOption.dataset.verified === 'true';
            
            if (isDomainVerified && instituteDomain && instituteDomain !== userDomain) {
                requiredDomainSpan.textContent = instituteDomain;
                domainWarning.classList.remove('hidden');
            } else {
                domainWarning.classList.add('hidden');
            }
        }
    }

    // Check on page load
    checkDomainMatch();
    
    // Check when selection changes
    instituteSelect.addEventListener('change', checkDomainMatch);
}

// =============================================================================
// DJANGO FORMSET MANAGEMENT
// =============================================================================

/**
 * Initialize Django formset with add/delete functionality
 * @param {string} formsetContainerId - Container ID for the formset
 * @param {string} addButtonId - Add button ID
 * @param {string} totalFormsId - Total forms hidden input ID
 * @param {number|string} initialFormCount - Initial form count (can be Django template variable)
 * @param {number} maxForms - Maximum number of forms allowed
 */
function initializeFormset(formsetContainerId, addButtonId, totalFormsId, initialFormCount = null, maxForms = 10) {
    const formsetContainer = document.getElementById(formsetContainerId);
    const addButton = document.getElementById(addButtonId);
    const totalFormsInput = document.getElementById(totalFormsId);
    
    if (!formsetContainer || !addButton || !totalFormsInput) return;
    
    let formCount = initialFormCount !== null ? 
        (typeof initialFormCount === 'number' ? initialFormCount : parseInt(initialFormCount)) : 
        parseInt(totalFormsInput.value);
    
    function updateDeleteButtons() {
        const visibleForms = formsetContainer.querySelectorAll('.activity-form:not([style*="display: none"])');
        const deleteButtons = formsetContainer.querySelectorAll('.delete-activity');
        
        deleteButtons.forEach(btn => {
            btn.style.display = visibleForms.length > 1 ? 'block' : 'none';
        });
        
        // Hide add button if maximum forms reached
        if (formCount >= maxForms) {
            addButton.style.display = 'none';
        } else {
            addButton.style.display = 'inline-flex';
        }
    }
    
    // Add new form
    addButton.addEventListener('click', function() {
        if (formCount < maxForms) {
            const templateForm = formsetContainer.querySelector('.activity-form');
            if (!templateForm) return;
            
            const newForm = templateForm.cloneNode(true);
            const formRegex = RegExp(`form-\\d+-`, 'g');
            
            // Update form attributes
            newForm.innerHTML = newForm.innerHTML.replace(formRegex, `form-${formCount}-`);
            newForm.setAttribute('data-form-index', formCount);
            
            // Clear values
            newForm.querySelectorAll('input, textarea, select').forEach(input => {
                if (input.type === 'checkbox' || input.type === 'radio') {
                    input.checked = false;
                } else {
                    input.value = '';
                }
            });
            
            // Show the form and reset any hidden state
            newForm.style.display = 'block';
            
            // Update form title if present
            const title = newForm.querySelector('h4');
            if (title) title.textContent = `Activity ${formCount + 1}`;
            
            formsetContainer.appendChild(newForm);
            formCount++;
            totalFormsInput.value = formCount;
            updateDeleteButtons();
        }
    });
    
    // Delete form (event delegation)
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-activity')) {
            const form = e.target.closest('.activity-form');
            if (!form) return;
            
            const deleteCheckbox = form.querySelector('input[name$="-DELETE"]');
            
            if (deleteCheckbox) {
                // For existing forms, just mark for deletion
                deleteCheckbox.checked = true;
                form.style.display = 'none';
            } else {
                // For new forms, remove completely
                form.remove();
                formCount--;
                totalFormsInput.value = formCount;
                
                // Re-index remaining forms
                const remainingForms = formsetContainer.querySelectorAll('.activity-form');
                remainingForms.forEach((form, index) => {
                    const title = form.querySelector('h4');
                    if (title) title.textContent = `Activity ${index + 1}`;
                    
                    const inputs = form.querySelectorAll('input, textarea, select');
                    inputs.forEach(input => {
                        const name = input.name;
                        const id = input.id;
                        if (name) input.name = name.replace(/form-\d+-/, `form-${index}-`);
                        if (id) input.id = id.replace(/id_form-\d+-/, `id_form-${index}-`);
                    });
                    
                    const labels = form.querySelectorAll('label');
                    labels.forEach(label => {
                        const forAttr = label.getAttribute('for');
                        if (forAttr) label.setAttribute('for', forAttr.replace(/id_form-\d+-/, `id_form-${index}-`));
                    });
                });
            }
            
            updateDeleteButtons();
        }
    });
    
    // Initial setup
    updateDeleteButtons();
}

// =============================================================================
// APPLICATION WITHDRAWAL
// =============================================================================

/**
 * Show application withdrawal confirmation modal
 * @param {string} applicationId - Application ID
 * @param {string} positionTitle - Position title
 */
function confirmWithdraw(applicationId, positionTitle) {
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    const withdrawForm = document.getElementById('withdrawForm');
    const withdrawModal = document.getElementById('withdrawModal');
    
    if (modalTitle) modalTitle.textContent = 'Withdraw Application';
    if (modalMessage) {
        modalMessage.textContent = `Are you sure you want to withdraw your application for "${positionTitle}"? This action cannot be undone.`;
    }
    if (withdrawForm) {
        withdrawForm.action = `/applications/${applicationId}/withdraw/`;
    }
    if (withdrawModal) {
        withdrawModal.classList.remove('hidden');
    }
}

/**
 * Close withdrawal modal
 */
function closeModal() {
    const withdrawModal = document.getElementById('withdrawModal');
    if (withdrawModal) {
        withdrawModal.classList.add('hidden');
    }
}

// =============================================================================
// INITIALIZATION
// =============================================================================

/**
 * Initialize common functionality when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alert messages after 5 seconds
    const alerts = document.querySelectorAll('.alert, .message');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.5s ease-out';
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // Confirm deletion actions
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = button.getAttribute('data-confirm-delete') || 'Are you sure you want to delete this item?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Enhanced form validation
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    field.classList.add('border-red-500', 'bg-red-50');
                    isValid = false;
                } else {
                    field.classList.remove('border-red-500', 'bg-red-50');
                }
            });

            if (!isValid) {
                e.preventDefault();
                showToast('Please fill in all required fields.', 'error');
            }
        });
    });
    
    // Initialize mobile menu toggle
    const mobileMenuButton = document.getElementById("mobile-menu-button");
    const mobileMenu = document.getElementById("mobile-menu");

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener("click", function () {
            mobileMenu.classList.toggle("hidden");
        });
    }
    
    // Initialize common modals
    const commonModals = ['withdrawModal', 'confirmModal', 'deleteModal'];
    commonModals.forEach(modalId => {
        if (document.getElementById(modalId)) {
            initializeModal(modalId);
        }
    });
});

// =============================================================================
// LEGACY SUPPORT - TarbiyatApp namespace for backward compatibility
// =============================================================================

window.TarbiyatApp = {
    showLoading: showLoading,
    hideLoading: hideLoading,
    formatDate: formatDate,
    validateRequired: validateRequired,
    showToast: showToast,
    showModal: showModal,
    hideModal: hideModal,
    makeAjaxRequest: makeAjaxRequest,
    buildUrl: buildUrl
};

// =============================================================================
// EXPORT FOR MODULE SYSTEMS (if needed)
// =============================================================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatFileSize,
        debounce,
        formatDate,
        showElement,
        hideElement,
        showToast,
        showLoading,
        hideLoading,
        validateRequired,
        updateFileName,
        updateEndDate,
        initializeDateValidation,
        showModal,
        hideModal,
        initializeModal,
        makeAjaxRequest,
        buildUrl,
        initializeDomainVerification,
        confirmWithdraw,
        closeModal
    };
}
