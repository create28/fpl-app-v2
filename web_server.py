import json
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from data_processor import data_processor
from database_manager import db_manager
from awards_calculator import awards_calculator
from fpl_api import fpl_api

class FPLRequestHandler(BaseHTTPRequestHandler):
    
    def end_headers(self):
        """Add CORS headers to all responses."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight CORS requests."""
        self.send_response(200)
        self.end_headers()

    def send_json(self, status_code, payload):
        """Send a JSON response with the given status code and payload."""
        try:
            self.send_response(status_code)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode('utf-8'))
        except Exception:
            # As a last resort, avoid crashing the handler
            try:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Internal Server Error')
            except Exception:
                pass
    def do_GET(self):
        """Handle GET requests."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        print(f"Received request for path: {path}")
        
        try:
            if path.startswith('/api/data/'):
                # Extract gameweek from path
                gameweek = int(path.split('/')[-1])
                data = self.get_simple_data(gameweek)
                
                if data:
                    self.send_json(200, data)
                    print(f"Successfully sent data for gameweek {gameweek}")
                else:
                    self.send_json(404, {'status': 'error', 'message': f'No data found for gameweek {gameweek}'})
            
            elif path.startswith('/api/refresh/'):
                # Refresh data for a specific gameweek
                gameweek = int(path.split('/')[-1])
                success = self.refresh_gameweek_data(gameweek)
                
                if success:
                    self.send_json(200, {'status': 'success', 'message': f'Data refreshed for gameweek {gameweek}'})
                else:
                    self.send_json(500, {'status': 'error', 'message': f'Failed to refresh data for gameweek {gameweek}'})
            
            elif path.startswith('/api/calculate-awards/'):
                # Calculate awards for a specific gameweek
                gameweek = int(path.split('/')[-1])
                success = self.calculate_gameweek_awards(gameweek)
                
                if success:
                    self.send_json(200, {'status': 'success', 'message': f'Awards calculated for gameweek {gameweek}'})
                else:
                    self.send_json(500, {'status': 'error', 'message': f'Failed to calculate awards for gameweek {gameweek}'})
            
            elif path.startswith('/api/gameweeks'):
                # Get available gameweeks from DB and include current gameweek if newer
                gameweeks = db_manager.get_available_gameweeks()
                try:
                    current_gameweek = fpl_api.get_current_gameweek()
                    if current_gameweek and (current_gameweek not in gameweeks):
                        gameweeks.append(current_gameweek)
                        gameweeks = sorted(set(gameweeks))
                except Exception:
                    pass
                
                self.send_json(200, {'gameweeks': gameweeks})
            
            elif path == '/api/current-gameweek':
                # Get current gameweek
                current_gameweek = fpl_api.get_current_gameweek()
                if current_gameweek is None:
                    self.send_json(500, {'status': 'error', 'message': 'Could not determine current gameweek'})
                else:
                    self.send_json(200, {'current_gameweek': current_gameweek})
            
            elif path == '/api/refresh-data':
                # Refresh data for current gameweek
                current_gameweek = fpl_api.get_current_gameweek()
                if current_gameweek:
                    success = self.refresh_gameweek_data(current_gameweek)
                    if success:
                        # Calculate awards after refresh
                        self.calculate_gameweek_awards(current_gameweek)
                        
                        self.send_json(200, {'status': 'success', 'message': f'Data refreshed for gameweek {current_gameweek}'})
                    else:
                        self.send_json(500, {'status': 'error', 'message': f'Failed to refresh data for gameweek {current_gameweek}'})
                else:
                    self.send_json(500, {'status': 'error', 'message': 'Could not determine current gameweek'})
            
            elif path.startswith('/api/fetch-players/'):
                # Fetch player data for a specific gameweek (manual trigger)
                gameweek = int(path.split('/')[-1])
                success = self.fetch_player_data_for_gameweek(gameweek)
                
                if success:
                    # Recalculate awards now that we have player data
                    self.calculate_gameweek_awards(gameweek)
                    
                    self.send_json(200, {'status': 'success', 'message': f'Player data fetched for gameweek {gameweek}. Awards recalculated.'})
                else:
                    self.send_json(500, {'status': 'error', 'message': f'Failed to fetch player data for gameweek {gameweek}'})
            
            elif path.startswith('/api/check-players/'):
                # Check player performance data availability
                gameweek = int(path.split('/')[-1])
                availability = self.check_player_data_availability(gameweek)
                
                self.send_json(200, {'gameweek': gameweek, 'availability': availability})
            
            elif path.startswith('/api/bulk-fetch-players/'):
                # Bulk fetch player performance data
                gameweek = int(path.split('/')[-1])
                success = self.bulk_fetch_player_data(gameweek)
                
                if success:
                    self.send_json(200, {'status': 'success', 'message': f'Player data fetched for gameweek {gameweek}'})
                else:
                    self.send_json(500, {'status': 'error', 'message': f'Failed to fetch player data for gameweek {gameweek}'})
            
            elif path == '/':
                # Serve the main HTML page
                self.serve_static_file('index.html', 'text/html')
            
            elif path == '/health':
                # Simple health check endpoint
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    'status': 'healthy',
                    'service': 'FPL Data Server',
                    'timestamp': str(datetime.now()),
                    'endpoints': [
                        '/api/current-gameweek',
                        '/api/gameweeks',
                        '/api/data/{gameweek}'
                    ]
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
            
            elif path.startswith('/static/'):
                # Serve static files from static directory
                file_path = path[1:]  # Remove leading slash
                if file_path.endswith('.css'):
                    self.serve_static_file(file_path, 'text/css')
                elif file_path.endswith('.js'):
                    self.serve_static_file(file_path, 'application/javascript')
                else:
                    self.serve_static_file(file_path, 'application/octet-stream')
            
            elif path.endswith(('.svg', '.png', '.jpg', '.jpeg', '.gif', '.ico')):
                # Serve image files directly
                self.serve_static_file(path[1:], 'image/svg+xml' if path.endswith('.svg') else 'image/png')
            
            elif path.endswith('.js'):
                # Serve JavaScript files directly
                self.serve_static_file(path[1:], 'application/javascript')
            
            elif path.endswith('.css'):
                # Serve CSS files directly
                self.serve_static_file(path[1:], 'text/css')
            
            else:
                self.send_json(404, {'status': 'error', 'message': 'Endpoint not found'})
        
        except Exception as e:
            print(f"Error handling request: {e}")
            self.send_json(500, {'status': 'error', 'message': f'Internal server error: {str(e)}'})
    
    def serve_static_file(self, file_path, content_type):
        """Serve a static file."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(content)
        
        except FileNotFoundError:
            self.send_error(404, 'File not found')
        except Exception as e:
            self.send_error(500, f'Error reading file: {str(e)}')
    
    def refresh_gameweek_data(self, gameweek):
        """Refresh data for a specific gameweek."""
        try:
            print(f"Refreshing data for gameweek {gameweek}...")
            
            # Get league ID from a known team (you might want to store this)
            league_id = 874353  # FPL League ID
            
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
    
    def fetch_player_data_for_gameweek(self, gameweek):
        """Fetch player performance data for all teams in a gameweek."""
        try:
            print(f"Fetching player data for gameweek {gameweek}...")
            
            # Get all teams for this gameweek
            teams = db_manager.get_fpl_data(gameweek)
            if not teams:
                print(f"No teams found for gameweek {gameweek}")
                return False
            
            total_teams = len(teams)
            successful_fetches = 0
            
            for i, team in enumerate(teams):
                team_id = team['team_id']
                team_name = team['team_name']
                print(f"Processing team {i+1}/{total_teams}: {team_name}")
                
                try:
                    # Get team picks from FPL API
                    picks = fpl_api.get_team_picks(team_id, gameweek)
                    if picks and 'picks' in picks:
                        # Process each player pick
                        players_data = []
                        for pick in picks['picks']:
                            # Get actual player performance data for this gameweek
                            player_performance = fpl_api.get_player_performance(pick['element'], gameweek)
                            
                            # Basic debug logging for first player of first team
                            if i == 0:
                                print(f"    Debug: Processing first player of first team")
                                print(f"    Debug: gameweek={gameweek} (type: {type(gameweek)})")
                                print(f"    Debug: player_id={pick['element']}")
                                print(f"    Debug: player_performance received: {player_performance is not None}")
                                if player_performance:
                                    print(f"    Debug: player_performance keys: {list(player_performance.keys())}")
                                    print(f"    Debug: has history: {'history' in player_performance}")
                                    if 'history' in player_performance:
                                        print(f"    Debug: history count: {len(player_performance['history'])}")
                                        if player_performance['history']:
                                            print(f"    Debug: first history entry: {player_performance['history'][0]}")
                            
                            # Extract points from player performance data
                            gw_points = 0
                            if player_performance and 'history' in player_performance:
                                # Find the specific gameweek in player history
                                for history_entry in player_performance['history']:
                                    if history_entry.get('round') == gameweek:
                                        gw_points = history_entry.get('total_points', 0)
                                        break
                                
                                # Additional debug logging
                                if i == 0 and len(players_data) == 0:
                                    print(f"    Debug: extracted points: {gw_points}")
                            else:
                                # Debug logging for failed API calls
                                if i == 0 and len(players_data) == 0:
                                    print(f"    Debug: Failed to get player performance data")
                                    print(f"    Debug: player_performance: {player_performance}")
                            
                            player_data = {
                                'player_id': pick['element'],
                                'position': pick['position'],
                                'is_captain': pick['is_captain'],
                                'gw_points': gw_points,
                                'chips_used': pick.get('chip', '')
                            }
                            
                            # Get player name and type from bootstrap data
                            player_info = self.get_player_info(pick['element'])
                            if player_info:
                                player_data['player_name'] = player_info['name']
                                player_data['element_type'] = player_info['element_type']
                            else:
                                # Fallback if we can't get player info
                                player_data['player_name'] = f"Player {pick['element']}"
                                player_data['element_type'] = 1  # Default to GKP
                            
                            players_data.append(player_data)
                        
                        # Store in database
                        print(f"  About to call db_manager.save_player_performance for {team_name}")
                        db_manager.save_player_performance(gameweek, team_id, players_data)
                        print(f"  ✓ Saved {len(players_data)} players for {team_name}")
                        successful_fetches += 1
                    else:
                        print(f"  ⚠ No picks data for {team_name}")
                
                except Exception as e:
                    print(f"  ❌ Error processing {team_name}: {e}")
                    continue
                
                # Rate limiting - wait between requests to be respectful to FPL API
                if i < total_teams - 1:  # Don't wait after the last team
                    import time
                    time.sleep(2)  # 2 second delay between teams (increased due to more API calls)
            
            print(f"Player data fetch complete: {successful_fetches}/{total_teams} teams processed successfully")
            return successful_fetches > 0
            
        except Exception as e:
            print(f"Error fetching player data for gameweek {gameweek}: {e}")
            return False
    
    def get_player_info(self, player_id):
        """Get player information from bootstrap data or cache."""
        try:
            # Try to get from bootstrap data (this should be cached)
            bootstrap_data = fpl_api.get_bootstrap_data()
            if bootstrap_data and 'elements' in bootstrap_data:
                for element in bootstrap_data['elements']:
                    if element['id'] == player_id:
                        return {
                            'name': element['web_name'],
                            'element_type': element['element_type']
                        }
            return None
        except Exception as e:
            print(f"Error getting player info for {player_id}: {e}")
            return None
    
    def check_player_data_availability(self, gameweek):
        """Check availability of player performance data."""
        try:
            with db_manager.get_connection() as conn:
                c = conn.cursor()
                c.execute('''SELECT COUNT(*) FROM player_performance WHERE gameweek = ?''', (gameweek,))
                count = c.fetchone()[0]
                
                return {
                    'available': count > 0,
                    'count': count
                }
        
        except Exception as e:
            print(f"Error checking player data availability: {e}")
            return {'available': False, 'count': 0}
    
    def bulk_fetch_player_data(self, gameweek):
        """Bulk fetch player performance data for all teams."""
        try:
            print(f"Bulk fetching player data for gameweek {gameweek}...")
            
            # Get teams for this gameweek
            teams = db_manager.get_fpl_data(gameweek)
            if not teams:
                print(f"No teams found for gameweek {gameweek}")
                return False
            
            # Fetch player data for each team
            for team in teams:
                team_id = team['team_id']
                print(f"Fetching player data for team {team['team_name']} (ID: {team_id})")
                
                # Get team details from FPL API
                team_details = fpl_api.get_team_details(team_id, gameweek)
                if team_details and 'picks' in team_details:
                    picks = team_details['picks']
                    
                    # Process and save player data
                    players_data = []
                    for pick in picks:
                        player_data = {
                            'id': pick['element'],
                            'name': pick.get('name', 'Unknown'),
                            'position': pick['position'],
                            'element_type': pick.get('element_type', 0),
                            'gw_points': pick.get('stats', {}).get('total_points', 0),
                            'is_captain': pick.get('is_captain', False),
                            'chips_used': team_details.get('active_chip', '')
                        }
                        players_data.append(player_data)
                    
                    # Save to database
                    db_manager.save_player_performance(gameweek, team_id, players_data)
                    print(f"Saved player data for {len(players_data)} players")
                
                else:
                    print(f"No player data found for team {team['team_name']}")
            
            print(f"Successfully bulk fetched player data for gameweek {gameweek}")
            return True
        
        except Exception as e:
            print(f"Error bulk fetching player data: {e}")
            return False
    
    def log_message(self, format, *args):
        """Override to reduce logging noise."""
        pass

    def get_simple_data(self, gameweek):
        """Get FPL data with awards directly from database."""
        try:
            import sqlite3
            
            # Get team data
            conn = sqlite3.connect('fpl_history.db')
            c = conn.cursor()
            
            # Get teams
            c.execute('''SELECT team_id, team_name, manager_name, gw_points, total_points, team_value, bank_balance
                         FROM fpl_data WHERE gameweek = ?''', (gameweek,))
            teams_data = c.fetchall()
            
            if not teams_data:
                conn.close()
                return None
            
            teams = []
            for row in teams_data:
                teams.append({
                    'team_id': row[0],
                    'team_name': row[1], 
                    'manager_name': row[2],
                    'gw_points': row[3],
                    'total_points': row[4],
                    'team_value': row[5],
                    'bank_balance': row[6],
                    'overall_rank': 1,  # Will be calculated
                    'rank_change': 0,
                    'awards': []  # Will be populated
                })
            
            # Sort by total points and assign ranks
            teams = sorted(teams, key=lambda x: x['total_points'], reverse=True)
            current_rank = 1
            for i, team in enumerate(teams):
                if i > 0 and team['total_points'] < teams[i-1]['total_points']:
                    current_rank = i + 1
                team['overall_rank'] = current_rank
            
            # Calculate rank changes from previous gameweek
            if gameweek > 1:
                c.execute('''SELECT team_id, total_points FROM fpl_data WHERE gameweek = ?''', (gameweek - 1,))
                prev_data = c.fetchall()
                prev_teams = []
                for row in prev_data:
                    prev_teams.append({'team_id': row[0], 'total_points': row[1]})
                
                # Sort previous teams and assign ranks
                prev_teams = sorted(prev_teams, key=lambda x: x['total_points'], reverse=True)
                prev_rank = 1
                for i, prev_team in enumerate(prev_teams):
                    if i > 0 and prev_team['total_points'] < prev_teams[i-1]['total_points']:
                        prev_rank = i + 1
                    prev_team['overall_rank'] = prev_rank
                
                # Create mapping for previous ranks
                prev_ranks = {team['team_id']: team['overall_rank'] for team in prev_teams}
                
                # Calculate rank changes
                for team in teams:
                    if team['team_id'] in prev_ranks:
                        team['rank_change'] = prev_ranks[team['team_id']] - team['overall_rank']
                    else:
                        team['rank_change'] = 0
            
            # Get awards from database
            c.execute('''SELECT award_type, team_id, team_name, manager_name, points
                         FROM award_winners WHERE gameweek = ?''', (gameweek,))
            awards_data = c.fetchall()
            
            # Create team_id to awards mapping
            team_awards = {}
            award_emojis = {
                'weekly_champion': '👑',
                'wooden_spoon': '🥄', 
                'performance_of_week': '🚀',
                'the_wall': '🧱',
                'benchwarmer': '🪑',
                'captain_fantastic': '⭐'
            }
            award_colors = {
                'weekly_champion': 'bg-yellow-400 text-white border-yellow-300',
                'wooden_spoon': 'bg-red-500 text-white border-red-300',
                'performance_of_week': 'bg-indigo-500 text-white border-indigo-300',
                'the_wall': 'bg-green-500 text-white border-green-300',
                'benchwarmer': 'bg-purple-500 text-white border-purple-300',
                'captain_fantastic': 'bg-slate-800 text-white border-slate-600'
            }
            
            for award_type, team_id, team_name, manager_name, points in awards_data:
                if team_id not in team_awards:
                    team_awards[team_id] = []
                
                team_awards[team_id].append({
                    'type': award_type,
                    'emoji': award_emojis.get(award_type, '🏆'),
                    'color': award_colors.get(award_type, 'bg-gray-300 text-gray-800 border-gray-200'),
                    'text': award_type.replace('_', ' ').title()
                })
            
            # Attach awards to teams
            for team in teams:
                team['awards'] = team_awards.get(team['team_id'], [])
            
            conn.close()
            
            # Create awards summary for frontend
            awards_summary = {}
            for award_type, team_id, team_name, manager_name, points in awards_data:
                if award_type not in awards_summary:
                    awards_summary[award_type] = []
                awards_summary[award_type].append({
                    'team_id': team_id,
                    'team_name': team_name,
                    'manager_name': manager_name,
                    'points': points
                })
            
            print(f"Successfully processed data for gameweek {gameweek}")
            teams_with_awards = [t for t in teams if t.get('awards') and len(t['awards']) > 0]
            print(f"Teams with awards: {len(teams_with_awards)}/{len(teams)}")
            
            return {
                'standings': teams,
                'awards': awards_summary
            }
            
        except Exception as e:
            print(f"Error getting simple data for gameweek {gameweek}: {e}")
            return None

def start_server(port=8000):
    """Start the HTTP server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, FPLRequestHandler)
    print(f"Starting server on port {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    start_server()
