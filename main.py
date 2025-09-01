#!/usr/bin/env python3
"""
FPL Data Server - Main Application
==================================

This is the main entry point for the FPL Data Server application.
It orchestrates all the modules and provides the main application logic.
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta
from database_manager import db_manager
from fpl_api import fpl_api
from awards_calculator import awards_calculator
from data_processor import data_processor
from web_server import start_server

class FPLDataServer:
    def __init__(self):
        self.running = False
        self.refresh_thread = None
        
    def start(self, port=None):
        """Start the FPL Data Server."""
        from config import Config
        
        # Use config port if none specified
        if port is None:
            port = Config.PORT
            
        print("Starting FPL Data Server...")
        Config.print_config()
        self.running = True
        
        # Start periodic refresh thread (non-blocking)
        self.refresh_thread = threading.Thread(target=self.periodic_refresh, daemon=True)
        self.refresh_thread.start()
        print("Periodic refresh thread started")

        # Start web server LAST (blocking)
        print("Starting web server...")
        try:
            start_server(port)
        except KeyboardInterrupt:
            print("\nReceived interrupt signal, shutting down...")
            self.stop()
        except Exception as e:
            print(f"Error starting web server: {e}")
            self.stop()
    
    def stop(self):
        """Stop the FPL Data Server."""
        print("Stopping FPL Data Server...")
        self.running = False
        if self.refresh_thread:
            self.refresh_thread.join(timeout=5)
    
    def periodic_refresh(self):
        """Periodic data refresh thread."""
        while self.running:
            try:
                print("==================================================")
                print("Starting periodic data refresh...")
                current_time = datetime.now()
                print(f"Current time: {current_time}")
                
                # Clean up old cache data
                self.cleanup_old_cache()
                
                # Get current gameweek
                current_gameweek = fpl_api.get_current_gameweek()
                if current_gameweek:
                    print(f"Current gameweek: {current_gameweek}")
                    
                    # Check if we need to refresh data
                    if self.should_refresh_data(current_gameweek):
                        print(f"Refreshing data for gameweek {current_gameweek}")
                        self.refresh_gameweek_data(current_gameweek)
                        
                        # Calculate awards
                        print(f"Calculating awards for gameweek {current_gameweek}")
                        self.calculate_gameweek_awards(current_gameweek)
                
                # Wait before next refresh (every hour)
                time.sleep(3600)
                
            except Exception as e:
                print(f"Error in periodic refresh: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying
    
    def cleanup_old_cache(self):
        """Clean up old cache data."""
        print("Cleaning up old cache data...")
        try:
            # Remove old JSON cache files
            cache_files = [f for f in os.listdir('.') if f.endswith('.json') and 'cache' in f]
            for cache_file in cache_files:
                file_path = os.path.join('.', cache_file)
                file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_age > timedelta(hours=24):
                    os.remove(file_path)
                    print(f"Removed old cache file: {cache_file}")
        except Exception as e:
            print(f"Error cleaning up cache: {e}")
    
    def should_refresh_data(self, gameweek):
        """Check if we should refresh data for a gameweek."""
        try:
            # Check if we have data for this gameweek
            existing_data = db_manager.get_fpl_data(gameweek)
            if not existing_data:
                print(f"No existing data for gameweek {gameweek}, will refresh")
                return True
            
            # Check if data is recent (within last hour)
            # For now, always refresh - you could implement more sophisticated logic here
            return True
            
        except Exception as e:
            print(f"Error checking if data should be refreshed: {e}")
            return True
    
    def refresh_gameweek_data(self, gameweek):
        """Refresh data for a specific gameweek."""
        try:
            print(f"Refreshing data for gameweek {gameweek}...")
            
            # Get league ID from config
            from config import Config
            league_id = Config.FPL_LEAGUE_ID
            
            # Fetch league standings
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
            
            # Save to database
            db_manager.save_fpl_data(gameweek, teams_data)
            
            print(f"Successfully refreshed data for gameweek {gameweek}")
            return True
        
        except Exception as e:
            print(f"Error refreshing data for gameweek {gameweek}: {e}")
            return False
    
    def calculate_gameweek_awards(self, gameweek):
        """Calculate awards for a specific gameweek."""
        try:
            print(f"Calculating awards for gameweek {gameweek}...")
            
            # Get teams data
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
            
            print(f"Successfully calculated awards for gameweek {gameweek}")
            return True
        
        except Exception as e:
            print(f"Error calculating awards for gameweek {gameweek}: {e}")
            return False

def main():
    """Main entry point."""
    print("FPL Data Server")
    print("===============")
    
    # Check if we're in the right directory
    if not os.path.exists('index.html'):
        print("Error: index.html not found. Please run this script from the project directory.")
        sys.exit(1)
    
    # Create server instance
    server = FPLDataServer()
    
    try:
        # Start the server
        server.start()
    except KeyboardInterrupt:
        print("\nReceived interrupt signal, shutting down...")
    finally:
        server.stop()
        print("Server stopped.")

if __name__ == '__main__':
    main()

