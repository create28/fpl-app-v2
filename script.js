// Environment detection and API configuration
const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
const API_BASE_URL = isProduction 
    ? 'https://fpl-app-v2-sigma.onrender.com'  // Production (Render) - update this to your actual URL
    : 'http://localhost:8000';                  // Local development

console.log(`Environment: ${isProduction ? 'Production' : 'Local Development'}`);
console.log(`API Base URL: ${API_BASE_URL}`);

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize gameweek data
    initializeGameweekData();

    // Add event listener for gameweek selector
    const gameweekSelect = document.getElementById('gameweekSelect');
    if (gameweekSelect) {
        gameweekSelect.addEventListener('change', function(e) {
            const gameweek = e.target.value;
            if (gameweek) {
                loadGameweekData(gameweek);
            }
        });
    }

    // Screenshot button event
    const screenshotBtn = document.getElementById('screenshotBtn');
    if (screenshotBtn) {
        screenshotBtn.addEventListener('click', captureScreenshot);
    }

    // Manual refresh functionality
    const refreshBtn = document.getElementById('refreshDataBtn');
    const refreshStatus = document.getElementById('refreshStatus');
    
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async function() {
            // Disable button and show loading state
            refreshBtn.disabled = true;
            refreshStatus.textContent = 'Refreshing data...';
            refreshStatus.className = 'ml-4 text-center py-2 px-4 rounded-lg bg-blue-100 text-blue-800';
            
            try {
                const response = await fetch(`${API_BASE_URL}/api/refresh-data`);
                const result = await response.json();
                
                if (result.status === 'success') {
                    refreshStatus.textContent = result.message;
                    refreshStatus.className = 'ml-4 text-center py-2 px-4 rounded-lg bg-green-100 text-green-800';
                    
                    // Wait a moment then refresh the page to show updated data
                    setTimeout(() => {
                        location.reload();
                    }, 2000);
                } else {
                    refreshStatus.textContent = result.message;
                    refreshStatus.className = 'ml-4 text-center py-2 px-4 rounded-lg bg-red-100 text-red-800';
                }
            } catch (error) {
                refreshStatus.textContent = 'Error: Failed to refresh data';
                refreshStatus.className = 'ml-4 text-center py-2 px-4 rounded-lg bg-red-100 text-red-800';
                console.error('Refresh error:', error);
            } finally {
                // Re-enable button after a delay
                setTimeout(() => {
                    refreshBtn.disabled = false;
                }, 3000);
            }
        });
    }

    // Manual player data fetch functionality
    const fetchPlayersBtn = document.getElementById('fetchPlayersBtn');
    const fetchStatus = document.getElementById('fetchStatus');
    
    if (fetchPlayersBtn) {
        fetchPlayersBtn.addEventListener('click', async function() {
            // Get current gameweek
            const gameweekSelect = document.getElementById('gameweekSelect');
            const currentGameweek = gameweekSelect.value;
            
            if (!currentGameweek) {
                fetchStatus.textContent = 'Please select a gameweek first';
                fetchStatus.className = 'text-center py-2 px-4 rounded-lg bg-yellow-100 text-yellow-800';
                return;
            }
            
            // Disable button and show loading state
            fetchPlayersBtn.disabled = true;
            fetchStatus.textContent = 'Fetching player data... This may take a few minutes.';
            fetchStatus.className = 'text-center py-2 px-4 rounded-lg bg-blue-100 text-blue-800';
            
            try {
                const response = await fetch(`${API_BASE_URL}/api/fetch-players/${currentGameweek}`);
                const result = await response.json();
                
                if (result.status === 'success') {
                    fetchStatus.textContent = result.message;
                    fetchStatus.className = 'text-center py-2 px-4 rounded-lg bg-green-100 text-green-800';
                    
                    // Reload the current gameweek data to show new awards
                    setTimeout(() => {
                        loadGameweekData(currentGameweek);
                    }, 2000);
                } else {
                    fetchStatus.textContent = result.message;
                    fetchStatus.className = 'text-center py-2 px-4 rounded-lg bg-red-100 text-red-800';
                }
            } catch (error) {
                fetchStatus.textContent = 'Error: Failed to fetch player data';
                fetchStatus.className = 'text-center py-2 px-4 rounded-lg bg-red-100 text-red-800';
                console.error('Fetch error:', error);
            } finally {
                // Re-enable button after a delay
                setTimeout(() => {
                    fetchPlayersBtn.disabled = false;
                }, 5000);
            }
        });
    }
});

// Initialize gameweek data
function initializeGameweekData() {
    // Get current gameweek
                fetch(`${API_BASE_URL}/api/current-gameweek`)
        .then(response => response.json())
        .then(data => {
            const currentGW = data.current_gameweek;
            
            // Populate gameweek selector
            const select = document.getElementById('gameweekSelect');
            if (select) {
                // Get available gameweeks
                fetch(`${API_BASE_URL}/api/gameweeks`)
                    .then(response => response.json())
                    .then(data => {
                        const gameweeks = data.gameweeks; // Extract the gameweeks array from the response
                        select.innerHTML = '<option value="">Select Gameweek</option>';
                        gameweeks.forEach(gw => {
                            const option = document.createElement('option');
                            option.value = gw;
                            option.textContent = `Gameweek ${gw}`;
                            if (gw === currentGW) {
                                option.selected = true;
                                // Load data for current gameweek
                                loadGameweekData(gw);
                            }
                            select.appendChild(option);
                        });
                    })
                    .catch(error => console.error('Error loading gameweeks:', error));
            }
        })
        .catch(error => console.error('Error loading current gameweek:', error));
}

