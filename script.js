// Environment detection and API configuration
const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
const API_BASE_URL = isProduction 
    ? window.location.origin  // Use same domain (Render serves both frontend and API)
    : 'http://localhost:8000'; // Local development

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

    // Tab switching functionality
    const tableTab = document.getElementById('tableTab');
    const awardsTab = document.getElementById('awardsTab');
    const tableTabContent = document.getElementById('tableTabContent');
    const awardsTabContent = document.getElementById('awardsTabContent');

    if (tableTab && awardsTab) {
        tableTab.addEventListener('click', function() {
            // Switch to table tab
            tableTab.classList.add('active');
            awardsTab.classList.remove('active');
            tableTabContent.classList.add('active');
            awardsTabContent.classList.remove('active');
        });

        awardsTab.addEventListener('click', function() {
            // Switch to awards tab
            awardsTab.classList.add('active');
            tableTab.classList.remove('active');
            awardsTabContent.classList.add('active');
            tableTabContent.classList.remove('active');
        });
    }

    // Screenshot buttons
    const tableScreenshotBtn = document.getElementById('tableScreenshotBtn');
    const awardsScreenshotBtn = document.getElementById('awardsScreenshotBtn');
    
    if (tableScreenshotBtn) {
        tableScreenshotBtn.addEventListener('click', function() {
            captureScreenshot('table');
        });
    }
    
    if (awardsScreenshotBtn) {
        awardsScreenshotBtn.addEventListener('click', function() {
            captureScreenshot('awards');
        });
    }
});

// Initialize gameweek data
function initializeGameweekData() {
    const select = document.getElementById('gameweekSelect');
    // First load available gameweeks
    fetch(`${API_BASE_URL}/api/gameweeks`)
        .then(r => r.json())
        .then(data => {
            const gameweeks = Array.isArray(data.gameweeks) ? data.gameweeks : [];
            if (select) {
                select.innerHTML = '<option value="">Select Gameweek</option>';
                gameweeks.forEach(gw => {
                    const option = document.createElement('option');
                    option.value = gw;
                    option.textContent = `Gameweek ${gw}`;
                    select.appendChild(option);
                });
            }

            // Try to get current gameweek; fallback to highest available
            return fetch(`${API_BASE_URL}/api/current-gameweek`)
                .then(r => r.ok ? r.json() : Promise.reject())
                .then(d => ({ current: d.current_gameweek, gameweeks }))
                .catch(() => ({ current: (gameweeks.length ? Math.max(...gameweeks) : null), gameweeks }));
        })
        .then(({ current, gameweeks }) => {
            if (!current && gameweeks.length) current = Math.max(...gameweeks);
            if (current && select) {
                select.value = String(current);
                loadGameweekData(current);
            }
        })
        .catch(err => console.error('Initialization error:', err));
}

// Load gameweek data
function loadGameweekData(gameweek) {
    console.log('Loading data for gameweek:', gameweek);
    fetch(`${API_BASE_URL}/api/data/${gameweek}`)
        .then(response => response.json())
        .then(data => {
            console.log('Received data:', data);
            if (data && data.standings) {
                updateTable(data.standings);
                updateAwards(data.awards);
            } else if (data && data.status === 'error') {
                // Show empty state for no data
                updateTable([]);
                updateAwards({});
                console.log(`No data available for gameweek ${gameweek}: ${data.message}`);
            } else {
                updateTable([]);
                updateAwards({});
            }
        })
        .catch(error => {
            console.error('Error loading gameweek data:', error);
            updateTable([]);
            updateAwards({});
        });
}

