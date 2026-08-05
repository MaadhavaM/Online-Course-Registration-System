// Auto-dismiss Flash Alerts after 4 seconds
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            // Using Bootstrap's alert instance to close it smoothly
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 4000); // 4000 milliseconds = 4 seconds
});
