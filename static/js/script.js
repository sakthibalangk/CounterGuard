// ============================================================
// CounterGuard — global client-side script
// Feature-specific scripts (barcode scanning, charts) will be
// added inline or as separate files in their respective modules.
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    // Auto-dismiss alerts after 5 seconds
    document.querySelectorAll(".alert").forEach((alert) => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });
});