// Update table with data
function updateTable(data) {
    console.log('updateTable called with data:', data);
    
    const tbody = document.querySelector('#standingsTable tbody');
    tbody.innerHTML = '';

    // Handle empty data case
    if (!data || !Array.isArray(data) || data.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="6" class="px-6 py-8 text-center text-gray-500">
                No data available for this gameweek. Try refreshing the data.
            </td>
        `;
        tbody.appendChild(row);
        return;
    }

    console.log('Data length:', data.length);
    
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
        if (team.rank_change !== undefined && team.rank_change !== null) {
            // Display rank with rank change
            const changeSymbol = team.rank_change > 0 ? '↑' : team.rank_change < 0 ? '↓' : '−';
            const changeText = team.rank_change !== 0 ? `${changeSymbol}${Math.abs(team.rank_change)}` : '−0';
            const changeColor = team.rank_change > 0 ? 'text-green-600' : team.rank_change < 0 ? 'text-red-600' : 'text-gray-500';
            
            rankDisplayHtml = `
                <div class="flex items-center space-x-2">
                    <span class="text-lg font-bold text-slate-900">#${team.overall_rank || team.rank}</span>
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 border border-gray-300">
                        <span class="${changeColor} font-semibold">${changeText}</span>
                    </span>
                </div>
            `;
            console.log(`Team ${team.team_name} rank change: ${changeText}`);
        } else {
            // Fallback if no rank change data
            console.log(`Team ${team.team_name} has no rank change data`);
            rankDisplayHtml = `<span class="text-lg font-bold text-slate-900">#${team.overall_rank || team.rank}</span>`;
        }

        // Add previous gameweek score if available
        const previousScore = team.previous_gw_points !== undefined && team.previous_gw_points !== null ? ` (${team.previous_gw_points})` : '';
        
        // Create awards display
        let awardsHtml = '';
        if (team.awards && team.awards.length > 0) {
            // Debug logging
            if (team.awards.length > 1) {
                console.log(`${team.team_name} has ${team.awards.length} awards:`, team.awards.map(a => a.type));
            }
            awardsHtml = `
                <div class="awards-container">
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
function captureScreenshot(tabType = 'table') {
    const captureArea = document.getElementById('captureArea');
    let screenshotBtn;
    let targetElement;
    
    // Determine which button to use (target is always captureArea now)
    targetElement = document.getElementById('captureArea');
    
    if (tabType === 'table') {
        screenshotBtn = document.getElementById('tableScreenshotBtn');
    } else if (tabType === 'awards') {
        screenshotBtn = document.getElementById('awardsScreenshotBtn');
    } else {
        screenshotBtn = document.getElementById('tableScreenshotBtn');
    }
    
    if (!targetElement || !screenshotBtn) {
        console.error('Target element or screenshot button not found');
        return;
    }

    // Show loading state
    const originalText = screenshotBtn.innerHTML;
    screenshotBtn.innerHTML = '📸 Capturing...';
    screenshotBtn.disabled = true;

    // Update gameweek numbers in screenshot titles
    const gameweekSelect = document.getElementById('gameweekSelect');
    const currentGameweek = gameweekSelect ? gameweekSelect.value : 'unknown';
    const gameweekNumbers = document.querySelectorAll('.gameweek-number');
    gameweekNumbers.forEach(element => {
        element.textContent = currentGameweek;
    });

    // Add screenshot mode class to simplify rendering
    if (captureArea) {
        captureArea.classList.add('screenshot-mode');
    }
    
    // Create a timeout promise to prevent infinite hanging
    const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Screenshot operation timed out after 15 seconds')), 15000);
    });

    // Check for library availability with retry
    let lib = window.htmlToImage;
    if (!lib) {
        // Try to wait a moment if it's still loading
        await new Promise(r => setTimeout(r, 500));
        lib = window.htmlToImage;
    }

    if (!lib) {
        throw new Error('Screenshot library not loaded. Please refresh the page and try again.');
    }

    // Main screenshot operation
    const screenshotPromise = (async () => {
        // Wait for styles and webfonts to apply
        if (document.fonts && document.fonts.ready) {
            await document.fonts.ready;
        }
        
        // Brief delay to allow layout to settle after class addition
        await new Promise(r => setTimeout(r, 1000));
        
        // Use html-to-image with simplified settings
        // Relies on CSS classes to hide elements
        return lib.toPng(targetElement, {
            quality: 0.95,
            cacheBust: true,
            skipAutoScale: true,
            style: {
                transform: 'none',
            }
        });
    })();

    // Race the screenshot against the timeout
    Promise.race([screenshotPromise, timeoutPromise])
        .then(dataUrl => {
            console.log(`${tabType} screenshot captured successfully`);
            
            // Create download link
            const link = document.createElement('a');
            link.download = `fpl-${tabType}-gw${currentGameweek}.png`;
            link.href = dataUrl;
            link.click();
        })
        .catch(error => {
            console.error('Screenshot error:', error);
            alert(`Screenshot failed: ${error.message}. Please try again.`);
        })
        .finally(() => {
            // ALWAYS cleanup, regardless of success or failure
            console.log('Cleaning up screenshot mode...');
            if (captureArea) {
                captureArea.classList.remove('screenshot-mode');
            }
            
            if (screenshotBtn) {
                screenshotBtn.innerHTML = originalText;
                screenshotBtn.disabled = false;
            }
        });
}