// Load gameweek data
function loadGameweekData(gameweek) {
    console.log('Loading data for gameweek:', gameweek);
    fetch(`${API_BASE_URL}/api/data/${gameweek}`)
        .then(response => response.json())
        .then(data => {
            console.log('Received data:', data);
            if (data) {
                updateTable(data.standings);
                updateAwards(data.awards);
            }
        })
        .catch(error => {
            console.error('Error loading gameweek data:', error);
        });
}

// Update table with data
function updateTable(data) {
    console.log('updateTable called with data:', data);
    console.log('Data length:', data.length);
    
    const tbody = document.querySelector('#standingsTable tbody');
    tbody.innerHTML = '';

    // Sort data by total points (descending)
    const sortedData = [...data].sort((a, b) => b.total_points - a.total_points);
    console.log('Sorted data length:', sortedData.length);
    console.log('First 3 teams:', sortedData.slice(0, 3));
    console.log('Last 3 teams:', sortedData.slice(-3));

    sortedData.forEach((team, index) => {
        console.log(`Processing team ${index + 1}:`, team);
        const row = document.createElement('tr');
        
        // Create merged rank and rank change display
        let rankDisplayHtml = '';
        if (team.rank_change_badge) {
            // Use the new badge data from backend
            const badge = team.rank_change_badge;
            console.log(`Team ${team.team_name} badge data:`, badge);
            rankDisplayHtml = `
                <div class="flex items-center space-x-2">
                    <span class="text-lg font-bold text-slate-900">#${team.overall_rank || team.rank}</span>
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${badge.bg_color} ${badge.text_color} ${badge.border_color} border">
                        ${badge.icon} ${badge.text}
                    </span>
                </div>
            `;
        } else {
            // Fallback if no badge data
            console.log(`Team ${team.team_name} has no badge data`);
            rankDisplayHtml = `<span class="text-lg font-bold text-slate-900">#${team.overall_rank || team.rank}</span>`;
        }

        // Add previous gameweek score if available
        const previousScore = team.previous_gw_points !== undefined && team.previous_gw_points !== null ? ` (${team.previous_gw_points})` : '';
        
        // Create awards display
        let awardsHtml = '';
        if (team.awards && team.awards.length > 0) {
            awardsHtml = `
                <div class="flex flex-wrap gap-1">
                    ${team.awards.map(award => `
                        <span class="award-badge inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${award.color} border shadow-sm" 
                              title="${award.text}">
                            ${award.emoji}
                        </span>
                    `).join('')}
                </div>
            `;
        } else {
            awardsHtml = '<span class="text-gray-400 text-xs">—</span>';
        }
        
        row.innerHTML = `
            <td class="px-6 py-4 border-b border-indigo-100 text-sm">${rankDisplayHtml}</td>
            <td class="px-6 py-4 border-b border-indigo-100 text-sm text-slate-900">${team.team_name}</td>
            <td class="px-6 py-4 border-b border-indigo-100 text-sm text-slate-700">${team.manager_name}</td>
            <td class="px-6 py-4 border-b border-indigo-100 text-sm">${awardsHtml}</td>
            <td class="px-6 py-4 border-b border-indigo-100 text-sm text-slate-900">${team.gw_points}${previousScore}</td>
            <td class="px-6 py-4 border-b border-indigo-100 text-sm text-slate-900">${team.total_points}</td>
            <td class="px-6 py-4 border-b border-indigo-100 text-sm text-slate-900">£${team.team_value.toFixed(1)}m</td>
            <td class="px-6 py-4 border-b border-indigo-100 text-sm text-slate-900">£${team.bank_balance.toFixed(1)}m</td>
        `;
        
        tbody.appendChild(row);
    });
    
    console.log('Table updated with', tbody.children.length, 'rows');
}

