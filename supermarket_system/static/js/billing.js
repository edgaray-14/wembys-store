const BILLING_API = '/api/billing';
let currentCart = null;
let selectedProduct = null;

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('productSearchInput').addEventListener('keypress', async event => {
        if (event.key === 'Enter') {
            event.preventDefault();
            await loadProductDetails();
        }
    });
});

async function createCart() {
    const customerName = document.getElementById('customerName').value.trim();

    const response = await fetch(`${BILLING_API}/carts`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            customer_name: customerName || null
            // cashier_id omitted; server will use logged-in employee
        })
    });
    const result = await response.json();
    if (!result.success) {
        return alert(result.error || 'Unable to create cart');
    }

    currentCart = result.data;
    document.getElementById('cartIdDisplay').textContent = currentCart.id;
    document.getElementById('invoiceNumber').textContent = currentCart.invoice_number;
    renderCart();
}

async function loadProductDetails() {
    const query = document.getElementById('productSearchInput').value.trim();
    if (!query) return alert('Enter SKU or product name');

    const response = await fetch(`/api/inventory/products?search=${encodeURIComponent(query)}`);
    const result = await response.json();
    if (!result.success) return alert('Unable to search product');

    if (result.data.length === 0) return alert('Product not found');
    selectedProduct = result.data[0];
    document.getElementById('productSearchInput').value = `${selectedProduct.sku} - ${selectedProduct.name}`;
}

async function addItemToCart() {
    if (!currentCart) return alert('Create a cart first');
    if (!selectedProduct) return alert('Load a product first');

    const quantity = parseInt(document.getElementById('productQty').value, 10);
    const discountType = document.getElementById('discountType').value;
    const discountValue = parseFloat(document.getElementById('discountValue').value || 0);

    if (quantity <= 0) return alert('Quantity must be greater than 0');

    const response = await fetch(`${BILLING_API}/carts/${currentCart.id}/items`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            product_id: selectedProduct.id,
            quantity,
            discount_type: discountType,
            discount_value: discountValue
        })
    });
    const result = await response.json();
    if (!result.success) return alert(result.error || 'Unable to add item');

    currentCart = result.data;
    renderCart();
}

function renderCart() {
    if (!currentCart) return;

    const tbody = document.getElementById('cartItemsBody');
    tbody.innerHTML = '';
    currentCart.items.forEach(item => {
        tbody.innerHTML += `
            <tr>
                <td>${item.sku}</td>
                <td>${item.product_name}</td>
                <td>${item.quantity}</td>
                <td>$${item.unit_price.toFixed(2)}</td>
                <td>${item.discount_type === 'PERCENT' ? item.discount_value + '%' : '$' + item.discount_value.toFixed(2)}</td>
                <td>$${item.line_total.toFixed(2)}</td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="editCartItem(${item.id})">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteCartItem(${item.id})">Delete</button>
                </td>
            </tr>
        `;
    });

    document.getElementById('subtotalAmount').textContent = `$${currentCart.subtotal.toFixed(2)}`;
    document.getElementById('discountAmount').textContent = `$${currentCart.discount_amount.toFixed(2)}`;
    document.getElementById('taxAmount').textContent = `$${currentCart.tax_amount.toFixed(2)}`;
    document.getElementById('totalAmount').textContent = `$${currentCart.total_amount.toFixed(2)}`;
}

async function editCartItem(itemId) {
    const newQuantity = parseInt(prompt('New quantity'), 10);
    if (!newQuantity || newQuantity <= 0) return;

    const discountValue = parseFloat(prompt('Discount value', '0')) || 0;
    const discountType = prompt('Discount type (AMOUNT or PERCENT)', 'AMOUNT').toUpperCase();

    const response = await fetch(`${BILLING_API}/carts/${currentCart.id}/items/${itemId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            quantity: newQuantity,
            discount_type: discountType,
            discount_value: discountValue
        })
    });
    const result = await response.json();
    if (!result.success) return alert(result.error || 'Unable to update item');

    currentCart = result.data;
    renderCart();
}

async function deleteCartItem(itemId) {
    if (!confirm('Remove this item from cart?')) return;

    const response = await fetch(`${BILLING_API}/carts/${currentCart.id}/items/${itemId}`, {
        method: 'DELETE'
    });
    const result = await response.json();
    if (!result.success) return alert(result.error || 'Unable to remove item');

    currentCart = result.data;
    renderCart();
}

async function checkoutCart() {
    if (!currentCart) return alert('Create a cart first');

    const paymentMethod = document.getElementById('paymentMethod').value;
    const paidAmount = parseFloat(document.getElementById('paidAmount').value);
    const reference = document.getElementById('paymentReference').value.trim();

    if (!paymentMethod) return alert('Select payment method');
    if (Number.isNaN(paidAmount) || paidAmount <= 0) return alert('Enter a valid paid amount');

    const response = await fetch(`${BILLING_API}/carts/${currentCart.id}/checkout`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            payment_method: paymentMethod,
            paid_amount: paidAmount,
            reference
        })
    });
    const result = await response.json();
    if (!result.success) return alert(result.error || 'Checkout failed');

    currentCart = result.data;
    renderCart();
    showReceipt(result.data);
}

function showReceipt(data) {
    const panel = document.getElementById('receiptPanel');
    const receipt = document.getElementById('receiptContent');

    receipt.innerHTML = `
        <div>
            <h5>Invoice ${data.invoice_number}</h5>
            <p>Customer: ${data.customer_name || 'Walk-in'}</p>
            <p>Status: ${data.status}</p>
            <table class="table table-sm">
                <thead><tr><th>Product</th><th>Qty</th><th>Total</th></tr></thead>
                <tbody>
                    ${data.items.map(item => `
                        <tr>
                            <td>${item.product_name}</td>
                            <td>${item.quantity}</td>
                            <td>$${item.line_total.toFixed(2)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            <p>Subtotal: $${data.subtotal.toFixed(2)}</p>
            <p>Tax: $${data.tax_amount.toFixed(2)}</p>
            <p>Total: $${data.total_amount.toFixed(2)}</p>
            <p>Paid: $${data.paid_amount.toFixed(2)}</p>
            <p>Change: $${data.change_amount.toFixed(2)}</p>
            <p>Payment: ${data.payment_method}</p>
        </div>
    `;
    panel.style.display = 'block';
}

function printReceipt() {
    window.print();
}