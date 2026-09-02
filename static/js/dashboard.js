/* ============================================
   Karpay Dashboard - Charts & Interactions
   ============================================ */

(function() {
    'use strict';

    // ==========================================
    // Daily Chart
    // ==========================================
    function initDailyChart() {
        const canvas = document.getElementById('dailyChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const data = window.dailyChartData || { labels: [], amounts: [], counts: [] };

        // Format labels
        const labels = data.labels.map(d => {
            if (typeof d === 'string' && d.includes('-')) {
                const date = new Date(d);
                return date.toLocaleDateString('ar-SA', { weekday: 'short', day: 'numeric' });
            }
            return d;
        });

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'المبالغ',
                        data: data.amounts || [],
                        backgroundColor: '#228C5B',
                        borderRadius: 6,
                        borderSkipped: false,
                        barPercentage: 0.6,
                        categoryPercentage: 0.7,
                        yAxisID: 'y',
                    },
                    {
                        label: 'العمليات',
                        data: data.counts || [],
                        backgroundColor: '#FCD761',
                        borderRadius: 6,
                        borderSkipped: false,
                        barPercentage: 0.6,
                        categoryPercentage: 0.7,
                        yAxisID: 'y1',
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
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
                        rtl: true,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) label += ': ';
                                if (context.dataset.yAxisID === 'y') {
                                    label += context.parsed.y.toLocaleString('ar-SA') + ' ر.ي';
                                } else {
                                    label += context.parsed.y.toLocaleString('ar-SA') + ' عملية';
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: { family: 'Tajawal', size: 11 },
                            color: '#94a3b8'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            color: '#f1f5f9',
                            drawBorder: false
                        },
                        ticks: {
                            font: { family: 'Tajawal', size: 10 },
                            color: '#94a3b8',
                            callback: function(value) {
                                return value >= 1000 ? (value/1000) + 'k' : value;
                            }
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: { family: 'Tajawal', size: 10 },
                            color: '#94a3b8'
                        }
                    }
                }
            }
        });
    }

    // ==========================================
    // Auto-init on DOM ready
    // ==========================================
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDailyChart);
    } else {
        initDailyChart();
    }

    // Expose for manual re-init
    window.Dashboard = {
        charts: {
            initDaily: initDailyChart
        }
    };
})();