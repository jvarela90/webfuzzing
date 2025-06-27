/* web/static/js/app.js */
// JavaScript principal para WebFuzzing Pro

class WebFuzzingApp {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.init();
    }

    init() {
        this.initializeSocket();
        this.setupEventListeners();
        this.startPeriodicUpdates();
        this.initializeCharts();
    }

    initializeSocket() {
        if (typeof io !== 'undefined') {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('Conectado al servidor WebSocket');
                this.updateConnectionStatus(true);
            });

            this.socket.on('disconnect', () => {
                console.log('Desconectado del servidor WebSocket');
                this.updateConnectionStatus(false);
            });

            this.socket.on('new_finding', (data) => {
                this.handleNewFinding(data);
            });

            this.socket.on('new_alert', (data) => {
                this.handleNewAlert(data);
            });

            this.socket.on('scan_progress', (data) => {
                this.updateScanProgress(data);
            });
        }
    }

    updateConnectionStatus(connected) {
        const indicator = document.getElementById('connectionStatus');
        if (indicator) {
            indicator.style.backgroundColor = connected ? '#28a745' : '#dc3545';
            indicator.title = connected ? 'Conectado' : 'Desconectado';
        }
    }

    handleNewFinding(data) {
        // Mostrar notificación
        if (data.is_critical) {
            this.showNotification(
                `Nuevo hallazgo crítico: ${data.path}`,
                'critical',
                {
                    persistent: true,
                    action: {
                        text: 'Ver',
                        callback: () => window.open(data.url, '_blank')
                    }
                }
            );
        } else {
            this.showNotification(`Nueva ruta encontrada: ${data.path}`, 'info');
        }

        // Actualizar contadores
        this.updateDashboardStats();

        // Agregar a tabla si estamos en la página de hallazgos
        this.addFindingToTable(data);
    }

    handleNewAlert(data) {
        // Actualizar contador de alertas
        this.updateAlertCounter();

        // Mostrar notificación
        this.showNotification(
            `Nueva alerta: ${data.title}`,
            data.severity === 'high' ? 'critical' : 'warning',
            {
                persistent: data.severity === 'high',
                action: {
                    text: 'Ver Alerta',
                    callback: () => window.location.href = `/alert/${data.id}`
                }
            }
        );
    }

    updateScanProgress(data) {
        const progressBar = document.getElementById('scanProgress');
        if (progressBar) {
            const percent = (data.completed / data.total) * 100;
            progressBar.style.width = `${percent}%`;
            progressBar.setAttribute('aria-valuenow', percent);
            progressBar.textContent = `${Math.round(percent)}%`;
        }

        const statusText = document.getElementById('scanStatus');
        if (statusText) {
            statusText.textContent = data.status;
        }
    }

    showNotification(message, type = 'info', options = {}) {
        const toast = this.createToast(message, type, options);
        const container = this.getToastContainer();
        container.appendChild(toast);

        // Mostrar toast
        const bsToast = new bootstrap.Toast(toast, {
            delay: options.persistent ? 0 : 5000
        });
        bsToast.show();

        // Auto-remove después de ser ocultado
        toast.addEventListener('hidden.bs.toast', () => {
            container.removeChild(toast);
        });
    }

    createToast(message, type, options) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        const icon = this.getIconForType(type);
        const actionButton = options.action 
            ? `<button type="button" class="btn btn-sm btn-outline-primary ms-2" onclick="(${options.action.callback.toString()})()">${options.action.text}</button>`
            : '';

        toast.innerHTML = `
            <div class="toast-header">
                <i class="fas ${icon} me-2"></i>
                <strong class="me-auto">WebFuzzing Pro</strong>
                <small class="text-muted">${new Date().toLocaleTimeString()}</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
                ${actionButton}
            </div>
        `;

        return toast;
    }

    getIconForType(type) {
        const icons = {
            'critical': 'fa-exclamation-triangle',
            'warning': 'fa-exclamation-circle',
            'info': 'fa-info-circle',
            'success': 'fa-check-circle'
        };
        return icons[type] || icons.info;
    }

    getToastContainer() {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }

    updateDashboardStats() {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                this.updateStatElement('totalDomains', data.total_domains);
                this.updateStatElement('recentFindings', data.recent_findings);
                this.updateStatElement('criticalFindings', data.critical_findings);
                this.updateStatElement('newAlerts', data.new_alerts);
                
                this.updateAlertCounter(data.new_alerts);
            })
            .catch(error => console.error('Error actualizando estadísticas:', error));
    }

    updateStatElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            // Animación de cambio de número
            const currentValue = parseInt(element.textContent) || 0;
            if (currentValue !== value) {
                this.animateNumber(element, currentValue, value);
            }
        }
    }

    animateNumber(element, from, to) {
        const duration = 1000;
        const steps = 30;
        const stepValue = (to - from) / steps;
        let currentStep = 0;

        const timer = setInterval(() => {
            currentStep++;
            const currentValue = Math.round(from + (stepValue * currentStep));
            element.textContent = currentValue;

            if (currentStep >= steps) {
                clearInterval(timer);
                element.textContent = to;
            }
        }, duration / steps);
    }

    updateAlertCounter(count = null) {
        const counter = document.getElementById('alertCounter');
        if (counter) {
            if (count === null) {
                // Incrementar contador actual
                const currentCount = parseInt(counter.textContent) || 0;
                count = currentCount + 1;
            }

            counter.textContent = count;
            counter.style.display = count > 0 ? 'inline' : 'none';

            // Animación de atención si hay nuevas alertas
            if (count > 0) {
                counter.classList.add('animate__animated', 'animate__pulse');
                setTimeout(() => {
                    counter.classList.remove('animate__animated', 'animate__pulse');
                }, 1000);
            }
        }
    }

    addFindingToTable(finding) {
        const table = document.querySelector('#findingsTable tbody');
        if (!table) return;

        const row = document.createElement('tr');
        row.className = `finding-row ${finding.is_critical ? 'critical' : ''}`;
        row.innerHTML = `
            <td><code>${finding.path}</code></td>
            <td><span class="badge bg-${finding.status_code === 200 ? 'success' : 'warning'}">${finding.status_code}</span></td>
            <td>${finding.is_critical ? '<span class="critical-badge">CRÍTICO</span>' : '<span class="badge bg-secondary">Normal</span>'}</td>
            <td><small>${new Date().toLocaleString()}</small></td>
            <td>
                <a href="${finding.url}" target="_blank" class="btn btn-sm btn-outline-primary">
                    <i class="fas fa-external-link-alt"></i>
                </a>
            </td>
        `;

        // Insertar al inicio de la tabla
        table.insertBefore(row, table.firstChild);

        // Limitar número de filas mostradas
        const maxRows = 100;
        const rows = table.querySelectorAll('tr');
        if (rows.length > maxRows) {
            table.removeChild(rows[rows.length - 1]);
        }

        // Animación de entrada
        row.classList.add('fade-in');
    }

    setupEventListeners() {
        // Búsqueda en tablas
        this.setupTableSearch();

        // Filtros
        this.setupFilters();

        // Botones de acción
        this.setupActionButtons();

        // Auto-refresh
        this.setupAutoRefresh();
    }

    setupTableSearch() {
        const searchInputs = document.querySelectorAll('.table-search');
        searchInputs.forEach(input => {
            input.addEventListener('input', (e) => {
                this.filterTable(e.target.value, e.target.dataset.table);
            });
        });
    }

    filterTable(searchTerm, tableId) {
        const table = document.getElementById(tableId);
        if (!table) return;

        const rows = table.querySelectorAll('tbody tr');
        const term = searchTerm.toLowerCase();

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(term) ? '' : 'none';
        });
    }

    setupFilters() {
        const filterButtons = document.querySelectorAll('.filter-btn');
        filterButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.applyFilter(e.target.dataset.filter, e.target.dataset.table);
                
                // Actualizar estado visual de botones
                const buttonGroup = e.target.parentElement;
                buttonGroup.querySelectorAll('.btn').forEach(btn => {
                    btn.classList.remove('btn-primary');
                    btn.classList.add('btn-outline-primary');
                });
                
                e.target.classList.remove('btn-outline-primary');
                e.target.classList.add('btn-primary');
            });
        });
    }

    applyFilter(filterType, tableId) {
        const table = document.getElementById(tableId);
        if (!table) return;

        const rows = table.querySelectorAll('tbody tr');

        rows.forEach(row => {
            let show = false;

            switch (filterType) {
                case 'all':
                    show = true;
                    break;
                case 'critical':
                    show = row.classList.contains('critical');
                    break;
                case 'recent':
                    const dateCell = row.querySelector('td:last-child small');
                    if (dateCell) {
                        const dateText = dateCell.textContent;
                        const cellDate = new Date(dateText);
                        const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
                        show = cellDate > oneDayAgo;
                    }
                    break;
            }

            row.style.display = show ? '' : 'none';
        });
    }

    setupActionButtons() {
        // Botones de escaneo
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-scan')) {
                this.handleScanButton(e.target);
            }
        });

        // Botones de exportación
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-export')) {
                this.handleExportButton(e.target);
            }
        });
    }

    handleScanButton(button) {
        const domain = button.dataset.domain;
        const scanType = button.dataset.scanType || 'general';

        if (confirm(`¿Iniciar escaneo ${scanType} para ${domain || 'todos los dominios'}?`)) {
            this.startScan(domain, scanType, button);
        }
    }

    startScan(domain, scanType, button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<span class="loading-spinner"></span> Escaneando...';
        button.disabled = true;

        const payload = { scan_type: scanType };
        if (domain) payload.domain = domain;

        fetch('/api/v1/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': window.API_KEY || 'demo-key'
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                this.showNotification('Escaneo iniciado exitosamente', 'success');
            } else {
                throw new Error(data.error || 'Error desconocido');
            }
        })
        .catch(error => {
            this.showNotification(`Error iniciando escaneo: ${error.message}`, 'critical');
        })
        .finally(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        });
    }

    handleExportButton(button) {
        const format = button.dataset.format || 'csv';
        const filters = button.dataset.filters || '';
        
        window.location.href = `/export/findings?format=${format}&${filters}`;
    }

    setupAutoRefresh() {
        // Auto-refresh cada 30 segundos para páginas específicas
        const autoRefreshPages = ['/', '/findings', '/alerts'];
        const currentPath = window.location.pathname;

        if (autoRefreshPages.includes(currentPath)) {
            setInterval(() => {
                this.updateDashboardStats();
            }, 30000);
        }
    }

    startPeriodicUpdates() {
        // Actualizar estadísticas cada 30 segundos
        setInterval(() => {
            this.updateDashboardStats();
        }, 30000);

        // Actualizar estado de conexión cada 5 segundos
        setInterval(() => {
            if (this.socket && !this.socket.connected) {
                this.updateConnectionStatus(false);
            }
        }, 5000);
    }

    initializeCharts() {
        // Inicializar gráficos si Chart.js está disponible
        if (typeof Chart !== 'undefined') {
            this.initActivityChart();
            this.initTrendChart();
        }
    }

    initActivityChart() {
        const ctx = document.getElementById('activityChart');
        if (!ctx) return;

        this.charts.activity = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Hallazgos por Hora',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });

        // Cargar datos iniciales
        this.updateActivityChart();
    }

    updateActivityChart() {
        fetch('/api/recent_findings?hours=24')
            .then(response => response.json())
            .then(data => {
                // Procesar datos por hora
                const hourlyData = this.groupByHour(data);
                
                if (this.charts.activity) {
                    this.charts.activity.data.labels = Object.keys(hourlyData);
                    this.charts.activity.data.datasets[0].data = Object.values(hourlyData);
                    this.charts.activity.update();
                }
            })
            .catch(error => console.error('Error actualizando gráfico:', error));
    }

    groupByHour(findings) {
        const hourlyData = {};
        const now = new Date();
        
        // Inicializar últimas 24 horas
        for (let i = 23; i >= 0; i--) {
            const hour = new Date(now.getTime() - i * 60 * 60 * 1000);
            const hourKey = hour.getHours().toString().padStart(2, '0') + ':00';
            hourlyData[hourKey] = 0;
        }

        // Contar hallazgos por hora
        findings.forEach(finding => {
            const date = new Date(finding.discovered_at);
            const hourKey = date.getHours().toString().padStart(2, '0') + ':00';
            if (hourlyData.hasOwnProperty(hourKey)) {
                hourlyData[hourKey]++;
            }
        });

        return hourlyData;
    }

    // Método para cleanup al cerrar la página
    cleanup() {
        if (this.socket) {
            this.socket.disconnect();
        }
        
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
    }
}

// Inicializar aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.webFuzzingApp = new WebFuzzingApp();
});

// Cleanup al cerrar la página
window.addEventListener('beforeunload', () => {
    if (window.webFuzzingApp) {
        window.webFuzzingApp.cleanup();
    }
});

// Utilidades globales
window.WebFuzzingUtils = {
    formatFileSize: (bytes) => {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    },

    formatDate: (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    },

    copyToClipboard: (text) => {
        navigator.clipboard.writeText(text).then(() => {
            if (window.webFuzzingApp) {
                window.webFuzzingApp.showNotification('Copiado al portapapeles', 'success');
            }
        });
    },

    downloadData: (data, filename, type = 'application/json') => {
        const blob = new Blob([data], { type });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
};
