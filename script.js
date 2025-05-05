document.getElementById('previousCsvFile').addEventListener('change', handlePreviousFile, false);
document.getElementById('currentCsvFile').addEventListener('change', handleCurrentFile, false);

let previousData = [];
let currentData = [];

function handlePreviousFile(event) {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function(e) {
      const csvData = e.target.result;
      Papa.parse(csvData, {
        header: true,
        skipEmptyLines: true,
        complete: function(results) {
          previousData = results.data;
          if (currentData.length > 0) displayData();
        }
      });
    };
    reader.readAsText(file);
  }
}

function handleCurrentFile(event) {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function(e) {
      const csvData = e.target.result;
      Papa.parse(csvData, {
        header: true,
        skipEmptyLines: true,
        complete: function(results) {
          currentData = results.data;
          if (previousData.length > 0) displayData();
        }
      });
    };
    reader.readAsText(file);
  }
}

function displayData() {
  const tableBody = document.querySelector('#leagueTable tbody');
  tableBody.innerHTML = ''; // Clear existing table data

  let maxPoints = -Infinity;
  let minPoints = Infinity;
  let maxPointsGain = -Infinity;
  let totalPoints = 0;
  let weeklyWinners = [];
  let woodenSpoons = [];
  let performanceOfTheWeek = [];

  const previousMap = {};
  previousData.forEach(row => {
    previousMap[row['Team Name']] = row;
  });

  currentData.forEach(row => {
    const previousRow = previousMap[row['Team Name']];
    if (previousRow) {
      const currentPoints = parseInt(row['Gameweek Points'], 10);
      const previousPoints = parseInt(previousRow['Gameweek Points'], 10);
      const pointsGain = currentPoints - previousPoints;
      totalPoints += currentPoints;

      const totalPointsCurrent = row['Total Points'] || 0; // Total Points from current gameweek CSV

      // Determine Weekly Winner and Wooden Spoon
      if (currentPoints === maxPoints) {
        weeklyWinners.push(`${row['Manager Name']} (${currentPoints} points)`);
      } else if (currentPoints > maxPoints) {
        maxPoints = currentPoints;
        weeklyWinners = [`${row['Manager Name']} (${currentPoints} points)`];
      }

      if (currentPoints === minPoints) {
        woodenSpoons.push(`${row['Manager Name']} (${currentPoints} points)`);
      } else if (currentPoints < minPoints) {
        minPoints = currentPoints;
        woodenSpoons = [`${row['Manager Name']} (${currentPoints} points)`];
      }

      // Determine Performance of the Week
      if (pointsGain === maxPointsGain) {
        performanceOfTheWeek.push(`${row['Manager Name']} (+${pointsGain} points)`);
      } else if (pointsGain > maxPointsGain) {
        maxPointsGain = pointsGain;
        performanceOfTheWeek = [`${row['Manager Name']} (+${pointsGain} points)`];
      }

      const rankChange = parseInt(previousRow['Rank'], 10) - parseInt(row['Rank'], 10);
      const pointsChange = currentPoints - previousPoints;

      const rankChangeClass = rankChange > 0 ? 'rank-change-positive' : rankChange < 0 ? 'rank-change-negative' : '';
      const pointsChangeClass = pointsChange > 0 ? 'points-change-positive' : pointsChange < 0 ? 'points-change-negative' : '';

const tr = document.createElement('tr');
tr.innerHTML = `
  <td>${row['Team Name']} (${row['Manager Name']})</td>
  <td><strong>${row['Rank']}</strong> (${previousRow['Rank']})</td>
  <td class="${rankChangeClass}">${rankChange > 0 ? '+' : ''}${rankChange}</td>
  <td><strong>${currentPoints}</strong> (${previousPoints})</td>
  <td class="${pointsChangeClass}">${pointsChange > 0 ? '+' : ''}${pointsChange}</td>
  <td><strong>${totalPointsCurrent}</strong></td>
`;
tableBody.appendChild(tr);

    }
  });

  // Calculate and display average score
  const averageScore = Math.round(totalPoints / currentData.length);
  document.getElementById('averageScore').textContent = `${averageScore} points`;

  // Display awards
  document.getElementById('weeklyWinner').textContent = weeklyWinners.join(", ");
  document.getElementById('woodenSpoon').textContent = woodenSpoons.join(", ");
  document.getElementById('performanceOfTheWeek').textContent = performanceOfTheWeek.join(", ");
}

