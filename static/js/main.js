document.addEventListener("DOMContentLoaded", function() {
    const alertsList = document.getElementById('alerts-list');
    const alertSound = document.getElementById('alert-sound');
    let lastAlertCount = 0;

    async function fetchAlerts() {
        try {
            const response = await fetch('/get_alerts');
            const alerts = await response.json();

            if (alerts.length > 0 && alerts.length !== lastAlertCount) {
                updateAlertsList(alerts);
                
                // Play sound only if new alerts have been added
                if (alerts.length > lastAlertCount) {
                    alertSound.play().catch(error => {
                        console.log("Audio play was prevented by browser:", error);
                    });
                }
                lastAlertCount = alerts.length;
            } else if (alerts.length === 0 && lastAlertCount > 0) {
                // Reset if all alerts are cleared
                alertsList.innerHTML = '<li>No threats detected yet.</li>';
                lastAlertCount = 0;
            }

        } catch (error) {
            console.error('Error fetching alerts:', error);
        }
    }

    function updateAlertsList(alerts) {
        alertsList.innerHTML = ''; // Clear current list
        // Reverse to show latest alert on top
        alerts.slice().reverse().forEach(alert => {
            const listItem = document.createElement('li');
            listItem.innerHTML = `${alert.message} <span class="timestamp">${alert.timestamp}</span>`;
            alertsList.appendChild(listItem);
        });
    }

    // Fetch alerts every 2 seconds
    setInterval(fetchAlerts, 2000);
});