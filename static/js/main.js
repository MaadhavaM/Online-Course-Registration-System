// Auto-dismiss Flash Alerts after 2 minutes (120 seconds)
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            // Using Bootstrap's alert instance to close it smoothly
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 120000); // 120000 milliseconds = 2 minutes
});