// Screenshot capture function
function captureScreenshot() {
  const captureArea = document.getElementById("captureArea");

  html2canvas(captureArea, {
    ignoreElements: element => element.tagName === 'BUTTON' || (element.tagName === 'INPUT' && element.type === 'file')
  }).then(canvas => {
    const link = document.createElement("a");
    link.href = canvas.toDataURL("image/png");
    link.download = "FPL_League_Summary.png";
    link.click();
  });
}

document.addEventListener('DOMContentLoaded', function() {
    // First get the latest valid gameweek
    fetch('/api/current-gameweek')
        .then(response => response.json())
        .then(data => {
            const latestGameweek = data.current_gameweek;
            console.log('Latest valid gameweek:', latestGameweek);
            
            // Get all available gameweeks
            return fetch('/api/gameweeks')
                .then(response => response.json())
                .then(gameweeks => {
                    const select = document.getElementById('gameweekSelect');
                    gameweeks.forEach(gw => {
                        const option = document.createElement('option');
                        option.value = gw;
                        option.textContent = `Gameweek ${gw}`;
                        select.appendChild(option);
                    });
                    
                    // Set latest gameweek as default selection
                    select.value = latestGameweek;
                    console.log('Set default gameweek to:', latestGameweek);
                    
                    // Load all gameweek data
                    return loadAllGameweekData();
                });
        })
        .catch(error => {
            console.error('Error loading gameweeks:', error);
            // If there's an error, default to gameweek 1
            const select = document.getElementById('gameweekSelect');
            select.value = '1';
            loadAllGameweekData();
        });

    // Handle gameweek selection
    document.getElementById('gameweekSelect').addEventListener('change', function(e) {
        const gameweek = e.target.value;
        if (gameweek) {
            displayGameweekData(gameweek);
        }
    });

    // Handle award type tabs
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', function() {
            // Update active tab
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Update displayed award type
            const awardType = this.dataset.award;
            displayAwardsHistory(awardType);
        });
    });

    // Screenshot button event
    document.getElementById('screenshotBtn').addEventListener('click', captureScreenshot);
});

let allGameweekData = {};

function loadAllGameweekData() {
    // Load all gameweek data
    return fetch('/api/all-data')
        .then(response => response.json())
        .then(allData => {
            allGameweekData = allData;
            
            // Get the selected gameweek from the dropdown
            const selectedGameweek = document.getElementById('gameweekSelect').value;
            console.log('Displaying data for gameweek:', selectedGameweek);
            
            // Display the selected gameweek data
            displayGameweekData(selectedGameweek);
            
            // Initialize awards history with the first tab
            const firstTab = document.querySelector('.tab-button.active');
            if (firstTab) {
                displayAwardsHistory(firstTab.dataset.award);
            }
        })
        .catch(error => console.error('Error loading gameweek data:', error));
}

function displayGameweekData(gameweek) {
    const data = allGameweekData[gameweek];
    if (data) {
        updateTable(data.standings);
        updateAwards(data.awards);
    }
}

