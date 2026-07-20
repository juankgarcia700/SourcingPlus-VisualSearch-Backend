/* ==========================================================================
   Frontend JavaScript Controller - SourcingPlus Light Consulting Edition
   ========================================================================== */

// Globals
let uploadedFile = null;
let currentTab = 'search';

// Initialize events when DOM finishes loading
document.addEventListener('DOMContentLoaded', () => {
    initDragAndDrop();
    initInputs();
});

// Tab Switch Logic
function switchTab(tabName) {
    if (currentTab === tabName) return;

    // Toggle nav buttons
    document.getElementById('btn-tab-search').classList.toggle('active', tabName === 'search');
    document.getElementById('btn-tab-dashboard').classList.toggle('active', tabName === 'dashboard');

    // Toggle panels
    document.getElementById('tab-search').classList.toggle('active', tabName === 'search');
    document.getElementById('tab-dashboard').classList.toggle('active', tabName === 'dashboard');

    currentTab = tabName;

    // Fetch analytics if entering dashboard tab
    if (tabName === 'dashboard') {
        fetchDashboardStats();
        fetchTrending();
    }
}

// Drag & Drop Area Listeners
function initDragAndDrop() {
    const dropZone = document.getElementById('image-drop-zone');
    const fileSelector = document.getElementById('file-selector');

    // Clicking drop zone triggers hidden file input click
    dropZone.addEventListener('click', (e) => {
        // Prevent click trigger if clear button is clicked
        if (e.target.id === 'btn-clear-preview') return;
        fileSelector.click();
    });

    fileSelector.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Drag-over highlights
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
}

function handleFileSelect(file) {
    if (!file.type.startsWith('image/')) {
        alert('Por favor, selecciona únicamente archivos de imagen (PNG, JPG, JPEG).');
        return;
    }
    
    uploadedFile = file;

    // Clear URL input since file is preferred
    document.getElementById('input-image-url').value = '';

    // Show image preview
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('image-preview').src = e.target.result;
        document.getElementById('preview-wrapper').style.display = 'flex';
        // Hide standard drop prompt text
        document.querySelector('.drop-zone-prompt').style.display = 'none';
    };
    reader.readAsDataURL(file);
}

function clearImagePreview(e) {
    if (e) e.stopPropagation();
    
    uploadedFile = null;
    document.getElementById('file-selector').value = '';
    document.getElementById('image-preview').src = '';
    document.getElementById('preview-wrapper').style.display = 'none';
    
    // Restore prompt text
    document.querySelector('.drop-zone-prompt').style.display = 'flex';
}

function initInputs() {
    const slider = document.getElementById('slider-image-weight');
    const valueDisplay = document.getElementById('val-image-weight');
    
    // Realtime weight slider display update
    slider.addEventListener('input', (e) => {
        const percent = Math.round(e.target.value * 100);
        valueDisplay.textContent = `${percent}%`;
    });
}

// REST API Queries
async function executeSearch() {
    const loadingEl = document.getElementById('search-loading');
    const emptyEl = document.getElementById('search-empty');
    const gridEl = document.getElementById('results-grid');
    const telemetryEl = document.getElementById('search-telemetry');

    const imageUrl = document.getElementById('input-image-url').value.trim();
    const textQuery = document.getElementById('input-text-query').value.trim();
    const imageWeight = parseFloat(document.getElementById('slider-image-weight').value);
    const brand = document.getElementById('input-brand').value.trim();
    const category = document.getElementById('input-category').value.trim();
    const minPrice = document.getElementById('input-min-price').value;
    const maxPrice = document.getElementById('input-max-price').value;
    const inStockOnly = document.getElementById('check-in-stock').checked;

    // Validation: Image url or file is mandatory
    if (!uploadedFile && !imageUrl) {
        alert('Por favor, selecciona un archivo de imagen o introduce una URL para buscar.');
        return;
    }

    // Toggle elements to loading state
    emptyEl.style.display = 'none';
    gridEl.style.display = 'none';
    telemetryEl.style.display = 'none';
    loadingEl.style.display = 'flex';

    try {
        let responseData = null;

        if (uploadedFile) {
            // 1. Searching using file upload (FormData)
            // URL Query parameters mapping
            const params = new URLSearchParams({
                top_k: 10,
                score_threshold: 0.0,
                in_stock_only: inStockOnly
            });
            if (category) params.append('category', category);
            if (textQuery) params.append('text_query', textQuery);
            params.append('image_weight', imageWeight);
            if (minPrice) params.append('min_price', minPrice);
            if (maxPrice) params.append('max_price', maxPrice);
            if (brand) params.append('brand', brand);

            const formData = new FormData();
            formData.append('file', uploadedFile);

            const response = await fetch(`/api/v1/search/file?${params.toString()}`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Fallo de búsqueda por archivo');
            }
            responseData = await response.json();
        } else {
            // 2. Searching using URL endpoint (JSON Body payload)
            const payload = {
                image_url: imageUrl,
                top_k: 10,
                score_threshold: 0.0,
                in_stock_only: inStockOnly
            };
            if (category) payload.category = category;
            if (textQuery) payload.text_query = textQuery;
            payload.image_weight = imageWeight;
            if (minPrice) payload.min_price = parseFloat(minPrice);
            if (maxPrice) payload.max_price = parseFloat(maxPrice);
            if (brand) payload.brand = brand;

            const response = await fetch('/api/v1/search/url', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Fallo de búsqueda por URL');
            }
            responseData = await response.json();
        }

        // Render matches
        renderResults(responseData);

    } catch (err) {
        console.error(err);
        alert(`Error al buscar: ${err.message}`);
        loadingEl.style.display = 'none';
        emptyEl.style.display = 'flex';
    }
}

