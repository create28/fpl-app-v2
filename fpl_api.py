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
            current_event = next((event for event in events if event['is_current']), None)
            if current_event:
                return current_event['id']
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

