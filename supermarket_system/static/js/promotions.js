const PROMO_API = '/api/promotions';
let promoModal;

document.addEventListener('DOMContentLoaded', () => {
    promoModal = new bootstrap.Modal(document.getElementById('promoModal'));
    loadPromotions();
});

function showAlert(message, type = 'danger') {
    const alert = document.getElementById('promoAlert');
    alert.innerHTML = `<div class="alert alert-${type}" role="alert">${message}</div>`;
    setTimeout(() => { alert.innerHTML = ''; }, 5000);
}

async function loadPromotions() {
    try {
        const res = await fetch(PROMO_API);
        const result = await res.json();
        if (!result.success) return showAlert(result.error || 'Unable to load promotions');

        const tbody = document.getElementById('promosTableBody');
        tbody.innerHTML = '';
        result.data.forEach(promo => {
            const startDate = new Date(promo.start_date).toLocaleDateString();
            const endDate = new Date(promo.end_date).toLocaleDateString();
            tbody.innerHTML += `
                <tr>
                    <td>${promo.name}</td>
                    <td>${promo.discount_type}</td>
                    <td>${promo.discount_value}</td>
                    <td>$${promo.min_purchase}</td>
                    <td>${startDate}</td>
                    <td>${endDate}</td>
                    <td>${promo.is_active ? 'Yes' : 'No'}</td>
                    <td>
                        <button class="btn btn-sm btn-primary me-1" onclick="editPromotion(${promo.id})">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="deletePromotion(${promo.id})">Deactivate</button>
                    </td>
                </tr>`;
        });
    } catch (err) {
        showAlert('Error loading promotions: ' + err.message);
    }
}

function openPromoModal() {
    document.getElementById('promoId').value = '';
    document.getElementById('promoName').value = '';
    document.getElementById('promoDescription').value = '';
    document.getElementById('promoDiscountType').value = 'PERCENT';
    document.getElementById('promoDiscountValue').value = '';
    document.getElementById('promoMinPurchase').value = '0';
    document.getElementById('promoMaxDiscount').value = '';
    document.getElementById('promoStartDate').value = '';
    document.getElementById('promoEndDate').value = '';
    document.getElementById('promoActive').checked = true;
    showAlert('');
    promoModal.show();
}

async function editPromotion(id) {
    try {
        const res = await fetch(`${PROMO_API}/${id}`);
        const result = await res.json();
        if (!result.success) return showAlert(result.error || 'Unable to load promotion');

        const promo = result.data;
        document.getElementById('promoId').value = promo.id;
        document.getElementById('promoName').value = promo.name;
        document.getElementById('promoDescription').value = promo.description || '';
        document.getElementById('promoDiscountType').value = promo.discount_type;
        document.getElementById('promoDiscountValue').value = promo.discount_value;
        document.getElementById('promoMinPurchase').value = promo.min_purchase;
        document.getElementById('promoMaxDiscount').value = promo.max_discount || '';
        document.getElementById('promoStartDate').value = promo.start_date.slice(0, 16);
        document.getElementById('promoEndDate').value = promo.end_date.slice(0, 16);
        document.getElementById('promoActive').checked = promo.is_active;
        showAlert('');
        promoModal.show();
    } catch (err) {
        showAlert('Error fetching promotion: ' + err.message);
    }
}

async function savePromotion() {
    const id = document.getElementById('promoId').value;
    const payload = {
        name: document.getElementById('promoName').value.trim(),
        description: document.getElementById('promoDescription').value.trim(),
        discount_type: document.getElementById('promoDiscountType').value,
        discount_value: parseFloat(document.getElementById('promoDiscountValue').value),
        min_purchase: parseFloat(document.getElementById('promoMinPurchase').value),
        max_discount: document.getElementById('promoMaxDiscount').value ? parseFloat(document.getElementById('promoMaxDiscount').value) : null,
        start_date: document.getElementById('promoStartDate').value,
        end_date: document.getElementById('promoEndDate').value,
        is_active: document.getElementById('promoActive').checked
    };

    if (!payload.name || !payload.discount_value) {
        return showAlert('Name and discount value required', 'warning');
    }

    try {
        const method = id ? 'PUT' : 'POST';
        const url = id ? `${PROMO_API}/${id}` : PROMO_API;
        const res = await fetch(url, {
            method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (!result.success) return showAlert(result.error || 'Error saving promotion');
        promoModal.hide();
        loadPromotions();
    } catch (err) {
        showAlert('Error saving promotion: ' + err.message);
    }
}

async function deletePromotion(id) {
    if (!confirm('Deactivate this promotion?')) return;
    try {
        const res = await fetch(`${PROMO_API}/${id}`, { method: 'DELETE' });
        const result = await res.json();
        if (!result.success) return showAlert(result.error || 'Error deactivating promotion');
        loadPromotions();
    } catch (err) {
        showAlert('Error deactivating promotion: ' + err.message);
    }
}