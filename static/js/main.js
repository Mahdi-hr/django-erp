(function() {
    'use strict';
    document.addEventListener('DOMContentLoaded', function() {
        initSidebar();
        initTableSort();
        initSearch();
        initAlerts();
        initConfirms();
        initSmsPreview();
    });

    function initSidebar() {
        var btn = document.getElementById('sidebarToggle');
        var sidebar = document.getElementById('sidebar');
        var overlay = document.getElementById('sidebarOverlay');
        if (btn && sidebar) {
            btn.addEventListener('click', function() {
                sidebar.classList.toggle('active');
                if (overlay) overlay.classList.toggle('active');
            });
        }
        if (overlay) {
            overlay.addEventListener('click', function() {
                sidebar.classList.remove('active');
                overlay.classList.remove('active');
            });
        }
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && sidebar && sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
                if (overlay) overlay.classList.remove('active');
            }
        });
    }

    function initTableSort() {
        document.querySelectorAll('table.sortable thead th').forEach(function(th, idx) {
            th.style.cursor = 'pointer';
            th.addEventListener('click', function() { sortTable(th.closest('table'), idx); });
            if (!th.querySelector('.sort-icon')) {
                var i = document.createElement('i');
                i.className = 'fas fa-sort sort-icon ms-1';
                th.appendChild(i);
            }
        });
    }

    function sortTable(table, col) {
        var tbody = table.querySelector('tbody');
        if (!tbody) return;
        var rows = Array.from(tbody.querySelectorAll('tr'));
        var th = table.querySelectorAll('thead th')[col];
        var dir = th.classList.contains('sorted-asc') ? 'desc' : 'asc';
        table.querySelectorAll('thead th').forEach(function(h) {
            h.classList.remove('sorted', 'sorted-asc', 'sorted-desc');
            var ic = h.querySelector('.sort-icon');
            if (ic) { ic.className = 'fas fa-sort sort-icon ms-1'; ic.style.opacity = '0.3'; }
        });
        th.classList.add('sorted', 'sorted-' + dir);
        var icon = th.querySelector('.sort-icon');
        if (icon) { icon.className = 'fas fa-sort-' + (dir === 'asc' ? 'up' : 'down') + ' sort-icon ms-1'; icon.style.opacity = '1'; icon.style.color = 'var(--accent)'; }
        rows.sort(function(a, b) {
            var av = a.cells[col] ? a.cells[col].textContent.trim() : '';
            var bv = b.cells[col] ? b.cells[col].textContent.trim() : '';
            var an = parseFloat(av.replace(/[^\d.-]/g, ''));
            var bn = parseFloat(bv.replace(/[^\d.-]/g, ''));
            if (!isNaN(an) && !isNaN(bn)) return dir === 'asc' ? an - bn : bn - an;
            return dir === 'asc' ? av.localeCompare(bv, 'fa') : bv.localeCompare(av, 'fa');
        });
        rows.forEach(function(r) { tbody.appendChild(r); });
    }

    function initSearch() {
        document.querySelectorAll('.table-search-input').forEach(function(input) {
            var table = document.getElementById(input.dataset.table);
            if (!table) return;
            input.addEventListener('input', function() {
                var term = this.value.trim().toLowerCase();
                table.querySelectorAll('tbody tr').forEach(function(row) {
                    row.style.display = row.textContent.toLowerCase().includes(term) ? '' : 'none';
                });
            });
        });
    }

    function initAlerts() {
        document.querySelectorAll('.alert-dismissible').forEach(function(alert) {
            setTimeout(function() {
                alert.classList.remove('show');
                setTimeout(function() { if (alert.parentNode) alert.remove(); }, 300);
            }, 5000);
        });
    }

    function initConfirms() {
        document.querySelectorAll('[data-confirm]').forEach(function(el) {
            el.addEventListener('click', function(e) {
                if (!confirm(this.dataset.confirm || 'آیا از انجام این عملیات اطمینان دارید؟')) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            });
        });
    }

    function initSmsPreview() {
        var ta = document.querySelector('#id_message, #id_body, textarea[name="message"]');
        var pv = document.getElementById('smsPreview');
        if (ta && pv) {
            ta.addEventListener('input', function() {
                pv.textContent = this.value || 'پیش‌نمایش پیامک...';
            });
        }
    }
})();
