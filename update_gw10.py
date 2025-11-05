#!/usr/bin/env python3
"""
Script to update gameweek 10 data in the database.
"""

from database_manager import db_manager
from fpl_api import fpl_api
from awards_calculator import awards_calculator
from data_export_import import save_export
from config import Config

def update_gameweek(gameweek):
    """Update data for a specific gameweek."""
    print(f"Updating gameweek {gameweek} data...")
    
    # Get league ID from config
    league_id = Config.FPL_LEAGUE_ID
    
    # Fetch league standings
    print(f"Fetching league standings from FPL API...")
    standings = fpl_api.get_league_standings(league_id)
    if not standings:
        print("Failed to fetch league standings")
        return False
    
    # Process and save data
    teams_data = []
    for entry in standings.get('standings', {}).get('results', []):
        team_data = {
            'team_id': entry['entry'],
            'team_name': entry['entry_name'],
            'manager_name': entry.get('player_name', 'Unknown Manager'),
            'gw_points': entry.get('event_total', 0),
            'total_points': entry['total'],
            'team_value': entry.get('value', 0),
            'bank_balance': entry.get('bank', 0)
        }
        teams_data.append(team_data)
    
    print(f"Found {len(teams_data)} teams")
    
    # Save to database
    print(f"Saving teams data to database...")
    db_manager.save_fpl_data(gameweek, teams_data)
    
    print(f"Successfully saved data for gameweek {gameweek}")
    
    # Calculate awards
    print(f"Calculating awards for gameweek {gameweek}...")
    
    # Get teams data from database
    teams = db_manager.get_fpl_data(gameweek)
    if not teams:
        print(f"No teams data found for gameweek {gameweek}")
        return False
    
    # Calculate basic awards
    basic_awards = awards_calculator.calculate_basic_awards(teams, gameweek)
    
    # Calculate detailed awards
    detailed_awards = awards_calculator.calculate_detailed_awards(teams, gameweek)
    
    # Merge awards
    all_awards = {**basic_awards, **detailed_awards}
    
    # Calculate Performance of the Week if we have previous data
    if gameweek > 1:
        previous_data = db_manager.get_previous_gameweek_data(gameweek)
        if previous_data:
            all_awards['performance_of_week'] = awards_calculator.calculate_performance_of_week(
                gameweek, teams, previous_data)
        else:
            all_awards['performance_of_week'] = []
    else:
        all_awards['performance_of_week'] = []
    
    # Save awards to database
    db_manager.save_award_winners(gameweek, all_awards)
    
    print(f"Successfully calculated and saved awards for gameweek {gameweek}")
    
    # Export to JSON file
    output_file = f"gw{gameweek}_with_awards.json"
    print(f"Exporting to {output_file}...")
    save_export(gameweek, output_file)
    
    print(f"Successfully updated gameweek {gameweek}!")
    return True

if __name__ == '__main__':
    import sys
    
    gameweek = 10
    if len(sys.argv) > 1:
        gameweek = int(sys.argv[1])
    
    print(f"Updating gameweek {gameweek}...")
    success = update_gameweek(gameweek)
    
    if success:
        print(f"\n✅ Gameweek {gameweek} data updated successfully!")
    else:
        print(f"\n❌ Failed to update gameweek {gameweek} data")
        sys.exit(1)


