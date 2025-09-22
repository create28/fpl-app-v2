# FPL Award Calculation Requirements

## Overview
This document outlines the exact requirements for calculating FPL awards. **Fallback awards should NEVER be used** - if proper player data is not available, awards should show as empty.

## Prerequisites
1. **Player data MUST be downloaded first** before calculating detailed awards
2. Use the "Fetch Player Data" button in the web interface to download player performance data
3. Only calculate awards after player data is available

## Award Calculations

### 1. Weekly Champion 👑
- **Calculation**: Team(s) with the highest gameweek points
- **Data Source**: Basic team data (always available)
- **Display**: Team name, manager name, points

### 2. Wooden Spoon 🥄
- **Calculation**: Team(s) with the lowest gameweek points
- **Data Source**: Basic team data (always available)
- **Display**: Team name, manager name, points

### 3. Performance of the Week 🚀
- **Calculation**: Team(s) with the greatest improvement in gameweek points from previous week
- **Data Source**: Basic team data (requires previous week data)
- **Display**: Team name, manager name, point difference

### 4. The Wall 🧱
- **Calculation**: Team with the most points from Goalkeeper and Defender players in starting XI (positions 1-11)
- **Data Source**: Player performance data (REQUIRED)
- **Requirements**:
  - Only count players in starting XI positions (1-11)
  - Only count players with element_type 1 (GKP) or 2 (DEF)
  - Sum their gameweek points
- **Display**: Team name, manager name, total points, player breakdown

### 5. Benchwarmer 🪑
- **Calculation**: Team with the most points from bench players (positions 12, 13, 14, 15)
- **Data Source**: Player performance data (REQUIRED)
- **Requirements**:
  - Only count players in bench positions (12-15)
  - Sum their gameweek points
  - Exclude if bench boost chip was used
- **Display**: Team name, manager name, total points, player breakdown

### 6. Captain Fantastic ⭐
- **Calculation**: Team with the captain that scored the most points (raw captain points)
- **Data Source**: Player performance data (REQUIRED)
- **Requirements**:
  - Find the captain (is_captain = true)
  - Use raw captain points for comparison (not non-captain value)
  - Display non-captain value in details for reference:
    - Regular captain: base_points / 2
    - Triple captain: base_points / 3
  - Compare raw captain points across teams
- **Display**: Team name, manager name, raw captain points, captain details with non-captain value

## Data Requirements

### Player Performance Data Structure
Each player record must include:
- `player_id`: Unique player identifier
- `player_name`: Player's name
- `position`: Squad position (1-15)
- `element_type`: Player type (1=GKP, 2=DEF, 3=MID, 4=FWD)
- `gw_points`: Gameweek points scored
- `is_captain`: Boolean indicating if player is captain
- `chips_used`: Chip used (empty string, '3xc', 'bboost', etc.)

### Database Tables Required
1. `fpl_data`: Basic team data (gameweek, team_id, team_name, manager_name, gw_points, total_points, team_value, bank_balance)
2. `player_performance`: Detailed player data (gameweek, team_id, player_id, player_name, position, element_type, gw_points, is_captain, chips_used)
3. `award_winners`: Calculated awards (gameweek, award_type, team_id, team_name, manager_name, points, additional_data)

## Implementation Notes

### When to Show Empty Awards
- If no player performance data exists for a gameweek
- If player data exists but no players meet the criteria (e.g., no bench players with points)
- If calculation fails due to missing required data

### Error Handling
- Always check for player data availability before calculating detailed awards
- Log warnings when player data is missing
- Return empty awards object `{}` when data is insufficient
- Never use fallback calculations based on team-level data

### Testing
- Test with gameweeks that have full player data
- Test with gameweeks that have partial player data
- Test with gameweeks that have no player data
- Verify all calculations match FPL rules exactly

## Workflow for New Gameweeks

1. **Fetch basic team data** (automatic)
2. **Download player performance data** (manual - use "Fetch Player Data" button)
3. **Calculate basic awards** (Weekly Champion, Wooden Spoon, Performance of the Week)
4. **Calculate detailed awards** (The Wall, Benchwarmer, Captain Fantastic) - only if player data exists
5. **Display results** - show empty for detailed awards if no player data

## Common Issues to Avoid

1. **Don't use fallback awards** - they mask the real problem of missing player data
2. **Don't calculate detailed awards without player data** - always check availability first
3. **Don't mix team-level and player-level calculations** - they're fundamentally different
4. **Don't assume team_value data is available** - it's often 0 in the API
5. **Don't use efficiency calculations as fallbacks** - they don't represent actual FPL performance

## Future Maintenance

- This document should be updated if FPL rules change
- Award calculation logic should be tested with each new gameweek
- Player data download should be automated if possible
- Consider adding validation to ensure data completeness before calculations
