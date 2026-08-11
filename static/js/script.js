/* ============================================================
   Auction System - UI behaviour & micro-interactions
   ============================================================ */
(function () {
    'use strict';

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* --------------------------------------------------------
       Countdown timers
       Any element with [data-countdown="<iso date>"] is updated
       every second. Adds .is-urgent to a parent .countdown-box
       when under an hour remains.
       -------------------------------------------------------- */
    function parseDate(value) {
        if (!value) return NaN;
        // MySQL style "2026-08-14 12:30:00" needs normalising for Safari/iOS
        const normalised = value.trim().replace(' ', 'T');
        let time = new Date(normalised).getTime();
        if (isNaN(time)) time = new Date(value).getTime();
        return time;
    }

    function initCountdowns() {
        const elements = document.querySelectorAll('[data-countdown]');
        if (!elements.length) return;

        function tick() {
            const now = Date.now();

            elements.forEach(el => {
                const end = parseDate(el.dataset.countdown);
                if (isNaN(end)) { el.textContent = '--'; return; }

                const distance = end - now;
                const box = el.closest('.countdown-box, .timer');

                if (distance <= 0) {
                    el.textContent = 'Auction closed';
                    el.classList.add('text-danger');
                    if (box) box.classList.remove('is-urgent');
                    return;
                }

                const days = Math.floor(distance / 86400000);
                const hours = Math.floor((distance % 86400000) / 3600000);
                const minutes = Math.floor((distance % 3600000) / 60000);
                const seconds = Math.floor((distance % 60000) / 1000);

                el.textContent = days > 0
                    ? `${days}d ${hours}h ${minutes}m ${seconds}s`
                    : `${hours}h ${minutes}m ${seconds}s`;

                // Under one hour = urgent styling
                if (box) box.classList.toggle('is-urgent', distance < 3600000);
            });
        }

        tick();
        setInterval(tick, 1000);
    }

    /* --------------------------------------------------------
       Button ripple + submit loading state
       -------------------------------------------------------- */
    function initButtonEffects() {
        // Show a spinner on submit buttons so slow posts feel responsive
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function () {
                if (form.classList.contains('needs-validation') && !form.checkValidity()) return;
                const submit = form.querySelector('button[type="submit"]');
                if (submit && !submit.classList.contains('is-loading')) {
                    setTimeout(() => submit.classList.add('is-loading'), 60);
                }
            });
        });
    }

    /* --------------------------------------------------------
       Flash message toasts - auto dismiss
       -------------------------------------------------------- */
    function initToasts() {
        document.querySelectorAll('.flash-stack .notice').forEach((notice, i) => {
            notice.style.animationDelay = (i * 80) + 'ms';

            const dismiss = () => {
                notice.classList.add('hiding');
                setTimeout(() => notice.remove(), 340);
            };

            let timer = setTimeout(dismiss, 5000 + i * 400);

            // Hovering holds the notice open
            notice.addEventListener('mouseenter', () => clearTimeout(timer));
            notice.addEventListener('mouseleave', () => { timer = setTimeout(dismiss, 2200); });

            const closeBtn = notice.querySelector('.close');
            if (closeBtn) {
                closeBtn.addEventListener('click', e => {
                    e.preventDefault();
                    clearTimeout(timer);
                    dismiss();
                });
            }
        });
    }

    /* --------------------------------------------------------
       Mobile navigation panel
       -------------------------------------------------------- */
    function initNavToggle() {
        const toggle = document.querySelector('[data-nav-toggle]');
        const panel = document.getElementById('navPanel');
        if (!toggle || !panel) return;

        toggle.addEventListener('click', () => {
            const open = panel.classList.toggle('open');
            toggle.setAttribute('aria-expanded', String(open));
            toggle.innerHTML = open
                ? '<i class="fas fa-xmark"></i>'
                : '<i class="fas fa-bars"></i>';
        });
    }

    /* --------------------------------------------------------
       Sticky navbar state + scroll progress + back to top
       -------------------------------------------------------- */
    function initScrollEffects() {
        const nav = document.querySelector('.app-nav');
        const progress = document.querySelector('.scroll-progress');
        const toTop = document.querySelector('.to-top');
        let ticking = false;

        function onScroll() {
            const y = window.scrollY;

            if (nav) nav.classList.toggle('is-stuck', y > 10);
            if (toTop) toTop.classList.toggle('show', y > 400);

            if (progress) {
                const height = document.documentElement.scrollHeight - window.innerHeight;
                progress.style.width = height > 0 ? ((y / height) * 100) + '%' : '0%';
            }
            ticking = false;
        }

        window.addEventListener('scroll', () => {
            if (!ticking) {
                window.requestAnimationFrame(onScroll);
                ticking = true;
            }
        }, { passive: true });

        onScroll();

        if (toTop) {
            toTop.addEventListener('click', () => {
                window.scrollTo({ top: 0, behavior: prefersReducedMotion ? 'auto' : 'smooth' });
            });
        }
    }

    /* --------------------------------------------------------
       Reveal elements as they scroll into view
       -------------------------------------------------------- */
    function initReveal() {
        const items = document.querySelectorAll('.reveal');
        if (!items.length) return;

        if (prefersReducedMotion || !('IntersectionObserver' in window)) {
            items.forEach(el => el.classList.add('is-visible'));
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (!entry.isIntersecting) return;
                const el = entry.target;
                const delay = parseInt(el.dataset.revealDelay || '0', 10);
                setTimeout(() => el.classList.add('is-visible'), delay);
                observer.unobserve(el);
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

        items.forEach(el => observer.observe(el));
    }

    /* --------------------------------------------------------
       Animated number counters (stat cards / hero)
       -------------------------------------------------------- */
    function initCounters() {
        const counters = document.querySelectorAll('[data-count]');
        if (!counters.length) return;

        function run(el) {
            const target = parseFloat(el.dataset.count) || 0;
            const decimals = parseInt(el.dataset.countDecimals || '0', 10);
            const prefix = el.dataset.countPrefix || '';
            const suffix = el.dataset.countSuffix || '';
            const format = (v) => prefix + v.toLocaleString('en-US', {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            }) + suffix;

            if (prefersReducedMotion) { el.textContent = format(target); return; }

            const duration = 1100;
            const start = performance.now();

            function frame(now) {
                const progress = Math.min((now - start) / duration, 1);
                // easeOutExpo
                const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
                el.textContent = format(target * eased);
                if (progress < 1) requestAnimationFrame(frame);
            }

            requestAnimationFrame(frame);
        }

        if (!('IntersectionObserver' in window)) {
            counters.forEach(run);
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (!entry.isIntersecting) return;
                run(entry.target);
                observer.unobserve(entry.target);
            });
        }, { threshold: 0.4 });

        counters.forEach(el => observer.observe(el));
    }

    /* --------------------------------------------------------
       Image upload preview + dropzone
       -------------------------------------------------------- */
    function initUploads() {
        const input = document.querySelector('input[type="file"][multiple]');
        if (!input) return;

        const zone = input.closest('.dropzone');
        const preview = document.querySelector('#image-preview-container');

        function render(files) {
            if (!preview) return;
            preview.innerHTML = '';
            Array.from(files).forEach(file => {
                if (!file.type.startsWith('image/')) return;
                const reader = new FileReader();
                reader.onload = e => {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.className = 'm-1';
                    img.style.cssText = 'width:84px;height:84px;object-fit:cover;';
                    img.title = file.name;
                    preview.appendChild(img);
                };
                reader.readAsDataURL(file);
            });

            if (zone) {
                const label = zone.querySelector('.hint');
                if (label) {
                    label.textContent = files.length
                        ? `${files.length} image${files.length > 1 ? 's' : ''} selected`
                        : label.dataset.default || label.textContent;
                }
            }
        }

        input.addEventListener('change', e => render(e.target.files));

        if (zone) {
            ['dragenter', 'dragover'].forEach(evt =>
                zone.addEventListener(evt, e => {
                    e.preventDefault();
                    zone.classList.add('is-dragover');
                })
            );

            ['dragleave', 'drop'].forEach(evt =>
                zone.addEventListener(evt, e => {
                    e.preventDefault();
                    zone.classList.remove('is-dragover');
                })
            );

            zone.addEventListener('drop', e => {
                if (e.dataTransfer && e.dataTransfer.files.length) {
                    input.files = e.dataTransfer.files;
                    render(input.files);
                }
            });
        }
    }

    /* --------------------------------------------------------
       Password visibility toggle + strength meter
       -------------------------------------------------------- */
    function initPasswords() {
        document.querySelectorAll('.password-toggle').forEach(toggle => {
            toggle.addEventListener('click', function () {
                const target = document.querySelector(this.dataset.target);
                if (!target) return;
                const show = target.getAttribute('type') === 'password';
                target.setAttribute('type', show ? 'text' : 'password');
                const icon = this.querySelector('i');
                icon.classList.toggle('fa-eye', !show);
                icon.classList.toggle('fa-eye-slash', show);
                this.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
            });
        });

        const meter = document.querySelector('.strength-meter');
        const pwd = document.querySelector('#password');
        if (!meter || !pwd) return;

        pwd.addEventListener('input', function () {
            const v = this.value;
            let score = 0;
            if (v.length >= 8) score++;
            if (/[A-Z]/.test(v) && /[a-z]/.test(v)) score++;
            if (/\d/.test(v)) score++;
            if (/[^A-Za-z0-9]/.test(v) || v.length >= 14) score++;
            meter.className = 'strength-meter' + (v ? ' s' + score : '');
        });
    }

    /* --------------------------------------------------------
       Form validation + confirm-before-delete + tooltips
       -------------------------------------------------------- */
    function initForms() {
        document.querySelectorAll('.needs-validation').forEach(form => {
            form.addEventListener('submit', function (e) {
                if (!this.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                    const invalid = this.querySelector(':invalid');
                    if (invalid) invalid.focus();
                }
                this.classList.add('was-validated');
            });
        });

        // Register page: live confirm-password matching
        const pwd = document.querySelector('#password');
        const confirm = document.querySelector('#confirm_password');
        if (pwd && confirm) {
            const check = () => {
                confirm.setCustomValidity(
                    confirm.value && confirm.value !== pwd.value ? 'Passwords do not match' : ''
                );
                confirm.classList.toggle('is-invalid', !!confirm.value && confirm.value !== pwd.value);
                confirm.classList.toggle('is-valid', !!confirm.value && confirm.value === pwd.value);
            };
            confirm.addEventListener('input', check);
            pwd.addEventListener('input', check);
        }

        document.querySelectorAll('.delete-confirm').forEach(button => {
            button.addEventListener('click', function (e) {
                if (!confirm('Are you sure you want to delete this item?')) e.preventDefault();
            });
        });

        if (window.bootstrap) {
            document.querySelectorAll('[data-bs-toggle="tooltip"]')
                .forEach(el => new bootstrap.Tooltip(el));
        }
    }

    /* --------------------------------------------------------
       Bid form helpers: quick-bid buttons + heart pop
       -------------------------------------------------------- */
    function initBidding() {
        const bidInput = document.querySelector('.bid-form input[name="bid_amount"]');

        document.querySelectorAll('[data-quick-bid]').forEach(btn => {
            btn.addEventListener('click', function () {
                if (!bidInput) return;
                bidInput.value = parseFloat(this.dataset.quickBid).toFixed(2);
                bidInput.focus();
                bidInput.classList.add('is-valid');
                setTimeout(() => bidInput.classList.remove('is-valid'), 1200);
            });
        });

        // Lock the bid form after submitting so a double click cannot
        // replay the same bid while the first request is in flight
        document.querySelectorAll('[data-bid-form]').forEach(form => {
            form.addEventListener('submit', function () {
                const submit = form.querySelector('button[type="submit"]');
                if (!submit) return;
                submit.disabled = true;
                submit.textContent = 'Placing bid…';
            });
        });

        document.querySelectorAll('.watch-form button').forEach(btn => {
            btn.addEventListener('click', function () {
                const icon = this.querySelector('.fa-heart');
                if (icon) {
                    icon.classList.add('heart-pop');
                    setTimeout(() => icon.classList.remove('heart-pop'), 450);
                }
            });
        });
    }

    /* --------------------------------------------------------
       Dashboard area charts
       Any <canvas data-area-chart> with data-labels / data-values.
       -------------------------------------------------------- */
    function initAreaCharts() {
        const canvases = document.querySelectorAll('canvas[data-area-chart]');
        if (!canvases.length || typeof Chart === 'undefined') return;

        const brand = '#10794f';
        const brandLine = '#23a06c';

        canvases.forEach(canvas => {
            let labels = [];
            let values = [];
            try {
                labels = JSON.parse(canvas.dataset.labels || '[]');
                values = JSON.parse(canvas.dataset.values || '[]');
            } catch (e) {
                return;
            }

            const decimals = parseInt(canvas.dataset.decimals || '0', 10);
            const prefix = canvas.dataset.prefix || '';
            const format = v => prefix + Number(v).toLocaleString('en-US', {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            });

            const ctx = canvas.getContext('2d');
            const fill = ctx.createLinearGradient(0, 0, 0, canvas.parentElement.clientHeight || 220);
            fill.addColorStop(0, 'rgba(35, 160, 108, .35)');
            fill.addColorStop(1, 'rgba(35, 160, 108, 0)');

            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: canvas.dataset.label || 'Activity',
                        data: values,
                        borderColor: brand,
                        borderWidth: 2,
                        backgroundColor: fill,
                        fill: true,
                        tension: .38,
                        pointRadius: 0,
                        pointHoverRadius: 5,
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: brandLine,
                        pointHoverBorderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: prefersReducedMotion ? false : { duration: 800 },
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#0f1418',
                            padding: 10,
                            cornerRadius: 10,
                            displayColors: false,
                            titleFont: { family: 'Inter', size: 12 },
                            bodyFont: { family: 'Inter', size: 13, weight: '600' },
                            callbacks: { label: c => format(c.parsed.y) }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            border: { display: false },
                            ticks: {
                                color: '#8b95a3',
                                font: { family: 'Inter', size: 11 },
                                maxRotation: 0,
                                autoSkipPadding: 12
                            }
                        },
                        y: {
                            beginAtZero: true,
                            grid: { color: '#e6e9ee', drawTicks: false },
                            border: { display: false },
                            ticks: {
                                color: '#8b95a3',
                                font: { family: 'Inter', size: 11 },
                                padding: 8,
                                maxTicksLimit: 5,
                                callback: v => format(v)
                            }
                        }
                    }
                }
            });
        });
    }

    /* --------------------------------------------------------
       Mark the active nav link based on current path
       -------------------------------------------------------- */
    function initActiveNav() {
        const here = window.location.pathname + window.location.search;
        const path = window.location.pathname;
        const links = Array.from(document.querySelectorAll('.nav-links a[href]'));

        // Prefer an exact path+query match (distinguishes /search from /search?status=closed)
        const exact = links.find(l => l.getAttribute('href') === here);
        if (exact) { exact.classList.add('active'); return; }

        // Otherwise fall back to the query-less link for this path
        const byPath = links.find(l => l.getAttribute('href') === path);
        if (byPath) byPath.classList.add('active');
    }

    /* --------------------------------------------------------
       Boot
       -------------------------------------------------------- */
    document.addEventListener('DOMContentLoaded', function () {
        // Reveal first, and independently, so a later failure can never leave
        // the page blank (and therefore apparently unscrollable).
        try { initReveal(); } catch (e) {
            document.querySelectorAll('.reveal').forEach(el => el.classList.add('is-visible'));
            console.error(e);
        }

        [initCountdowns, initButtonEffects, initToasts, initNavToggle, initScrollEffects,
         initCounters, initUploads, initPasswords, initForms, initBidding,
         initAreaCharts, initActiveNav].forEach(fn => {
            try { fn(); } catch (e) { console.error(e); }
        });
    });

    // Exposed helper
    window.formatCurrency = function (amount) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
    };
})();
