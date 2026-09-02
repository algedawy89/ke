/**
 * Karpay Dashboard - Main JavaScript
 * Responsive, Non-scalable, Dynamic Layout
 */

(function() {
    'use strict';

    // ============================================
    // SIDEBAR MANAGEMENT
    // ============================================

    const Sidebar = {
        element: null,
        overlay: null,
        toggleBtn: null,
        isOpen: false,

        init() {
            this.element = document.getElementById('sidebar');
            this.overlay = document.getElementById('sidebarOverlay');
            this.toggleBtn = document.getElementById('sidebarToggle');

            if (!this.element) return;

            // Bind events
            if (this.toggleBtn) {
                this.toggleBtn.addEventListener('click', () => this.toggle());
            }

            if (this.overlay) {
                this.overlay.addEventListener('click', () => this.close());
            }

            // Close on Escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isOpen) {
                    this.close();
                }
            });

            // Close when clicking outside on mobile
            document.addEventListener('click', (e) => {
                if (window.innerWidth < 1024) {
                    if (this.isOpen && 
                        !this.element.contains(e.target) && 
                        !this.toggleBtn.contains(e.target)) {
                        this.close();
                    }
                }
            });

            // Handle resize
            window.addEventListener('resize', () => this.handleResize());

            // Initial state
            this.handleResize();
        },

        toggle() {
            if (this.isOpen) {
                this.close();
            } else {
                this.open();
            }
        },

        open() {
            this.element.classList.add('open');
            if (this.overlay) this.overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
            this.isOpen = true;
        },

        close() {
            this.element.classList.remove('open');
            if (this.overlay) this.overlay.classList.remove('active');
            document.body.style.overflow = '';
            this.isOpen = false;
        },

        handleResize() {
            if (window.innerWidth >= 1024) {
                // Desktop: sidebar always visible
                this.element.classList.remove('open');
                if (this.overlay) this.overlay.classList.remove('active');
                document.body.style.overflow = '';
                this.isOpen = false;
            } else {
                // Mobile: ensure sidebar is closed by default
                if (!this.isOpen) {
                    this.element.classList.remove('open');
                    if (this.overlay) this.overlay.classList.remove('active');
                }
            }
        }
    };

    // ============================================
    // ALERTS AUTO-DISMISS
    // ============================================

    const Alerts = {
        init() {
            const alerts = document.querySelectorAll('.alert');
            alerts.forEach(alert => {
                // Auto dismiss after 5 seconds
                setTimeout(() => {
                    this.dismiss(alert);
                }, 5000);

                // Manual close
                const closeBtn = alert.querySelector('.alert-close');
                if (closeBtn) {
                    closeBtn.addEventListener('click', () => this.dismiss(alert));
                }
            });
        },

        dismiss(alert) {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(20px)';
            setTimeout(() => alert.remove(), 300);
        }
    };

    // ============================================
    // CHARTS
    // ============================================

    const Charts = {
        instances: {},

        init() {
            this.initDailyChart();
        },

        initDailyChart() {
            const canvas = document.getElementById('dailyChart');
            if (!canvas || typeof Chart === 'undefined') return;

            // Check if data is available from Django template
            const chartData = window.dailyChartData;

            if (chartData) {
                this.renderDailyChart(canvas, chartData);
            } else {
                // Try to fetch from API
                this.fetchDailyChart(canvas);
            }
        },

        renderDailyChart(canvas, data) {
            const ctx = canvas.getContext('2d');

            this.instances.dailyChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: 'المبالغ',
                        data: data.amounts || [],
                        backgroundColor: '#228C5B',
                        borderRadius: 6,
                        borderSkipped: false,
                        yAxisID: 'y',
                        barPercentage: 0.6,
                        categoryPercentage: 0.8
                    }, {
                        label: 'العمليات',
                        data: data.counts || [],
                        backgroundColor: '#FCD761',
                        borderRadius: 6,
                        borderSkipped: false,
                        yAxisID: 'y1',
                        barPercentage: 0.6,
                        categoryPercentage: 0.8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: '#0f172a',
                            titleFont: { family: 'Tajawal', size: 13 },
                            bodyFont: { family: 'Tajawal', size: 12 },
                            padding: 12,
                            cornerRadius: 8,
                            displayColors: true,
                            rtl: true,
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) label += ': ';
                                    if (context.dataset.yAxisID === 'y') {
                                        label += context.parsed.y.toLocaleString('ar-SA') + ' ر.ي';
                                    } else {
                                        label += context.parsed.y;
                                    }
                                    return label;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: {
                                font: { family: 'Tajawal', size: 11 },
                                color: '#94a3b8'
                            }
                        },
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            grid: { display: false },
                            ticks: {
                                font: { family: 'Tajawal', size: 11 },
                                color: '#94a3b8',
                                callback: function(value) {
                                    return value.toLocaleString('ar-SA') + ' ر.ي';
                                }
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            grid: {
                                color: '#f1f5f9',
                                drawBorder: false
                            },
                            ticks: {
                                font: { family: 'Tajawal', size: 11 },
                                color: '#94a3b8',
                                stepSize: 1,
                                precision: 0
                            }
                        }
                    }
                }
            });
        },

        async fetchDailyChart(canvas) {
            try {
                const response = await fetch('/dashboard/api/chart-data/?type=daily');
                if (!response.ok) throw new Error('Failed to fetch chart data');
                const data = await response.json();

                // Format labels
                if (data.labels) {
                    data.labels = data.labels.map(d => {
                        const date = new Date(d);
                        return date.toLocaleDateString('ar-SA', { 
                            weekday: 'short', 
                            day: 'numeric' 
                        });
                    });
                }

                this.renderDailyChart(canvas, data);
            } catch (error) {
                console.warn('Chart data fetch failed:', error);
                // Render with empty data
                this.renderDailyChart(canvas, { labels: [], amounts: [], counts: [] });
            }
        },

        destroy() {
            Object.values(this.instances).forEach(chart => chart.destroy());
            this.instances = {};
        }
    };

    // ============================================
    // MODAL
    // ============================================

    const Modal = {
        init() {
            document.querySelectorAll('[data-modal]').forEach(trigger => {
                trigger.addEventListener('click', (e) => {
                    e.preventDefault();
                    const modalId = trigger.getAttribute('data-modal');
                    this.open(modalId);
                });
            });

            document.querySelectorAll('.modal-overlay').forEach(overlay => {
                overlay.addEventListener('click', (e) => {
                    if (e.target === overlay) {
                        this.close(overlay.id);
                    }
                });
            });

            document.querySelectorAll('.modal-close').forEach(btn => {
                btn.addEventListener('click', () => {
                    const modal = btn.closest('.modal-overlay');
                    if (modal) this.close(modal.id);
                });
            });
        },

        open(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        },

        close(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }
        }
    };

    // ============================================
    // TOOLTIPS
    // ============================================

    const Tooltip = {
        init() {
            document.querySelectorAll('[data-tooltip]').forEach(el => {
                el.addEventListener('mouseenter', (e) => this.show(e, el));
                el.addEventListener('mouseleave', () => this.hide());
            });
        },

        show(e, el) {
            const text = el.getAttribute('data-tooltip');
            if (!text) return;

            let tooltip = document.getElementById('global-tooltip');
            if (!tooltip) {
                tooltip = document.createElement('div');
                tooltip.id = 'global-tooltip';
                tooltip.style.cssText = `
                    position: fixed;
                    background: #0f172a;
                    color: white;
                    padding: 6px 12px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                    z-index: 9999;
                    pointer-events: none;
                    white-space: nowrap;
                    opacity: 0;
                    transition: opacity 0.2s;
                    font-family: 'Tajawal', sans-serif;
                `;
                document.body.appendChild(tooltip);
            }

            tooltip.textContent = text;
            tooltip.style.opacity = '1';

            const rect = el.getBoundingClientRect();
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 8) + 'px';
            tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
        },

        hide() {
            const tooltip = document.getElementById('global-tooltip');
            if (tooltip) tooltip.style.opacity = '0';
        }
    };

    // ============================================
    // DROPDOWN
    // ============================================

    const Dropdown = {
        init() {
            document.querySelectorAll('[data-dropdown]').forEach(trigger => {
                trigger.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const dropdownId = trigger.getAttribute('data-dropdown');
                    const dropdown = document.getElementById(dropdownId);
                    if (dropdown) {
                        dropdown.classList.toggle('active');
                    }
                });
            });

            document.addEventListener('click', () => {
                document.querySelectorAll('.dropdown-menu.active').forEach(d => {
                    d.classList.remove('active');
                });
            });
        }
    };

    // ============================================
    // LAZY LOADING IMAGES
    // ============================================

    const LazyLoad = {
        init() {
            if ('IntersectionObserver' in window) {
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                            observer.unobserve(img);
                        }
                    });
                });

                document.querySelectorAll('img[data-src]').forEach(img => {
                    observer.observe(img);
                });
            } else {
                // Fallback
                document.querySelectorAll('img[data-src]').forEach(img => {
                    img.src = img.dataset.src;
                });
            }
        }
    };

    // ============================================
    // SMOOTH SCROLL
    // ============================================

    const SmoothScroll = {
        init() {
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', (e) => {
                    const target = document.querySelector(anchor.getAttribute('href'));
                    if (target) {
                        e.preventDefault();
                        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                });
            });
        }
    };

    // ============================================
    // FORM VALIDATION
    // ============================================

    const FormValidation = {
        init() {
            document.querySelectorAll('form[data-validate]').forEach(form => {
                form.addEventListener('submit', (e) => this.validate(e, form));
            });
        },

        validate(e, form) {
            let isValid = true;

            form.querySelectorAll('[required]').forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    this.showError(field, 'هذا الحقل مطلوب');
                } else {
                    this.clearError(field);
                }
            });

            if (!isValid) {
                e.preventDefault();
            }
        },

        showError(field, message) {
            field.style.borderColor = '#ef4444';

            let errorEl = field.parentElement.querySelector('.field-error');
            if (!errorEl) {
                errorEl = document.createElement('span');
                errorEl.className = 'field-error';
                errorEl.style.cssText = `
                    color: #ef4444;
                    font-size: 12px;
                    margin-top: 4px;
                    display: block;
                    font-weight: 600;
                `;
                field.parentElement.appendChild(errorEl);
            }
            errorEl.textContent = message;
        },

        clearError(field) {
            field.style.borderColor = '';
            const errorEl = field.parentElement.querySelector('.field-error');
            if (errorEl) errorEl.remove();
        }
    };

    // ============================================
    // CONFIRM DIALOG
    // ============================================

    const ConfirmDialog = {
        init() {
            document.querySelectorAll('[data-confirm]').forEach(el => {
                el.addEventListener('click', (e) => {
                    const message = el.getAttribute('data-confirm');
                    if (!confirm(message)) {
                        e.preventDefault();
                    }
                });
            });
        }
    };

    // ============================================
    // ACTIVE NAV LINK
    // ============================================

    const ActiveNav = {
        init() {
            const currentPath = window.location.pathname;
            document.querySelectorAll('.nav-link').forEach(link => {
                const href = link.getAttribute('href');
                if (href && currentPath.includes(href) && href !== '/') {
                    link.classList.add('active');
                }
            });
        }
    };

    // ============================================
    // SCROLL TO TOP
    // ============================================

    const ScrollTop = {
        init() {
            const btn = document.getElementById('scrollTopBtn');
            if (!btn) return;

            window.addEventListener('scroll', () => {
                if (window.scrollY > 300) {
                    btn.classList.add('visible');
                } else {
                    btn.classList.remove('visible');
                }
            });

            btn.addEventListener('click', () => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }
    };

    // ============================================
    // TABLE SORTING
    // ============================================

    const TableSort = {
        init() {
            document.querySelectorAll('th[data-sort]').forEach(th => {
                th.style.cursor = 'pointer';
                th.addEventListener('click', () => this.sort(th));
            });
        },

        sort(th) {
            const table = th.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const index = Array.from(th.parentElement.children).indexOf(th);
            const type = th.getAttribute('data-sort');

            const isAsc = !th.classList.contains('sort-asc');

            // Reset other headers
            table.querySelectorAll('th').forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
            });

            th.classList.add(isAsc ? 'sort-asc' : 'sort-desc');

            rows.sort((a, b) => {
                let aVal = a.children[index].textContent.trim();
                let bVal = b.children[index].textContent.trim();

                if (type === 'number') {
                    aVal = parseFloat(aVal.replace(/[^0-9.-]/g, '')) || 0;
                    bVal = parseFloat(bVal.replace(/[^0-9.-]/g, '')) || 0;
                }

                if (aVal < bVal) return isAsc ? -1 : 1;
                if (aVal > bVal) return isAsc ? 1 : -1;
                return 0;
            });

            rows.forEach(row => tbody.appendChild(row));
        }
    };

    // ============================================
    // NOTIFICATIONS
    // ============================================

    const Notifications = {
        container: null,

        init() {
            this.container = document.getElementById('notification-container');
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.id = 'notification-container';
                this.container.style.cssText = `
                    position: fixed;
                    top: 80px;
                    left: 24px;
                    z-index: 9999;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    max-width: 400px;
                `;
                document.body.appendChild(this.container);
            }
        },

        show(message, type = 'info', duration = 5000) {
            const el = document.createElement('div');
            const icons = {
                success: 'fa-check-circle',
                error: 'fa-exclamation-circle',
                warning: 'fa-exclamation-triangle',
                info: 'fa-info-circle'
            };
            const colors = {
                success: '#166534',
                error: '#991b1b',
                warning: '#92400e',
                info: '#1e40af'
            };
            const bgColors = {
                success: '#f0fdf4',
                error: '#fef2f2',
                warning: '#fffbeb',
                info: '#eff6ff'
            };

            el.style.cssText = `
                background: ${bgColors[type]};
                color: ${colors[type]};
                padding: 14px 18px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 10px;
                box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
                animation: slideInLeft 0.4s ease-out;
                border: 1px solid ${colors[type]}20;
                font-family: 'Tajawal', sans-serif;
            `;

            el.innerHTML = `
                <i class="fas ${icons[type]}"></i>
                <span>${message}</span>
                <button style="margin-right:auto;background:none;border:none;color:inherit;cursor:pointer;font-size:12px;opacity:0.6;" onclick="this.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            `;

            this.container.appendChild(el);

            setTimeout(() => {
                el.style.opacity = '0';
                el.style.transform = 'translateX(-20px)';
                setTimeout(() => el.remove(), 300);
            }, duration);
        }
    };

    // ============================================
    // LOADING STATE
    // ============================================

    const Loading = {
        show(message = 'جاري التحميل...') {
            let overlay = document.getElementById('loading-overlay');
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.id = 'loading-overlay';
                overlay.style.cssText = `
                    position: fixed;
                    inset: 0;
                    background: rgba(255,255,255,0.9);
                    z-index: 9999;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    gap: 16px;
                    backdrop-filter: blur(4px);
                `;
                overlay.innerHTML = `
                    <div style="
                        width: 48px;
                        height: 48px;
                        border: 3px solid #e2e8f0;
                        border-top-color: #228C5B;
                        border-radius: 50%;
                        animation: spin 0.8s linear infinite;
                    "></div>
                    <span style="font-family:'Tajawal',sans-serif;font-size:14px;font-weight:700;color:#475569;">${message}</span>
                `;
                document.body.appendChild(overlay);
            }
            overlay.style.display = 'flex';
        },

        hide() {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) overlay.style.display = 'none';
        }
    };

    // ============================================
    // ANIMATIONS CSS INJECTION
    // ============================================

    const injectAnimations = () => {
        if (document.getElementById('dashboard-animations')) return;

        const style = document.createElement('style');
        style.id = 'dashboard-animations';
        style.textContent = `
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            @keyframes slideInLeft {
                from { opacity: 0; transform: translateX(-20px); }
                to { opacity: 1; transform: translateX(0); }
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .animate-fade-in {
                animation: fadeIn 0.5s ease-out;
            }
            .animate-fade-in-up {
                animation: fadeInUp 0.5s ease-out;
            }
            .animate-pulse {
                animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
            }
        `;
        document.head.appendChild(style);
    };

    // ============================================
    // INIT
    // ============================================

    document.addEventListener('DOMContentLoaded', () => {
        injectAnimations();
        Sidebar.init();
        Alerts.init();
        Charts.init();
        Modal.init();
        Tooltip.init();
        Dropdown.init();
        LazyLoad.init();
        SmoothScroll.init();
        FormValidation.init();
        ConfirmDialog.init();
        ActiveNav.init();
        ScrollTop.init();
        TableSort.init();
        Notifications.init();

        // Expose global utilities
        window.Dashboard = {
            notify: (msg, type, duration) => Notifications.show(msg, type, duration),
            loading: { show: () => Loading.show(), hide: () => Loading.hide() },
            modal: { open: (id) => Modal.open(id), close: (id) => Modal.close(id) },
            sidebar: { toggle: () => Sidebar.toggle(), open: () => Sidebar.open(), close: () => Sidebar.close() }
        };
    });

})();
