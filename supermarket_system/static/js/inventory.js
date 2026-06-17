const API = '/api/inventory/products';
let productModal;

document.addEventListener('DOMContentLoaded', () => {
    productModal = new bootstrap.Modal(document.getElementById('productModal'));
    loadCategories();
    loadProducts();
});

function showAlert(message, type = 'danger') {
    const alert = document.getElementById('inventoryAlert');
    alert.innerHTML = `<div class="alert alert-${type}" role="alert">${message}</div>`;
    setTimeout(() => { alert.innerHTML = ''; }, 5000);
}

async function loadCategories() {
    try {
        const res = await fetch('/api/inventory/categories');
        const result = await res.json();
        if (!result.success) return;

        const select = document.getElementById('categoryFilter');
        result.data.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = cat;
            select.appendChild(option);
        });
    } catch (err) {
        console.error('Error loading categories:', err);
    }
}

async function loadProducts() {
    try {
        const category = document.getElementById('categoryFilter').value;
        const search = document.getElementById('searchInput').value;
        let url = API + '?page=1&per_page=100';
        if (category) url += `&category=${category}`;
        if (search) url += `&search=${search}`;

        const res = await fetch(url);
        const result = await res.json();
        if (!result.success) return showAlert(result.error || 'Unable to load products');

        const tbody = document.getElementById('productsTableBody');
        tbody.innerHTML = '';
        result.data.forEach(product => {
            const status = product.quantity < product.min_stock ? 
                '<span class="badge bg-warning">Low Stock</span>' : 
                '<span class="badge bg-success">In Stock</span>';
            
            tbody.innerHTML += `
                <tr>
                    <td>${product.sku}</td>
                    <td>${product.name}</td>
                    <td>${product.category}</td>
                    <td>${product.price.toLocaleString('en-US', {minimumFractionDigits: 0})} UGX</td>
                    <td>${product.quantity}</td>
                    <td>${product.min_stock}</td>
                    <td>${status}</td>
                    <td>
                        <button class="btn btn-sm btn-primary me-1" onclick="editProduct(${product.id})">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteProduct(${product.id})">Delete</button>
                    </td>
                </tr>`;
        });
    } catch (err) {
        showAlert('Error loading products: ' + err.message);
    }
}

function openProductModal() {
    document.getElementById('productId').value = '';
    document.getElementById('productSku').value = '';
    document.getElementById('productName').value = '';
    document.getElementById('productCategory').value = '';
    document.getElementById('productPrice').value = '';
    document.getElementById('productQuantity').value = '0';
    document.getElementById('productMinStock').value = '10';
    document.getElementById('productSupplier').value = '';
    document.getElementById('productDescription').value = '';
    document.getElementById('productActive').checked = true;
    showAlert('');
    productModal.show();
}

async function editProduct(id) {
    try {
        const res = await fetch(`${API}/${id}`);
        const result = await res.json();
        if (!result.success) return showAlert(result.error || 'Unable to load product');

        const product = result.data;
        document.getElementById('productId').value = product.id;
        document.getElementById('productSku').value = product.sku;
        document.getElementById('productName').value = product.name;
        document.getElementById('productCategory').value = product.category;
        document.getElementById('productPrice').value = product.price;
        document.getElementById('productQuantity').value = product.quantity;
        document.getElementById('productMinStock').value = product.min_stock;
        document.getElementById('productSupplier').value = product.supplier || '';
        document.getElementById('productDescription').value = product.description || '';
        document.getElementById('productActive').checked = product.is_active;
        showAlert('');
        productModal.show();
    } catch (err) {
        showAlert('Error fetching product: ' + err.message);
    }
}

async function saveProduct() {
    const id = document.getElementById('productId').value;
    const payload = {
        sku: document.getElementById('productSku').value.trim(),
        name: document.getElementById('productName').value.trim(),
        category: document.getElementById('productCategory').value.trim(),
        price: parseFloat(document.getElementById('productPrice').value),
        quantity: parseInt(document.getElementById('productQuantity').value),
        min_stock: parseInt(document.getElementById('productMinStock').value),
        supplier: document.getElementById('productSupplier').value.trim(),
        description: document.getElementById('productDescription').value.trim(),
        is_active: document.getElementById('productActive').checked
    };

    if (!payload.sku || !payload.name) {
        return showAlert('SKU and name required', 'warning');
    }

    try {
        const method = id ? 'PUT' : 'POST';
        const url = id ? `${API}/${id}` : API;
        const res = await fetch(url, {
            method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (!result.success) return showAlert(result.error || 'Error saving product');
        productModal.hide();
        loadProducts();
    } catch (err) {
        showAlert('Error saving product: ' + err.message);
    }
}

async function deleteProduct(id) {
    if (!confirm('Deactivate this product?')) return;
    try {
        const res = await fetch(`${API}/${id}`, { method: 'DELETE' });
        const result = await res.json();
        if (!result.success) return showAlert(result.error || 'Error deleting product');
        loadProducts();
    } catch (err) {
        showAlert('Error deleting product: ' + err.message);
    }
}