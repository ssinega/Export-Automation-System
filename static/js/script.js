/* ─────────────────────────────────────────────────────
   API 3 – EXPORT Automation System
   Minimal JavaScript for interactive elements
   ───────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
    // ── Flash message auto-dismiss ──
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-8px)';
            setTimeout(() => flash.remove(), 300);
        }, 6000);
    });

    // ── File upload area – visual feedback ──
    const uploadArea = document.querySelector('.upload-area');
    if (uploadArea) {
        const fileInput = uploadArea.querySelector('input[type="file"]');

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = 'var(--accent)';
            uploadArea.style.background = 'rgba(108, 99, 255, 0.06)';
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.borderColor = '';
            uploadArea.style.background = '';
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '';
            uploadArea.style.background = '';
            if (e.dataTransfer.files.length > 0 && fileInput) {
                fileInput.files = e.dataTransfer.files;
                _showFileName(fileInput);
            }
        });

        if (fileInput) {
            fileInput.addEventListener('change', () => _showFileName(fileInput));
        }
    }

    // ── Confirm before sending campaign ──
    const sendForm = document.getElementById('campaign-form');
    if (sendForm) {
        sendForm.addEventListener('submit', (e) => {
            const isDryRun = sendForm.dataset.dryrun === 'true';
            const msg = isDryRun
                ? 'Run campaign in DRY RUN mode? No emails will be sent.'
                : '⚠ LIVE MODE – This will send real emails. Continue?';
            if (!confirm(msg)) {
                e.preventDefault();
            }
        });
    }

    // ── Animate stat cards on scroll ──
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.1 }
    );

    document.querySelectorAll('.stat-card').forEach(card => {
        card.style.opacity = '0';
        observer.observe(card);
    });

    // ── Active sidebar link ──
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-nav a').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});


/**
 * Show selected filename in the upload area.
 */
function _showFileName(input) {
    const area = input.closest('.upload-area');
    if (!area) return;
    const label = area.querySelector('.upload-label');
    if (label && input.files.length > 0) {
        label.textContent = input.files[0].name;
        label.style.color = 'var(--accent)';
    }
}
