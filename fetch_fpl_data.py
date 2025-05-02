import requests
import csv
import datetime
import os
import pandas as pd
import urllib3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import parse_qs, urlparse
import sqlite3
import time
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize SQLite database for historical data
def init_db():
    """Initialize the SQLite database for storing historical FPL data."""
    conn = sqlite3.connect('fpl_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS fpl_data
                 (gameweek INTEGER,
                  team_id INTEGER,
                  team_name TEXT,
                  manager_name TEXT,
                  gw_points INTEGER,
                  total_points INTEGER,
                  rank INTEGER,
                  team_value REAL,
                  bank_balance REAL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (gameweek, team_id))''')
    
    # Create table for award winners
    c.execute('''CREATE TABLE IF NOT EXISTS award_winners
                 (gameweek INTEGER,
                  award_type TEXT,
                  team_id INTEGER,
                  team_name TEXT,
                  manager_name TEXT,
                  points INTEGER,
                  PRIMARY KEY (gameweek, award_type))''')
    
    conn.commit()
    conn.close()

def store_fpl_data(gameweek, data):
    """Store FPL data in the database."""
    conn = sqlite3.connect('fpl_history.db')
    c = conn.cursor()
    
    for team in data:
        c.execute('''INSERT OR REPLACE INTO fpl_data 
                    (gameweek, team_id, team_name, manager_name, gw_points, 
                     total_points, rank, team_value, bank_balance)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (gameweek, team['team_id'], team['team_name'], 
                  team['manager_name'], team['gw_points'], team['total_points'],
                  team['rank'], team['team_value'], team['bank_balance']))
    
    conn.commit()
    conn.close()

