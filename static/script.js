/**
 * Dashboard Auto-Refresh Script
 * Simple JavaScript to update data every seconds
 */

// Update dashboard with latest data
async function updateDashboard() {
    try {
        const response = await fetch('/api/dashboard');
        const result = await response.json();
        
        if (result.status === 'success') {
            displayGroups(result.data);
            document.getElementById('update-time').textContent = new Date().toLocaleTimeString();
            document.getElementById('total-groups').textContent = result.data.length;
        }
    } catch (error) {
        console.error('Error updating dashboard:', error);
    }
}

// Display groups data on the dashboard
function displayGroups(groupsData) {
    const container = document.getElementById('groups-container');
    
    if (groupsData.length === 0) {
        container.innerHTML = '<div class="no-data">No data received yet from any group</div>';
        return;
    }
    
    container.innerHTML = groupsData.map(group => `
        <div class="group-card ${isRecent(group.timestamp) ? 'online' : 'offline'}">
            <div class="group-header">
                <div class="group-name">${group.group_id.toUpperCase()}</div>
                <div class="group-status ${isRecent(group.timestamp) ? 'status-online' : 'status-offline'}">
                    ${isRecent(group.timestamp) ? 'ONLINE' : 'OFFLINE'}
                </div>
            </div>
            
            <div class="sensor-data">
                ${Object.entries(group.sensor_data).map(([key, value]) => `
                    <div class="sensor-item">
                        <span class="sensor-name">${key}:</span>
                        <span class="sensor-value">${formatValue(value)}</span>
                    </div>
                `).join('')}
            </div>
            
            <div class="timestamp">
                Last update: ${new Date(group.timestamp * 1000).toLocaleTimeString()}
            </div>
        </div>
    `).join('');
}

// Check if data is recent (within last 2 minutes)
function isRecent(timestamp) {
    // Get the latest timestamp from all groups as reference
    const latestTs = window.latestTimestamp || timestamp;
    // Update our reference timestamp if this one is more recent
    if (timestamp > window.latestTimestamp || !window.latestTimestamp) {
        window.latestTimestamp = timestamp;
    }
    
    // Compare with the latest known timestamp instead of system time
    const difference = Math.abs(latestTs - timestamp);
    
    // Debug info
    console.log('Timestamp check:', {
        timestamp,
        latestKnown: latestTs,
        difference,
        isRecent: difference < 120
    });
    
    return difference < 120; // Within 2 minutes of the latest reading
}

// Format sensor values for display
function formatValue(value) {
    if (typeof value === 'number') {
        return value.toFixed(2);
    }
    return value;
}

// Auto-refresh every seconds
setInterval(updateDashboard, 1000);

// Load data immediately when page loads
document.addEventListener('DOMContentLoaded', updateDashboard);