function renderResults(data) {
    const loadingEl = document.getElementById('search-loading');
    const gridEl = document.getElementById('results-grid');
    const telemetryEl = document.getElementById('search-telemetry');
    const emptyEl = document.getElementById('search-empty');

    loadingEl.style.display = 'none';
    gridEl.innerHTML = ''; // Clear grid

    const results = data.results || [];

    if (results.length === 0) {
        emptyEl.style.display = 'flex';
        // Customize text for no match
        emptyEl.querySelector('h4').textContent = 'Sin Coincidencias';
        emptyEl.querySelector('p').textContent = 'Ningún producto del catálogo coincide con tus filtros y similitud.';
        return;
    }

    // Populate Results
    results.forEach(item => {
        const card = document.createElement('div');
        card.className = 'product-card';

        const matchPercent = Math.round(item.score * 100);
        const stockStatus = item.inventory > 0 ? 'in' : 'out';
        const stockText = item.inventory > 0 ? `En Stock (${item.inventory})` : 'Agotado';
        const fallbackImg = 'https://picsum.photos/200'; // Fallback visual check
        const buyUrl = item.product_url || '#';

        card.innerHTML = `
            <div class="card-img-box">
                <img class="card-img" src="${item.image_url || fallbackImg}" onerror="this.src='${fallbackImg}'" alt="${item.title || 'Producto'}">
                <span class="match-badge">${matchPercent}% Match</span>
            </div>
            <div class="card-body">
                <span class="card-brand">${item.brand || 'Marca General'}</span>
                <h4 class="card-title" title="${item.title || item.sku}">${item.title || 'Producto sin Título'}</h4>
                <div class="card-meta-row">
                    <span class="card-price">$${item.price.toFixed(2)}</span>
                    <span class="card-stock ${stockStatus}">${stockText}</span>
                </div>
            </div>
            <a href="${buyUrl}" target="_blank" class="card-link">Detalles de Compra</a>
        `;
        gridEl.appendChild(card);
    });

    // Populate Telemetry details
    document.getElementById('tel-count').textContent = `${results.length} coincidencias`;
    document.getElementById('tel-time').textContent = `${data.took_ms} ms`;
    
    const cacheBadge = document.getElementById('tel-cache');
    cacheBadge.className = `badge-cache ${data.cache_hit ? 'hit' : 'miss'}`;
    cacheBadge.textContent = data.cache_hit ? 'Cache Hit' : 'Cache Miss';

    gridEl.style.display = 'grid';
    telemetryEl.style.display = 'flex';
}

// Fetch dashboard telemetry metrics
async function fetchDashboardStats() {
    try {
        const res = await fetch('/api/v1/analytics/stats');
        if (!res.ok) throw new Error('Error al consultar estadísticas');
        const data = await res.json();

        // Populate KPIs
        document.getElementById('kpi-total-queries').textContent = data.total_queries;
        document.getElementById('kpi-cache-rate').textContent = `${(data.cache_hit_rate * 100).toFixed(1)}%`;
        document.getElementById('kpi-avg-latency').textContent = `${data.average_took_ms} ms`;

        // Render distribution chart
        const dist = data.query_type_distribution || { url: 0, file: 0 };
        document.getElementById('lbl-dist-url').textContent = dist.url;
        document.getElementById('lbl-dist-file').textContent = dist.file;

        const totalDist = dist.url + dist.file;
        const urlPercent = totalDist > 0 ? (dist.url / totalDist) * 100 : 50;
        
        const progressBar = document.getElementById('bar-dist-url');
        progressBar.style.width = `${urlPercent}%`;

    } catch (err) {
        console.error(err);
    }
}

// Fetch top trending matches
async function fetchTrending() {
    const listEl = document.getElementById('trending-list');
    try {
        const res = await fetch('/api/v1/analytics/trending?top_k=5');
        if (!res.ok) throw new Error('Error al consultar productos trending');
        const data = await res.json();
        
        listEl.innerHTML = '';
        const results = data.results || [];

        if (results.length === 0) {
            listEl.innerHTML = '<p class="empty-trending">No se registran datos de consultas en el historial.</p>';
            return;
        }

        results.forEach((item, index) => {
            const row = document.createElement('div');
            row.className = 'trending-row';
            const fallbackImg = 'https://picsum.photos/100';

            row.innerHTML = `
                <span class="trend-rank">#${index + 1}</span>
                <div class="trend-img-box">
                    <img class="trend-img" src="${item.image_url || fallbackImg}" onerror="this.src='${fallbackImg}'" alt="Product">
                </div>
                <div class="trend-meta">
                    <h4 class="trend-title">${item.title || 'Producto sin Título'}</h4>
                    <span class="trend-brand">${item.brand || 'Marca General'} • $${item.price.toFixed(2)}</span>
                </div>
                <div class="trend-hits">
                    <span class="trend-hits-count">${item.search_hits}</span>
                    <span class="trend-hits-lbl">Coincidencias</span>
                </div>
            `;
            listEl.appendChild(row);
        });

    } catch (err) {
        console.error(err);
        listEl.innerHTML = '<p class="empty-trending">Error al cargar productos tendencia.</p>';
    }
}
