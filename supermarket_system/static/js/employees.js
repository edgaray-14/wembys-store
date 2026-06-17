const EMP_API = '/api/employees';
let employeeModal;

document.addEventListener('DOMContentLoaded', () => {
    employeeModal = new bootstrap.Modal(document.getElementById('employeeModal'));
    loadRoles();
    loadEmployees();
});

function showAlert(message, type = 'danger') {
    const alert = document.getElementById('employeeAlert');
    alert.innerHTML = `<div class="alert alert-${type}" role="alert">${message}</div>`;
    setTimeout(() => { alert.innerHTML = ''; }, 5000);
}

async function loadRoles() {
    try {
        const res = await fetch(`${EMP_API}/roles`);
        const result = await res.json();
        if (!result.success) return showAlert('Unable to load roles', 'warning');

        const select = document.getElementById('empRole');
        select.innerHTML = '<option value="">-- Select role --</option>';
        result.data.forEach(role => {
            const option = document.createElement('option');
            option.value = role.id;
            option.textContent = role.name;
            select.appendChild(option);
        });
    } catch (err) {
        showAlert('Error loading roles: ' + err.message);
    }
}

async function loadEmployees() {
    try {
        const res = await fetch(EMP_API);
        const result = await res.json();
        if (!result.success) return showAlert(result.error || 'Unable to load employees');

        const tbody = document.getElementById('employeesTableBody');
        tbody.innerHTML = '';
        result.data.forEach(emp => {
            tbody.innerHTML += `
                <tr>
                    <td>${emp.username}</td>
                    <td>${emp.full_name || ''}</td>
                    <td>${emp.role ? emp.role.name : ''}</td>
                    <td>${emp.email || ''}</td>
                    <td>${emp.is_active ? 'Yes' : 'No'}</td>
                    <td>
                        <button class="btn btn-sm btn-primary me-1" onclick="editEmployee(${emp.id})">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="deactivateEmployee(${emp.id})">Deactivate</button>
                    </td>
                </tr>`;
        });
    } catch (err) {
        showAlert('Error loading employees: ' + err.message);
    }
}

function openEmployeeModal() {
    document.getElementById('empId').value = '';
    document.getElementById('empUsername').value = '';
    document.getElementById('empPassword').value = '';
    document.getElementById('empFullName').value = '';
    document.getElementById('empEmail').value = '';
    document.getElementById('empPhone').value = '';
    document.getElementById('empRole').value = '';
    document.getElementById('empActive').checked = true;
    showAlert('');
    employeeModal.show();
}

async function editEmployee(id) {
    try {
        const res = await fetch(`${EMP_API}/${id}`);
        const result = await res.json();
        if (!result.success) return showAlert(result.error || 'Unable to load employee');

        const emp = result.data;
        document.getElementById('empId').value = emp.id;
        document.getElementById('empUsername').value = emp.username;
        document.getElementById('empPassword').value = '';
        document.getElementById('empFullName').value = emp.full_name || '';
        document.getElementById('empEmail').value = emp.email || '';
        document.getElementById('empPhone').value = emp.phone || '';
        document.getElementById('empRole').value = emp.role ? emp.role.id : '';
        document.getElementById('empActive').checked = emp.is_active;
        showAlert('');
        employeeModal.show();
    } catch (err) {
        showAlert('Error fetching employee: ' + err.message);
    }
}

async function saveEmployee() {
    const id = document.getElementById('empId').value;
    const payload = {
        username: document.getElementById('empUsername').value.trim(),
        password: document.getElementById('empPassword').value,
        full_name: document.getElementById('empFullName').value.trim(),
        email: document.getElementById('empEmail').value.trim(),
        phone: document.getElementById('empPhone').value.trim(),
        role_id: parseInt(document.getElementById('empRole').value) || null,
        is_active: document.getElementById('empActive').checked
    };

    if (!payload.username) {
        return showAlert('Username is required', 'warning');
    }

    try {
        const method = id ? 'PUT' : 'POST';
        const url = id ? `${EMP_API}/${id}` : EMP_API;
        const res = await fetch(url, {
            method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (!result.success) {
            return showAlert(result.error || 'Error saving employee');
        }
        employeeModal.hide();
        loadEmployees();
    } catch (err) {
        showAlert('Error saving employee: ' + err.message);
    }
}

async function deactivateEmployee(id) {
    if (!confirm('Deactivate this employee?')) return;
    try {
        const res = await fetch(`${EMP_API}/${id}`, { method: 'DELETE' });
        const result = await res.json();
        if (!result.success) return showAlert(result.error || 'Error deactivating employee');
        loadEmployees();
    } catch (err) {
        showAlert('Error deactivating employee: ' + err.message);
    }
}