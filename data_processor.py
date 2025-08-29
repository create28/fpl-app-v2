from database_manager import db_manager

class DataProcessor:
    def __init__(self):
        pass
    
    def calculate_overall_rankings(self, teams, gameweek):
        """Calculate overall league rankings based on total points."""
        if not teams:
            return []
        
        # Sort teams by total points (descending)
        sorted_teams = sorted(teams, key=lambda x: x['total_points'], reverse=True)
        
        # Assign ranks (handling ties with same rank)
        current_rank = 1
        for i, team in enumerate(sorted_teams):
            if i > 0 and team['total_points'] < sorted_teams[i-1]['total_points']:
                current_rank = i + 1
            team['overall_rank'] = current_rank
        
        print(f"Overall league rankings for gameweek {gameweek}:")
        for i, team in enumerate(sorted_teams[:5]):  # Show top 5
            print(f"  Rank {team['overall_rank']}: {team['team_name']} - {team['total_points']} total points (GW: {team['gw_points']})")
        
        return sorted_teams
    
    def calculate_rank_changes(self, teams, gameweek):
        """Calculate rank changes from previous gameweek."""
        if gameweek <= 1:
            print("No previous gameweek data for rank change calculation")
            return
        
        # Get previous gameweek data
        previous_data = db_manager.get_previous_gameweek_data(gameweek)
        if not previous_data:
            print("No previous gameweek data for rank change calculation")
            return
        
        print("Found previous gameweek data for rank change calculation")
        
        # Calculate rank changes
        for team in teams:
            if team['team_id'] in previous_data:
                prev_rank = previous_data[team['team_id']].get('overall_rank', 0)
                if prev_rank > 0:
                    rank_change = prev_rank - team['overall_rank']
                    team['rank_change'] = rank_change
                else:
                    team['rank_change'] = 0
            else:
                team['rank_change'] = 0
        
        # Show top 5 rank changes
        top_teams = sorted(teams, key=lambda x: x['overall_rank'])[:5]
        print("Overall league rank changes for gameweek {}:".format(gameweek))
        print("  Top 5 teams:")
        for team in top_teams:
            change_symbol = "↑" if team['rank_change'] > 0 else "↓" if team['rank_change'] < 0 else "−"
            change_text = f"{change_symbol}+{abs(team['rank_change'])}" if team['rank_change'] != 0 else "−0"
            print(f"    {team['overall_rank']}. {team['team_name']:<20} {change_text} (was {team['overall_rank'] + team['rank_change']:2d})")
        
        # Show biggest risers and fallers
        risers = [t for t in teams if t['rank_change'] > 0]
        fallers = [t for t in teams if t['rank_change'] < 0]
        
        if risers:
            biggest_risers = sorted(risers, key=lambda x: x['rank_change'], reverse=True)[:3]
            print("  Biggest risers:")
            for team in biggest_risers:
                print(f"    ↑+{team['rank_change']} {team['team_name']} ({team['overall_rank'] + team['rank_change']} → {team['overall_rank']})")
        
        if fallers:
            biggest_fallers = sorted(fallers, key=lambda x: abs(x['rank_change']))[:3]
            print("  Biggest fallers:")
            for team in biggest_fallers:
                print(f"    ↓-{abs(team['rank_change'])} {team['team_name']} ({team['overall_rank'] - team['rank_change']} → {team['overall_rank']})")
    
    def process_team_awards(self, teams, awards):
        """Process awards and attach them to teams for frontend display."""
        print(f"Processing team awards from database...")
        print(f"Teams count: {len(teams)}")
        print(f"Awards: {list(awards.keys())}")
        
        # Ensure all award types exist (even if empty)
        for award_type in ['weekly_champion', 'wooden_spoon', 'performance_of_week', 'the_wall', 'benchwarmer', 'captain_fantastic']:
            if award_type not in awards:
                awards[award_type] = []
        
        # Create team_id to awards mapping
        team_id_to_awards = {}
        def add_award(team_award_map, award_list, award_type):
            for a in award_list or []:
                tid = a.get('team_id')
                if not tid:
                    print(f"Warning: Award {award_type} missing team_id for {a.get('team_name', 'Unknown')}")
                    continue
                team_award_map.setdefault(tid, []).append(award_type)
                print(f"Added award {award_type} to team {tid}")
        
        add_award(team_id_to_awards, awards.get('weekly_champion'), 'weekly_champion')
        add_award(team_id_to_awards, awards.get('wooden_spoon'), 'wooden_spoon')
        add_award(team_id_to_awards, awards.get('performance_of_week'), 'performance_of_week')
        add_award(team_id_to_awards, awards.get('the_wall'), 'the_wall')
        add_award(team_id_to_awards, awards.get('benchwarmer'), 'benchwarmer')
        add_award(team_id_to_awards, awards.get('captain_fantastic'), 'captain_fantastic')
        
        print(f"Team ID to awards mapping: {team_id_to_awards}")
        
        # Helper mappings for badge metadata
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
        
        # Attach awards to each team
        for team in teams:
            awards_for_team = []
            team_awards = team_id_to_awards.get(team['team_id'], [])
            print(f"Team {team['team_name']} (ID: {team['team_id']}) has awards: {team_awards}")
            
            for a_type in team_awards:
                awards_for_team.append({
                    'type': a_type,
                    'emoji': award_emojis.get(a_type, '🏆'),
                    'color': award_colors.get(a_type, 'bg-gray-300 text-gray-800 border-gray-200'),
                    'text': a_type.replace('_', ' ').title()
                })
            
            team['awards'] = awards_for_team
            print(f"  Final awards for {team['team_name']}: {len(awards_for_team)} awards")
        
        # Count teams with awards
        teams_with_awards = [t for t in teams if t.get('awards') and len(t['awards']) > 0]
        print(f"Teams with awards after processing: {len(teams_with_awards)}/{len(teams)}")
        
        return teams
    
    def get_fpl_data(self, gameweek):
        """Get FPL data for a specific gameweek with rankings and awards."""
        try:
            print(f"Getting data for gameweek {gameweek} from database...")
            
            # Get teams data from database
            teams = db_manager.get_fpl_data(gameweek)
            if not teams:
                print(f"No data found in database for gameweek {gameweek}")
                return None
            
            print(f"Found {len(teams)} teams in database for gameweek {gameweek}")
            
            # Calculate overall rankings
            print(f"Calculating overall league rankings for gameweek {gameweek}...")
            teams = self.calculate_overall_rankings(teams, gameweek)
            
            # Calculate rank changes
            self.calculate_rank_changes(teams, gameweek)
            
            # Get stored awards directly from database
            print(f"Reading stored awards for gameweek {gameweek} from database...")
            awards = db_manager.get_awards(gameweek)
            
            # Ensure all award types exist (even if empty)
            for award_type in ['weekly_champion', 'wooden_spoon', 'performance_of_week', 'the_wall', 'benchwarmer', 'captain_fantastic']:
                if award_type not in awards:
                    awards[award_type] = []
            
            print(f"Successfully processed data for gameweek {gameweek}")
            
            # Process awards and attach to teams
            teams = self.process_team_awards(teams, awards)
            
            return teams
            
        except Exception as e:
            print(f"Error getting data for gameweek {gameweek}: {e}")
            import traceback
            traceback.print_exc()
            return None

# Global data processor instance
data_processor = DataProcessor()
