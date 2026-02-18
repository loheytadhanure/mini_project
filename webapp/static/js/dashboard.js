/**
 * Farm Health Monitoring Dashboard
 * Real-time dashboard for monitoring farm sensors, weed detection, and system status
 */

// Configuration
const CONFIG = {
    refreshInterval: 2000, // 2 seconds
    apiBase: '',
    chartMaxPoints: 20
};

// Chart instances
let tempChart = null;
let moistureChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌱 Farm Health Monitor initializing...');

    // Initialize Lucide icons
    lucide.createIcons();

    // Initialize charts
    initCharts();

    // Initialize heatmap grid
    initHeatmapGrid();

    // Start data fetching
    fetchAllData();

    // Set up auto-refresh
    setInterval(fetchAllData, CONFIG.refreshInterval);

    console.log('✅ Dashboard initialized successfully');
});

/**
 * Initialize Chart.js charts
 */
function initCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 500
        },
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            x: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.05)'
                },
                ticks: {
                    color: '#9ca3af',
                    maxTicksLimit: 8
                }
            },
            y: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.05)'
                },
                ticks: {
                    color: '#9ca3af'
                }
            }
        },
        elements: {
            line: {
                tension: 0.4,
                borderWidth: 2
            },
            point: {
                radius: 3,
                hoverRadius: 5
            }
        }
    };

    // Temperature Chart
    const tempCtx = document.getElementById('temp-chart').getContext('2d');
    tempChart = new Chart(tempCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Temperature (°C)',
                data: [],
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                fill: true
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    min: 15,
                    max: 45
                }
            }
        }
    });

    // Moisture Chart
    const moistureCtx = document.getElementById('moisture-chart').getContext('2d');
    moistureChart = new Chart(moistureCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Soil Moisture (%)',
                data: [],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    min: 0,
                    max: 100
                }
            }
        }
    });
}

/**
 * Initialize 5x5 heatmap grid
 */
function initHeatmapGrid() {
    const grid = document.getElementById('heatmap-grid');
    grid.innerHTML = '';

    for (let i = 0; i < 25; i++) {
        const cell = document.createElement('div');
        cell.className = 'heatmap-cell clean';
        cell.dataset.zone = i + 1;
        cell.textContent = i + 1;
        cell.title = `Zone ${i + 1}`;
        grid.appendChild(cell);
    }
}

/**
 * Fetch all data from APIs
 */
async function fetchAllData() {
    try {
        await Promise.all([
            fetchSensors(),
            // fetchCameraFrame(), // Canvas update removed, using img tag
            fetchPrediction(),
            fetchHeatmap(),
            fetchHistory(),
            fetchStatus(),
            fetchAlerts()
        ]);
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

/**
 * Fetch sensor data and update gauges
 */
async function fetchSensors() {
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/sensors`);
        const data = await response.json();

        if (data.status === 'disconnected') {
            updateGauge('temp-gauge', null, 0, 50, '°C');
            updateGauge('humidity-gauge', null, 0, 100, '%');
            updateGauge('moisture-gauge', null, 0, 100, '%');
        } else {
            updateGauge('temp-gauge', data.temperature, 0, 50, '°C');
            updateGauge('humidity-gauge', data.humidity, 0, 100, '%');
            updateGauge('moisture-gauge', data.moisture, 0, 100, '%');
        }
    } catch (error) {
        console.error('Error fetching sensors:', error);
    }
}

/**
 * Update a gauge with new value
 */
function updateGauge(gaugeId, value, min, max, unit) {
    const gauge = document.getElementById(gaugeId);
    if (!gauge) return;

    const fill = gauge.querySelector('.gauge-fill');
    const valueText = gauge.querySelector('.gauge-value');

    // Handle disconnected/null state
    if (value === null) {
        fill.style.strokeDashoffset = 314; // Empty
        valueText.textContent = '--';
        fill.classList.remove('warning', 'danger');
        return;
    }

    // Calculate percentage
    const percentage = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));

    // Calculate stroke-dashoffset (314 is full circle circumference for r=50)
    const circumference = 314;
    const offset = circumference - (percentage / 100 * circumference / 2);

    fill.style.strokeDashoffset = offset;
    valueText.textContent = value.toFixed(1);

    // Update color based on thresholds
    fill.classList.remove('warning', 'danger');

    if (gaugeId === 'temp-gauge') {
        if (value > 35) fill.classList.add('danger');
        else if (value > 30) fill.classList.add('warning');
    } else if (gaugeId === 'humidity-gauge') {
        if (value < 40) fill.classList.add('danger');
        else if (value < 50) fill.classList.add('warning');
    } else if (gaugeId === 'moisture-gauge') {
        if (value < 25) fill.classList.add('danger');
        else if (value < 35) fill.classList.add('warning');
    }
}

/**
 * Fetch camera frame and update canvas
 */
/**
 * Fetch camera frame - DEPRECATED/REMOVED
 * Handled by img tag src="/video_feed"
 */
async function fetchCameraFrame() {
    // No-op
}

/**
 * Draw a simulated field view on canvas
 */
function drawFieldSimulation(ctx, width, height) {
    // Create gradient for sky/field effect
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, '#1a3a1a');
    gradient.addColorStop(0.3, '#2d5a2d');
    gradient.addColorStop(1, '#1a2e1a');

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);

    // Draw grid lines to simulate field rows
    ctx.strokeStyle = 'rgba(16, 185, 129, 0.2)';
    ctx.lineWidth = 1;

    // Horizontal lines
    for (let y = 0; y < height; y += 40) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }

    // Draw some random "plants"
    for (let i = 0; i < 50; i++) {
        const x = Math.random() * width;
        const y = Math.random() * height;
        const size = Math.random() * 10 + 5;

        ctx.fillStyle = `rgba(${34 + Math.random() * 30}, ${139 + Math.random() * 50}, ${34 + Math.random() * 30}, 0.8)`;
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();
    }

    // Add timestamp overlay
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.fillRect(width - 180, height - 30, 170, 25);
    ctx.fillStyle = '#10b981';
    ctx.font = '12px Inter, sans-serif';
    ctx.fillText(new Date().toLocaleString(), width - 170, height - 12);
}

/**
 * Fetch weed detection prediction
 */
async function fetchPrediction() {
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/prediction`);
        const data = await response.json();

        const statusEl = document.getElementById('detection-status');
        const confidenceValue = document.getElementById('confidence-value');
        const confidenceFill = document.getElementById('confidence-fill');

        const isWeed = data.status === 'weed';
        const confidence = Math.round(data.confidence * 100);

        // Update status
        statusEl.className = `detection-status ${isWeed ? 'weed' : 'clean'}`;
        statusEl.innerHTML = `
            <i data-lucide="${isWeed ? 'alert-triangle' : 'check-circle'}"></i>
            <span>${isWeed ? 'Weed Detected!' : 'No Weed Found'}</span>
        `;

        // Update confidence
        confidenceValue.textContent = `${confidence}%`;
        confidenceFill.style.width = `${confidence}%`;

        // Reinitialize icons
        lucide.createIcons();

    } catch (error) {
        console.error('Error fetching prediction:', error);
    }
}

