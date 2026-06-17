const CATALOGUE_API = '/api/catalogue';

document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
    loadCatalogue();
});

async function loadCategories() {
    try {
        const resp = await fetch(`${CATALOGUE_API}/categories`);
        const result = await resp.json();
        if (!result.success) throw new Error(result.error || 'Failed to load categories');

        const select = document.getElementById('catalogueCategory');
        select.innerHTML = '<option value="">All Categories</option>';
        result.data.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.id;
            option.textContent = cat.name;
            select.appendChild(option);
        });
    } catch (err) {
        console.error('Catalogue category load error:', err);
    }
}

async function loadCatalogue(page = 1) {
    try {
        const search = document.getElementById('catalogueSearch').value.trim();
        const categoryId = document.getElementById('catalogueCategory').value;
        const minPrice = document.getElementById('catalogueMinPrice').value;
        const maxPrice = document.getElementById('catalogueMaxPrice').value;
        const inStock = document.getElementById('catalogueStock').value;

        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (categoryId) params.append('category_id', categoryId);
        if (minPrice) params.append('min_price', minPrice);
        if (maxPrice) params.append('max_price', maxPrice);
        if (inStock === 'true') params.append('in_stock', 'true');
        params.append('page', page);

        const resp = await fetch(`${CATALOGUE_API}/products?${params.toString()}`);
        const result = await resp.json();
        if (!result.success) throw new Error(result.error || 'Failed to load products');

        renderProducts(result.data);
    } catch (err) {
        console.error('Catalogue load error:', err);
    }
}

function renderProducts(products) {
    const container = document.getElementById('catalogueResults');
    const empty = document.getElementById('catalogueEmpty');
    container.innerHTML = '';

    if (!products.length) {
        empty.style.display = 'block';
        return;
    }
    empty.style.display = 'none';

    products.forEach(product => {
        const stockBadge = product.inventory && product.inventory.quantity_on_hand > 0
            ? '<span class="badge bg-success">In stock</span>'
            : '<span class="badge bg-secondary">Out of stock</span>';

        const imageUrl = product.image_url || '/static/images/product-placeholder.png';

        container.innerHTML += `
            <div class="col-md-3">
                <div class="card h-100">
                    <img src="${imageUrl}" class="card-img-top" alt="${product.name}" style="height:180px; object-fit:cover;">
                    <div class="card-body d-flex flex-column">
                        <h5 class="card-title">${product.name}</h5>
                        <p class="card-text text-muted">${product.brand || 'Brand unavailable'}</p>
                        <p class="mb-1"><strong>$${product.unit_price.toFixed(2)}</strong></p>
                        <p class="mb-1">${stockBadge}</p>
                        <p class="small text-muted">${product.tags.join(', ')}</p>
                        <div class="mt-auto">
                            <button class="btn btn-outline-primary btn-sm w-100"
                                    onclick="viewProductDetail(${product.id})">
                                View details
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
}

async function viewProductDetail(productId) {
    try {
        const resp = await fetch(`${CATALOGUE_API}/products/${productId}`);
        const result = await resp.json();
        if (!result.success) return alert(result.error || 'Product not found');

        const product = result.data;
        const detail = `
            <div>
                <h4>${product.name}</h4>
                <p><strong>SKU:</strong> ${product.sku}</p>
                <p><strong>Brand:</strong> ${product.brand || 'N/A'}</p>
                <p><strong>Category:</strong> ${product.category_name}</p>
                <p><strong>Price:</strong> $${product.unit_price.toFixed(2)}</p>
                <p><strong>Barcode:</strong> ${product.barcode || 'N/A'}</p>
                <p><strong>Stock:</strong> ${product.inventory ? product.inventory.quantity_on_hand : 0}</p>
                <p><strong>Description:</strong></p>
                <p>${product.description || 'No description available.'}</p>
            </div>
        `;
        const detailWindow = window.open('', '_blank', 'width=520,height=680');
        detailWindow.document.write(`
            <html>
                <head><title>${product.name}</title></head>
                <body>${detail}</body>
            </html>
        `);
        detailWindow.document.close();
    } catch (err) {
        console.error('Product detail error:', err);
        alert('Unable to load product details.');
    }
}