// Update awards display
function updateAwards(awards) {
    if (!awards) return;

    // Update Weekly Champion
    const weeklyChampionCard = document.querySelector('#weekly-champion-card .award-content');
    if (awards.weekly_champion && awards.weekly_champion.length > 0) {
        weeklyChampionCard.innerHTML = awards.weekly_champion.map(champion => `
            <h3 class="text-lg font-semibold mb-2">${champion.team_name}</h3>
            <p class="text-sm mb-1">${champion.manager_name}</p>
            <p class="text-lg font-bold">${champion.points} points</p>
        `).join('<hr class="my-3">');
    } else {
        weeklyChampionCard.innerHTML = '<p class="text-white/80">No data available</p>';
    }

    // Update Wooden Spoon
    const woodenSpoonCard = document.querySelector('#wooden-spoon-card .award-content');
    if (awards.wooden_spoon && awards.wooden_spoon.length > 0) {
        woodenSpoonCard.innerHTML = awards.wooden_spoon.map(spoon => `
            <h3 class="text-lg font-semibold mb-2">${spoon.team_name}</h3>
            <p class="text-sm mb-1">${spoon.manager_name}</p>
            <p class="text-lg font-bold">${spoon.points} points</p>
        `).join('<hr class="my-3">');
    } else {
        woodenSpoonCard.innerHTML = '<p class="text-white/80">No data available</p>';
    }

    // Update Performance of the Week
    const gameweekChampionCard = document.querySelector('#gameweek-champion-card .award-content');
    if (awards.performance_of_week && awards.performance_of_week.length > 0) {
        gameweekChampionCard.innerHTML = awards.performance_of_week.map(champion => `
            <h3 class="text-lg font-semibold mb-2">${champion.team_name}</h3>
            <p class="text-sm mb-1">${champion.manager_name}</p>
            <p class="text-lg font-bold">${champion.points > 0 ? '+' : ''}${champion.points} points</p>
        `).join('<hr class="my-3">');
    } else {
        gameweekChampionCard.innerHTML = '<p class="text-white/80">No data available</p>';
    }

    // Update The Wall
    const theWallCard = document.querySelector('#the-wall-card .award-content');
    if (awards.the_wall && awards.the_wall.length > 0) {
        theWallCard.innerHTML = awards.the_wall.map(wall => `
            <h3 class="text-lg font-semibold mb-2">${wall.team_name}</h3>
            <p class="text-sm mb-1">${wall.manager_name}</p>
            <p class="text-lg font-bold">${wall.points} points</p>
            ${wall.details ? `<p class="text-sm text-white/80 mt-1">${wall.details}</p>` : ''}
        `).join('<hr class="my-3">');
    } else {
        theWallCard.innerHTML = '<p class="text-white/80">No data available</p>';
    }

    // Update Benchwarmer
    const benchwarmerCard = document.querySelector('#benchwarmer-card .award-content');
    if (awards.benchwarmer && awards.benchwarmer.length > 0) {
        benchwarmerCard.innerHTML = awards.benchwarmer.map(bench => `
            <h3 class="text-lg font-semibold mb-2">${bench.team_name}</h3>
            <p class="text-sm mb-1">${bench.manager_name}</p>
            <p class="text-lg font-bold">${bench.points} points</p>
            ${bench.details ? `<p class="text-sm text-white/80 mt-1">${bench.details}</p>` : ''}
        `).join('<hr class="my-3">');
    } else {
        benchwarmerCard.innerHTML = '<p class="text-white/80">No data available</p>';
    }

    // Update Captain Fantastic
    const captainFantasticCard = document.querySelector('#captain-fantastic-card .award-content');
    if (awards.captain_fantastic && awards.captain_fantastic.length > 0) {
        captainFantasticCard.innerHTML = awards.captain_fantastic.map(captain => `
            <h3 class="text-lg font-semibold mb-2">${captain.team_name}</h3>
            <p class="text-sm mb-1">${captain.manager_name}</p>
            <p class="text-lg font-bold">${captain.points} points</p>
            ${captain.details ? `<p class="text-sm text-white/80 mt-1">${captain.details}</p>` : ''}
        `).join('<hr class="my-3">');
    } else {
        captainFantasticCard.innerHTML = '<p class="text-white/80">No data available</p>';
    }
}

// Screenshot capture function
function captureScreenshot() {
    const captureArea = document.getElementById('captureArea');
    const screenshotBtn = document.getElementById('screenshotBtn');
    
    if (!captureArea) {
        console.error('Capture area not found');
        return;
    }

    // Show loading state
    const originalText = screenshotBtn.innerHTML;
    screenshotBtn.innerHTML = '📸 Capturing...';
    screenshotBtn.disabled = true;

    // Add screenshot mode class to simplify rendering
    captureArea.classList.add('screenshot-mode');
    
    // Wait for styles to apply
    setTimeout(() => {
        html2canvas(captureArea, {
            backgroundColor: '#ffffff',
            scale: 1.5,
            useCORS: true,
            allowTaint: true,
            logging: false,
            removeContainer: true,
            foreignObjectRendering: false,
            imageTimeout: 15000
        }).then(canvas => {
            console.log('Screenshot captured successfully');
            
            // Remove screenshot mode class
            captureArea.classList.remove('screenshot-mode');

            // Create download link
            const link = document.createElement('a');
            const gameweekSelect = document.getElementById('gameweekSelect');
            const currentGameweek = gameweekSelect ? gameweekSelect.value : 'unknown';
            link.download = `fpl-standings-gw${currentGameweek}.png`;
            link.href = canvas.toDataURL('image/png', 1.0);
            link.click();

            // Restore button
            screenshotBtn.innerHTML = originalText;
            screenshotBtn.disabled = false;
        }).catch(error => {
            console.error('Screenshot error:', error);
            
            // Remove screenshot mode class on error
            captureArea.classList.remove('screenshot-mode');

            // Restore button
            screenshotBtn.innerHTML = originalText;
            screenshotBtn.disabled = false;
        });
    }, 200);
}
