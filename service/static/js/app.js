// API Base URL
const API_BASE = '/api';

// DOM Elements
const flashMessage = document.getElementById('flash-message');
const customerForm = document.getElementById('customer-form');
const searchForm = document.getElementById('search-form');
const customerListContainer = document.getElementById('customer-list-container');
const createBtn = document.getElementById('create-btn');
const updateBtn = document.getElementById('update-btn');
const clearBtn = document.getElementById('clear-btn');
const listAllBtn = document.getElementById('list-all-btn');
const clearSearchBtn = document.getElementById('clear-search-btn');

// Form inputs
const customerIdInput = document.getElementById('customer-id');
const firstNameInput = document.getElementById('first-name');
const lastNameInput = document.getElementById('last-name');
const addressInput = document.getElementById('address');

// Utility Functions
function showFlash(message, type = 'success') {
    flashMessage.textContent = message;
    flashMessage.className = `flash-message ${type}`;
    flashMessage.classList.remove('hidden');
    
    setTimeout(() => {
        flashMessage.classList.add('hidden');
    }, 5000);
}

function clearForm() {
    customerForm.reset();
    customerIdInput.value = '';
    createBtn.classList.remove('hidden');
    updateBtn.classList.add('hidden');
}

// API Functions
async function createCustomer(data) {
    try {
        const response = await fetch(`${API_BASE}/customers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to create customer');
        }
        
        return await response.json();
    } catch (error) {
        throw error;
    }
}

async function updateCustomer(id, data) {
    try {
        const response = await fetch(`${API_BASE}/customers/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to update customer');
        }
        
        return await response.json();
    } catch (error) {
        throw error;
    }
}