def store_award_winners(gameweek, data, gameweek_champions):
    """Store award winners in the database."""
    conn = sqlite3.connect('fpl_history.db')
    c = conn.cursor()
    
    # Calculate all awards
    awards = calculate_awards(data)
    
    # Store weekly champions
    for champion in awards['weekly_champion']:
        c.execute('''INSERT OR REPLACE INTO award_winners 
                    (gameweek, award_type, team_id, team_name, manager_name, points)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (gameweek, 'weekly_champion', 
                  next((team['team_id'] for team in data 
                       if team['team_name'] == champion['team_name']), None),
                  champion['team_name'], champion['manager_name'], champion['points']))
    
    # Store wooden spoons
    for spoon in awards['wooden_spoon']:
        c.execute('''INSERT OR REPLACE INTO award_winners 
                    (gameweek, award_type, team_id, team_name, manager_name, points)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (gameweek, 'wooden_spoon',
                  next((team['team_id'] for team in data 
                       if team['team_name'] == spoon['team_name']), None),
                  spoon['team_name'], spoon['manager_name'], spoon['points']))
    
    # Store gameweek champions
    for champion in gameweek_champions:
        c.execute('''INSERT OR REPLACE INTO award_winners 
                    (gameweek, award_type, team_id, team_name, manager_name, points)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (gameweek, 'gameweek_champion',
                  next((team['team_id'] for team in data 
                       if team['team_name'] == champion['team_name']), None),
                  champion['team_name'], champion['manager_name'], champion['points']))
    
    conn.commit()
    conn.close()

def get_award_winners(gameweek, award_type=None):
    """Retrieve award winners for a specific gameweek and optionally filter by award type."""
    conn = sqlite3.connect('fpl_history.db')
    c = conn.cursor()
    
    if award_type:
        c.execute('''SELECT * FROM award_winners WHERE gameweek = ? AND award_type = ?''', 
                 (gameweek, award_type))
    else:
        c.execute('''SELECT * FROM award_winners WHERE gameweek = ?''', (gameweek,))
    
    winners = []
    for row in c.fetchall():
        winners.append({
            'team_name': row[3],
            'manager_name': row[4],
            'points': row[5]
        })
    
    conn.close()
    return winners

def get_historical_data(gameweek):
    """Retrieve historical FPL data from the database."""
    conn = sqlite3.connect('fpl_history.db')
    c = conn.cursor()
    
    # Get current gameweek data
    c.execute('''SELECT * FROM fpl_data WHERE gameweek = ?''', (gameweek,))
    current_data = []
    for row in c.fetchall():
        current_data.append({
            'team_id': row[1],
            'team_name': row[2],
            'manager_name': row[3],
            'gw_points': row[4],
            'total_points': row[5],
            'rank': row[6],
            'team_value': row[7],
            'bank_balance': row[8]
        })
    
    # Get previous gameweek data for comparison
    if gameweek > 1:
        c.execute('''SELECT * FROM fpl_data WHERE gameweek = ?''', (gameweek - 1,))
        previous_data = {row[1]: row[6] for row in c.fetchall()}  # team_id: rank
        
        # Add rank changes
        for team in current_data:
            if team['team_id'] in previous_data:
                team['rank_change'] = previous_data[team['team_id']] - team['rank']
    
    conn.close()
    return current_data

# Function to fetch data from a given URL
def fetch_data(url):
    try:
        response = requests.get(url, verify=False)  # Disable SSL verification
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching data: {response.status_code}")
            return None
    except requests.exceptions.SSLError as e:
        print(f"SSL error: {e}")
        return None

def get_all_gameweek_data():
    """Fetch data for all available gameweeks."""
    all_data = {}
    for gameweek in range(1, 39):  # 1-38
        data = get_fpl_data(gameweek)
        if data:
            all_data[gameweek] = data
    return all_data

def calculate_awards(data):
    """Calculate all awards for a given gameweek's data."""
    if not data:
        return {
            'weekly_champion': [],
            'wooden_spoon': [],
            'gameweek_champion': []
        }

    # Filter out teams with 0 points
    valid_teams = [team for team in data if team['gw_points'] > 0]
    
    if not valid_teams:
        return {
            'weekly_champion': [],
            'wooden_spoon': [],
            'gameweek_champion': []
        }

    # Find weekly champion (most points)
    max_points = max(team['gw_points'] for team in valid_teams)
    weekly_champions = [team for team in valid_teams if team['gw_points'] == max_points]
    
    # Find wooden spoon (least points)
    min_points = min(team['gw_points'] for team in valid_teams)
    wooden_spoons = [team for team in valid_teams if team['gw_points'] == min_points]
    
    return {
        'weekly_champion': [{
            'team_name': champ['team_name'],
            'manager_name': champ['manager_name'],
            'points': champ['gw_points']
        } for champ in weekly_champions],
        'wooden_spoon': [{
            'team_name': spoon['team_name'],
            'manager_name': spoon['manager_name'],
            'points': spoon['gw_points']
        } for spoon in wooden_spoons]
    }

def calculate_gameweek_champion(gameweek, current_data, previous_data):
    """Calculate the gameweek champion based on points improvement."""
    if not previous_data:
        return []
    
    # Filter out teams with 0 points in current gameweek
    valid_current_teams = [team for team in current_data if team['gw_points'] > 0]
    
    if not valid_current_teams:
        return []
    
    improvements = []
    for current_team in valid_current_teams:
        for previous_team in previous_data:
            if current_team['team_id'] == previous_team['team_id']:
                improvement = current_team['gw_points'] - previous_team['gw_points']
                improvements.append((current_team, improvement))
                break
    
    if not improvements:
        return []
    
    max_improvement = max(imp[1] for imp in improvements)
    champions = [imp[0] for imp in improvements if imp[1] == max_improvement]
    
    return [{
        'team_name': champ['team_name'],
        'manager_name': champ['manager_name'],
        'points': champ['gw_points']
    } for champ in champions]

def save_data_to_json(data, filename):
    """Save data to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f)

def load_data_from_json(filename):
    """Load data from a JSON file if it exists and is not too old."""
    if not os.path.exists(filename):
        return None
    
    # Check if file is older than 1 hour
    file_time = datetime.fromtimestamp(os.path.getmtime(filename))
    if datetime.now() - file_time > timedelta(hours=1):
        return None
    
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        return None

def get_fpl_data(gameweek):
    """Fetch and process FPL data for a specific gameweek."""
    # First try to get historical data from database
    historical_data = get_historical_data(gameweek)
    if historical_data:
        # Get previous gameweek data for gameweek champion calculation
        previous_data = get_historical_data(gameweek - 1) if gameweek > 1 else None
        
        # Calculate all awards
        awards = calculate_awards(historical_data)
        awards['gameweek_champion'] = calculate_gameweek_champion(gameweek, historical_data, previous_data)
        
        return {
            'standings': historical_data,
            'awards': awards
        }

    # If no historical data, try to get from JSON cache
    cache_file = f'cache/gameweek_{gameweek}.json'
    cached_data = load_data_from_json(cache_file)
    if cached_data:
        return cached_data

    # If no cached data, fetch from API
    league_id = 1658794
    league_url = f"https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/"
    league_data = fetch_data(league_url)

    if not league_data:
        return None

    standings = league_data['standings']['results']
    current_data = []
    
    for team in standings:
        team_id = team['entry']
        team_name = team['entry_name']
        manager_name = team['player_name']
        rank = team['rank']

        # Fetch gameweek points and other info
        gw_url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{gameweek}/picks/"
        gw_data = fetch_data(gw_url)

        if gw_data:
            gw_points = gw_data['entry_history']['points']
            total_points = gw_data['entry_history']['total_points']
            team_value = gw_data['entry_history']['value'] / 10
            bank_balance = gw_data['entry_history']['bank'] / 10
        else:
            gw_points = 0
            total_points = 0
            team_value = 0
            bank_balance = 0

        team_data = {
            'team_id': team_id,
            'team_name': team_name,
            'manager_name': manager_name,
            'gw_points': gw_points,
            'total_points': total_points,
            'rank': rank,
            'team_value': team_value,
            'bank_balance': bank_balance
        }
        current_data.append(team_data)

    # Store the data for future use
    store_fpl_data(gameweek, current_data)
    
    # Get previous gameweek data for comparison
    previous_data = get_historical_data(gameweek - 1) if gameweek > 1 else None
    if previous_data:
        previous_ranks = {team['team_id']: team['rank'] for team in previous_data}
        for team in current_data:
            if team['team_id'] in previous_ranks:
                team['rank_change'] = previous_ranks[team['team_id']] - team['rank']

    # Calculate all awards
    awards = calculate_awards(current_data)
    awards['gameweek_champion'] = calculate_gameweek_champion(gameweek, current_data, previous_data)
    
    # Store award winners
    store_award_winners(gameweek, current_data, awards['gameweek_champion'])

    result_data = {
        'standings': current_data,
        'awards': awards
    }

    # Cache the result
    os.makedirs('cache', exist_ok=True)
    save_data_to_json(result_data, cache_file)

    return result_data

def fetch_current_gameweek():
    """Fetch the current gameweek from the FPL API."""
    try:
        response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/', verify=False)
        if response.status_code == 200:
            data = response.json()
            events = data['events']
            for event in events:
                if event['is_current']:
                    return event['id']
        return 1  # Default to gameweek 1 if current gameweek not found
    except Exception as e:
        print(f"Error fetching current gameweek: {e}")
        return 1

def preload_data():
    """Preload data for current gameweek only."""
    print("Preloading FPL data...")
    current_gw = fetch_current_gameweek()
    print(f"Current gameweek: {current_gw}")
    
    try:
        data = get_fpl_data(current_gw)
        if data:
            print(f"Successfully loaded gameweek {current_gw}")
        else:
            print(f"Failed to load gameweek {current_gw}")
    except Exception as e:
        print(f"Error loading gameweek {current_gw}: {e}")
    
    print("Data preloading complete!")

def get_latest_valid_gameweek():
    """Find the latest gameweek that has valid data (not all zeros)."""
    current_gw = fetch_current_gameweek()
    
    # Try current gameweek first
    data = get_fpl_data(current_gw)
    if data and any(team['gw_points'] > 0 for team in data['standings']):
        return current_gw
    
    # If current gameweek has no data, check previous gameweeks
    for gameweek in range(current_gw - 1, 0, -1):
        data = get_fpl_data(gameweek)
        if data and any(team['gw_points'] > 0 for team in data['standings']):
            return gameweek
    
    return 1  # Default to gameweek 1 if no valid data found

class FPLHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        """Handle HEAD requests."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            # Serve the main HTML page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('index.html', 'rb') as f:
                self.wfile.write(f.read())
        
        elif path == '/styles.css':
            # Serve CSS file
            self.send_response(200)
            self.send_header('Content-type', 'text/css')
            self.end_headers()
            with open('styles.css', 'rb') as f:
                self.wfile.write(f.read())
        
        elif path == '/script.js':
            # Serve JavaScript file
            self.send_response(200)
            self.send_header('Content-type', 'application/javascript')
            self.end_headers()
            with open('script.js', 'rb') as f:
                self.wfile.write(f.read())
        
        elif path == '/api/current-gameweek':
            # Return latest gameweek with valid data
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            latest_gw = get_latest_valid_gameweek()
            self.wfile.write(json.dumps({'current_gameweek': latest_gw}).encode())
        
        elif path == '/api/gameweeks':
            # Return list of available gameweeks
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            gameweeks = list(range(1, 39))  # 1-38
            self.wfile.write(json.dumps(gameweeks).encode())
        
        elif path == '/api/all-data':
            # Return data for all gameweeks
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            all_data = get_all_gameweek_data()
            self.wfile.write(json.dumps(all_data).encode())
        
        elif path.startswith('/api/data/'):
            # Handle data requests
            try:
                gameweek = int(parsed_path.path.split('/')[-1])
                if 1 <= gameweek <= 38:
                    data = get_fpl_data(gameweek)
                    if data:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(data).encode())
                    else:
                        self.send_error(500, "Failed to fetch FPL data")
                else:
                    self.send_error(400, "Invalid gameweek number")
            except ValueError:
                self.send_error(400, "Invalid gameweek format")
        
        else:
            self.send_error(404, "Not found")

def run_server():
    # Initialize database
    print("Initializing database...")
    init_db()
    
    # Create cache directory if it doesn't exist
    os.makedirs('cache', exist_ok=True)
    
    # Preload only current gameweek data
    preload_data()
    
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, FPLHandler)
    print("Server running at http://localhost:8000")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