function updateTable(data) {
    const tbody = document.querySelector('#standingsTable tbody');
    tbody.innerHTML = '';

    // Sort data by total points (descending)
    const sortedData = [...data].sort((a, b) => b.total_points - a.total_points);

    sortedData.forEach((team, index) => {
        const row = document.createElement('tr');
        
        // Add rank change indicator
        let rankChangeHtml = '';
        if (team.rank_change) {
            const change = team.rank_change;
            const arrow = change > 0 ? '↑' : change < 0 ? '↓' : '→';
            const color = change > 0 ? 'green' : change < 0 ? 'red' : 'gray';
            rankChangeHtml = `<span style="color: ${color}">${arrow} ${Math.abs(change)}</span>`;
        }

        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${team.team_name}</td>
            <td>${team.manager_name}</td>
            <td>${team.gw_points}</td>
            <td>${team.total_points}</td>
            <td>£${team.team_value.toFixed(1)}m</td>
            <td>£${team.bank_balance.toFixed(1)}m</td>
            <td>${rankChangeHtml}</td>
        `;
        
        tbody.appendChild(row);
    });
}

function updateAwards(awards) {
    if (!awards) return;

    // Update Weekly Champion
    const weeklyChampionCard = document.querySelector('.award-card:nth-child(1) .award-content');
    if (awards.weekly_champion && awards.weekly_champion.length > 0) {
        weeklyChampionCard.innerHTML = awards.weekly_champion.map(champion => `
            <h3>${champion.team_name}</h3>
            <p>${champion.manager_name}</p>
            <p class="points">${champion.points} points</p>
        `).join('<hr>');
    } else {
        weeklyChampionCard.innerHTML = '<p>No data available</p>';
    }

    // Update Wooden Spoon
    const woodenSpoonCard = document.querySelector('.award-card:nth-child(2) .award-content');
    if (awards.wooden_spoon && awards.wooden_spoon.length > 0) {
        woodenSpoonCard.innerHTML = awards.wooden_spoon.map(spoon => `
            <h3>${spoon.team_name}</h3>
            <p>${spoon.manager_name}</p>
            <p class="points">${spoon.points} points</p>
        `).join('<hr>');
    } else {
        woodenSpoonCard.innerHTML = '<p>No data available</p>';
    }

    // Update Gameweek Champion
    const gameweekChampionCard = document.querySelector('.award-card:nth-child(3) .award-content');
    if (awards.gameweek_champion && awards.gameweek_champion.length > 0) {
        gameweekChampionCard.innerHTML = awards.gameweek_champion.map(champion => `
            <h3>${champion.team_name}</h3>
            <p>${champion.manager_name}</p>
            <p class="points">+${champion.points} points</p>
        `).join('<hr>');
    } else {
        gameweekChampionCard.innerHTML = '<p>No data available</p>';
    }
}

function displayAwardsHistory(awardType) {
    const historyContent = document.getElementById('awardsHistoryContent');
    if (!allGameweekData) {
        historyContent.innerHTML = '<p>No awards data available.</p>';
        return;
    }

    // Collect all awards of the specified type across all gameweeks
    const allAwards = [];
    Object.entries(allGameweekData).forEach(([gameweek, data]) => {
        if (data.awards && data.awards[awardType]) {
            data.awards[awardType].forEach(winner => {
                allAwards.push({
                    gameweek: parseInt(gameweek),
                    ...winner
                });
            });
        }
    });

    if (allAwards.length === 0) {
        historyContent.innerHTML = '<p>No awards data available.</p>';
        return;
    }

    // Count wins for each manager
    const winCounts = {};
    allAwards.forEach(award => {
        const key = `${award.manager_name} (${award.team_name})`;
        winCounts[key] = (winCounts[key] || 0) + 1;
    });

    // Sort by gameweek (descending)
    allAwards.sort((a, b) => b.gameweek - a.gameweek);

    const historyHTML = allAwards.map(award => {
        const key = `${award.manager_name} (${award.team_name})`;
        const winCount = winCounts[key];
        const winBadge = winCount > 1 ? `<span class="win-badge">${winCount}×</span>` : '';
        
        return `
            <div class="award-history-item">
                <h3>Gameweek ${award.gameweek}</h3>
                <p class="team-name">${award.team_name}</p>
                <p class="manager-name">${award.manager_name} ${winBadge}</p>
                <p class="points">${award.points} points</p>
            </div>
        `;
    }).join('');

    historyContent.innerHTML = historyHTML;
}