async function deleteCustomer(id) {
    try {
        const response = await fetch(`${API_BASE}/customers/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok && response.status !== 204) {
            throw new Error('Failed to delete customer');
        }
    } catch (error) {
        throw error;
    }
}

async function getCustomer(id) {
    try {
        const response = await fetch(`${API_BASE}/customers/${id}`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Customer not found');
        }
        
        return await response.json();
    } catch (error) {
        throw error;
    }
}

async function listCustomers(queryParams = {}) {
    try {
        const params = new URLSearchParams();
        Object.keys(queryParams).forEach(key => {
            if (queryParams[key]) {
                params.append(key, queryParams[key]);
            }
        });
        
        const url = `${API_BASE}/customers${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to fetch customers');
        }
        
        return await response.json();
    } catch (error) {
        throw error;
    }
}

async function updateStatus(id, status) {
    try {
        const response = await fetch(`${API_BASE}/customers/${id}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to update status');
        }
        
        return await response.json();
    } catch (error) {
        throw error;
    }
}

// UI Functions
function renderCustomers(customers) {
    if (!customers || customers.length === 0) {
        customerListContainer.innerHTML = '<p class="empty-message">No customers found matching your search</p>';
        return;
    }
    
    const table = document.createElement('table');
    table.className = 'customer-table';
    
    table.innerHTML = `
        <thead>
            <tr>
                <th>ID</th>
                <th>First Name</th>
                <th>Last Name</th>
                <th>Address</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            ${customers.map(customer => `
                <tr>
                    <td>${customer.id}</td>
                    <td>${customer.first_name}</td>
                    <td>${customer.last_name}</td>
                    <td>${customer.address}</td>
                    <td>
                        <span class="status-badge status-${customer.status}">
                            ${customer.status}
                        </span>
                    </td>
                    <td class="actions">
                        <button class="btn btn-sm btn-info" onclick="loadCustomer(${customer.id})">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="confirmDelete(${customer.id})">Delete</button>
                        ${customer.status !== 'active' ? `<button class="btn btn-sm btn-success" onclick="changeStatus(${customer.id}, 'active')">Activate</button>` : ''}
                        ${customer.status !== 'deactivated' ? `<button class="btn btn-sm btn-warning" onclick="changeStatus(${customer.id}, 'deactivated')">Deactivate</button>` : ''}
                        ${customer.status !== 'suspended' ? `<button class="btn btn-sm btn-warning" onclick="changeStatus(${customer.id}, 'suspended')">Suspend</button>` : ''}
                    </td>
                </tr>
            `).join('')}
        </tbody>
    `;
    
    customerListContainer.innerHTML = '';
    customerListContainer.appendChild(table);
}

async function loadCustomer(id) {
    try {
        const customer = await getCustomer(id);
        
        customerIdInput.value = customer.id;
        firstNameInput.value = customer.first_name;
        lastNameInput.value = customer.last_name;
        addressInput.value = customer.address;
        
        createBtn.classList.add('hidden');
        updateBtn.classList.remove('hidden');
        
        // Scroll to form
        customerForm.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        showFlash('Error: ' + error.message, 'error');
    }
}

async function confirmDelete(id) {
    if (confirm('Are you sure you want to delete this customer?')) {
        try {
            await deleteCustomer(id);
            showFlash('Success: Customer deleted!', 'success');
            
            // Small delay to ensure backend processes the deletion
            await new Promise(resolve => setTimeout(resolve, 100));
            
            // Refresh the list
            await loadAllCustomers();
        } catch (error) {
            showFlash('Error: ' + error.message, 'error');
        }
    }
}

async function changeStatus(id, status) {
    try {
        await updateStatus(id, status);
        const statusText = status.charAt(0).toUpperCase() + status.slice(1);
        showFlash(`Success: Customer ${statusText.toLowerCase()}ed!`, 'success');
        await loadAllCustomers();
    } catch (error) {
        showFlash('Error: ' + error.message, 'error');
    }
}

async function loadAllCustomers() {
    try {
        const customers = await listCustomers();
        renderCustomers(customers);
    } catch (error) {
        showFlash('Error: ' + error.message, 'error');
    }
}

// Event Listeners
customerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Check if form is valid using HTML5 validation
    if (!customerForm.checkValidity()) {
        customerForm.reportValidity();  // Show validation messages
        return;
    }
    
    const data = {
        first_name: firstNameInput.value.trim(),
        last_name: lastNameInput.value.trim(),
        address: addressInput.value.trim()
    };
    
    // Additional validation for trimmed values
    if (!data.first_name || !data.last_name || !data.address) {
        showFlash('Error: All fields are required', 'error');
        return;
    }
    
    try {
        const customerId = customerIdInput.value;
        
        if (customerId) {
            // Update existing customer
            await updateCustomer(customerId, data);
            showFlash('Success: Customer updated!', 'success');
        } else {
            // Create new customer
            await createCustomer(data);
            showFlash('Success: Customer created!', 'success');
        }
        
        clearForm();
        await loadAllCustomers();
    } catch (error) {
        showFlash('Error: ' + error.message, 'error');
    }
});

updateBtn.addEventListener('click', async () => {
    customerForm.dispatchEvent(new Event('submit'));
});

clearBtn.addEventListener('click', clearForm);

searchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const queryParams = {};
    const searchId = document.getElementById('search-id').value.trim();
    const searchFirstName = document.getElementById('search-first-name').value.trim();
    const searchLastName = document.getElementById('search-last-name').value.trim();
    const searchAddress = document.getElementById('search-address').value.trim();
    
    if (searchId) queryParams.id = searchId;
    if (searchFirstName) queryParams.first_name = searchFirstName;
    if (searchLastName) queryParams.last_name = searchLastName;
    if (searchAddress) queryParams.address = searchAddress;
    
    try {
        const customers = await listCustomers(queryParams);
        renderCustomers(customers);
    } catch (error) {
        showFlash('Error: ' + error.message, 'error');
    }
});

listAllBtn.addEventListener('click', loadAllCustomers);

clearSearchBtn.addEventListener('click', () => {
    searchForm.reset();
    customerListContainer.innerHTML = '<p class="empty-message">Click "List All Customers" to view customers</p>';
});

// Make functions globally available for onclick handlers
window.loadCustomer = loadCustomer;
window.confirmDelete = confirmDelete;
window.changeStatus = changeStatus;

// Initial load
console.log('Customer Admin UI loaded successfully!');