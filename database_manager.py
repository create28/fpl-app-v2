import sqlite3
import os
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path='fpl_history.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with self.get_connection() as conn:
            c = conn.cursor()
            
            # Create FPL data table
            c.execute('''CREATE TABLE IF NOT EXISTS fpl_data
                         (gameweek INTEGER, team_id INTEGER, team_name TEXT, 
                          manager_name TEXT, gw_points INTEGER, total_points INTEGER,
                          team_value INTEGER, bank_balance INTEGER,
                          PRIMARY KEY (gameweek, team_id))''')
            
            # Create award winners table
            c.execute('''CREATE TABLE IF NOT EXISTS award_winners
                         (gameweek INTEGER, award_type TEXT, team_id INTEGER,
                          team_name TEXT, manager_name TEXT, points INTEGER,
                          additional_data TEXT,
                          PRIMARY KEY (gameweek, award_type, team_id))''')
            
            # Check if player_performance table exists and has the correct schema
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='player_performance'")
            if c.fetchone():
                # Table exists, check if it has the right schema
                c.execute("PRAGMA table_info(player_performance)")
                columns = [row[1] for row in c.fetchall()]
                expected_columns = ['gameweek', 'team_id', 'player_id', 'player_name', 'position', 'element_type', 'gw_points', 'is_captain', 'chips_used']
                
                if columns == expected_columns:
                    # Schema is correct, no migration needed
                    print("Player performance table exists with correct schema")
                else:
                    # Schema is wrong, need to migrate
                    print("Player performance table has wrong schema, migrating...")
                    # Create new table with correct schema
                    c.execute('''CREATE TABLE player_performance_new
                                 (gameweek INTEGER, team_id INTEGER, player_id INTEGER,
                                  player_name TEXT, position INTEGER, element_type INTEGER,
                                  gw_points INTEGER, is_captain BOOLEAN, chips_used TEXT,
                                  PRIMARY KEY (gameweek, team_id, player_id))''')
                    
                    # Copy data if possible (only if old table has compatible columns)
                    try:
                        c.execute("INSERT INTO player_performance_new SELECT * FROM player_performance")
                        print("Data migrated successfully")
                    except:
                        print("Could not migrate data, starting fresh")
                    
                    # Drop old table and rename new one
                    c.execute("DROP TABLE player_performance")
                    c.execute("ALTER TABLE player_performance_new RENAME TO player_performance")
                    print("Migration complete")
            else:
                # Table doesn't exist, create it
                print("Creating new player_performance table")
                c.execute('''CREATE TABLE player_performance
                             (gameweek INTEGER, team_id INTEGER, player_id INTEGER,
                              player_name TEXT, position INTEGER, element_type INTEGER,
                              gw_points INTEGER, is_captain BOOLEAN, chips_used TEXT,
                              PRIMARY KEY (gameweek, team_id, player_id))''')
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def save_fpl_data(self, gameweek, teams_data):
        """Save FPL data for a specific gameweek."""
        with self.get_connection() as conn:
            c = conn.cursor()
            for team in teams_data:
                c.execute('''INSERT OR REPLACE INTO fpl_data 
                             (gameweek, team_id, team_name, manager_name, gw_points, 
                              total_points, team_value, bank_balance)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (gameweek, team['team_id'], team['team_name'], 
                           team['manager_name'], team['gw_points'], team['total_points'],
                           team['team_value'], team['bank_balance']))
            conn.commit()
    
    def save_award_winners(self, gameweek, awards_data):
        """Save award winners for a specific gameweek."""
        with self.get_connection() as conn:
            c = conn.cursor()
            for award_type, winners in awards_data.items():
                if winners:
                    for winner in winners:
                        c.execute('''INSERT OR REPLACE INTO award_winners
                                     (gameweek, award_type, team_id, team_name, 
                                      manager_name, points, additional_data)
                                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                  (gameweek, award_type, winner.get('team_id'),
                                   winner.get('team_name'), winner.get('manager_name'),
                                   winner.get('points'), winner.get('details', '')))
            conn.commit()
    
    def save_player_performance(self, gameweek, team_id, players_data):
        """Save player performance data for a team in a gameweek."""
        with self.get_connection() as conn:
            c = conn.cursor()
            print(f"Attempting to save {len(players_data)} players for team {team_id} in gameweek {gameweek}")
            for i, player in enumerate(players_data):
                try:
                    c.execute('''INSERT OR REPLACE INTO player_performance
                                 (gameweek, team_id, player_id, player_name, position,
                                  element_type, gw_points, is_captain, chips_used)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                              (gameweek, team_id, player.get('player_id'), player.get('player_name'),
                               player.get('position'), player.get('element_type'),
                               player.get('gw_points'), player.get('is_captain', False),
                               player.get('chips_used', '')))
                    if i == 0:  # Log first player for debugging
                        print(f"  First player data: {player}")
                except Exception as e:
                    print(f"  Error saving player {i}: {e}")
                    print(f"  Player data: {player}")
            conn.commit()
            print(f"  Committed {len(players_data)} players to database")
    
    def get_fpl_data(self, gameweek):
        """Get FPL data for a specific gameweek."""
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('''SELECT team_id, team_name, manager_name, gw_points, 
                                total_points, team_value, bank_balance 
                         FROM fpl_data WHERE gameweek = ?''', (gameweek,))
            rows = c.fetchall()
            
            if not rows:
                return None
            
            teams = []
            for row in rows:
                teams.append({
                    'team_id': row[0],
                    'team_name': row[1],
                    'manager_name': row[2],
                    'gw_points': row[3],
                    'total_points': row[4],
                    'team_value': row[5],
                    'bank_balance': row[6]
                })
            
            return teams
    
    def get_awards(self, gameweek):
        """Get awards for a specific gameweek."""
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('''SELECT award_type, team_id, team_name, manager_name, 
                                points, additional_data 
                         FROM award_winners WHERE gameweek = ?''', (gameweek,))
            rows = c.fetchall()
            
            awards = {}
            for row in rows:
                award_type, team_id, team_name, manager_name, points, additional_data = row
                if award_type not in awards:
                    awards[award_type] = []
                
                awards[award_type].append({
                    'team_id': team_id,
                    'team_name': team_name,
                    'manager_name': manager_name,
                    'points': points,
                    'details': additional_data
                })
            
            return awards
    
    def get_previous_gameweek_data(self, gameweek):
        """Get data from the previous gameweek for rank change calculations."""
        if gameweek <= 1:
            return {}
        
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('''SELECT team_id, total_points, gw_points 
                         FROM fpl_data WHERE gameweek = ?''', (gameweek - 1,))
            rows = c.fetchall()
            
            previous_data = {}
            for row in rows:
                previous_data[row[0]] = {
                    'total_points': row[1],
                    'gw_points': row[2]
                }
            
            return previous_data
    
    def get_available_gameweeks(self):
        """Get list of available gameweeks in the database."""
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('''SELECT DISTINCT gameweek FROM fpl_data ORDER BY gameweek''')
            rows = c.fetchall()
            return [row[0] for row in rows]

# Global database manager instance
db_manager = DatabaseManager()

