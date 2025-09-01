import requests
import json
from datetime import datetime, timedelta
import os

class FPLAPI:
    def __init__(self):
        self.base_url = "https://fantasy.premierleague.com/api"
        self.session = requests.Session()
        # Identify politely to upstream and improve compatibility
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; FPL-App/1.0; +https://github.com/create28/fpl-app-v2)'
        })
        # Disable SSL verification for development; consider enabling in production
        self.session.verify = False
        # Store last error for diagnostics
        self.last_error = None
        
    def fetch_data(self, endpoint, max_retries=3):
        """Fetch data from FPL API with retry logic."""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    self.last_error = None
                    return response.json()
                else:
                    snippet = ''
                    try:
                        snippet = response.text[:200]
                    except Exception:
                        pass
                    msg = f"status {response.status_code} for {url} :: {snippet}"
                    self.last_error = msg
                    print(f"API request failed: {msg}")
            except Exception as e:
                self.last_error = str(e)
                print(f"API request attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    continue
                else:
                    print("Max retries reached")
        
        return None
    
    def get_bootstrap_static(self):
        """Get bootstrap static data (teams, players, etc.)."""
        return self.fetch_data("bootstrap-static/")
    
    def get_gameweek_data(self, gameweek):
        """Get data for a specific gameweek."""
        return self.fetch_data(f"event/{gameweek}/live/")
    
    def get_league_standings(self, league_id):
        """Get league standings."""
        return self.fetch_data(f"leagues-classic/{league_id}/standings/")
    
    def get_team_details(self, team_id, gameweek):
        """Get detailed team data for a specific gameweek."""
        return self.fetch_data(f"entry/{team_id}/event/{gameweek}/picks/")
    
    def get_team_picks(self, team_id, gameweek):
        """Get team picks for a specific gameweek."""
        return self.fetch_data(f"entry/{team_id}/event/{gameweek}/picks/")
    
    def get_player_performance(self, player_id, gameweek):
        """Get individual player performance data for a specific gameweek."""
        return self.fetch_data(f"element-summary/{player_id}/")
    
    def get_bootstrap_data(self):
        """Get bootstrap static data (teams, players, etc.)."""
        return self.get_bootstrap_static()
    
    def get_current_gameweek(self):
        """Get the current gameweek from the API."""
        bootstrap_data = self.get_bootstrap_static()
        if bootstrap_data and 'events' in bootstrap_data:
            events = bootstrap_data['events']
            print(f"Found {len(events)} events in bootstrap data")
            
            # First try to find current gameweek
            current_event = next((event for event in events if event.get('is_current')), None)
            if current_event:
                print(f"Found current gameweek: {current_event['id']}")
                return current_event['id']
            
            # If no current event, find the next upcoming one
            next_event = next((event for event in events if event.get('is_next')), None)
            if next_event:
                print(f"No current gameweek, using next: {next_event['id']}")
                return next_event['id']
            
            # If neither current nor next, find the latest finished one
            finished_events = [event for event in events if event.get('finished')]
            if finished_events:
                latest_finished = max(finished_events, key=lambda x: x['id'])
                print(f"Using latest finished gameweek: {latest_finished['id']}")
                return latest_finished['id']
            
            # Fallback to first event
            if events:
                print(f"Fallback to first gameweek: {events[0]['id']}")
                return events[0]['id']
        
        print("No gameweek data found in bootstrap")
        if self.last_error:
            print(f"Last API error: {self.last_error}")
        return None
    
    def get_league_id_from_team(self, team_id):
        """Get the league ID for a specific team."""
        try:
            response = self.session.get(f"{self.base_url}/entry/{team_id}/", timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get('leagues', {}).get('classic', [{}])[0].get('id')
        except Exception as e:
            print(f"Failed to get league ID for team {team_id}: {e}")
        return None

# Global FPL API instance
fpl_api = FPLAPI()