/**
 * Fetch and update heatmap grid
 */
async function fetchHeatmap() {
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/heatmap`);
        const data = await response.json();

        const cells = document.querySelectorAll('.heatmap-cell');
        let cleanCount = 0;
        let weedCount = 0;

        data.grid.flat().forEach((status, index) => {
            if (cells[index]) {
                cells[index].className = `heatmap-cell ${status}`;
                if (status === 'weed') weedCount++;
                else cleanCount++;
            }
        });

        // Update stats
        document.getElementById('clean-count').textContent = cleanCount;
        document.getElementById('weed-count').textContent = weedCount;

    } catch (error) {
        console.error('Error fetching heatmap:', error);
    }
}

/**
 * Fetch history data and update charts
 */
async function fetchHistory() {
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/history`);
        const data = await response.json();

        // Update temperature chart
        tempChart.data.labels = data.map(d => d.time);
        tempChart.data.datasets[0].data = data.map(d => d.temperature);
        tempChart.update('none');

        // Update moisture chart
        moistureChart.data.labels = data.map(d => d.time);
        moistureChart.data.datasets[0].data = data.map(d => d.moisture);
        moistureChart.update('none');

    } catch (error) {
        console.error('Error fetching history:', error);
    }
}

/**
 * Fetch system status
 */
async function fetchStatus() {
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/status`);
        const data = await response.json();

        // Update ESP32 status
        const espStatus = document.getElementById('esp-status');
        const isOnline = data.esp32 === 'online';
        espStatus.innerHTML = `
            <span class="status-dot ${isOnline ? 'online' : 'offline'}"></span>
            <span>ESP32: <strong>${isOnline ? 'Online' : 'Offline'}</strong></span>
        `;

        // Update last update time
        document.getElementById('last-update').innerHTML = `
            <i data-lucide="clock"></i>
            <span>Last Update: <strong>${data.lastUpdate.split(' ')[1]}</strong></span>
        `;

        // Update FPS
        document.getElementById('fps-display').innerHTML = `
            <i data-lucide="activity"></i>
            <span>FPS: <strong>${data.fps}</strong></span>
        `;

        // Reinitialize icons
        lucide.createIcons();

    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

/**
 * Fetch and update alerts
 */
async function fetchAlerts() {
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/alerts`);
        const alerts = await response.json();

        const container = document.getElementById('alerts-container');

        if (alerts.length === 0) {
            container.innerHTML = `
                <div class="alert-item info">
                    <i data-lucide="check-circle"></i>
                    <span>All systems normal</span>
                </div>
            `;
        } else {
            container.innerHTML = alerts.map(alert => `
                <div class="alert-item ${alert.type}">
                    <i data-lucide="${alert.icon}"></i>
                    <span>${alert.message}</span>
                </div>
            `).join('');
        }

        // Reinitialize icons
        lucide.createIcons();

    } catch (error) {
        console.error('Error fetching alerts:', error);
    }
}
