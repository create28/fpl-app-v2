from database_manager import db_manager

class AwardsCalculator:
    def __init__(self):
        pass
    
    def calculate_basic_awards(self, teams, gameweek):
        """Calculate basic awards (weekly champion, wooden spoon)."""
        if not teams:
            return {}
        
        # Weekly Champion (highest gameweek points)
        max_points = max(team['gw_points'] for team in teams)
        weekly_champions = [team for team in teams if team['gw_points'] == max_points]
        
        # Wooden Spoon (lowest gameweek points)
        min_points = min(team['gw_points'] for team in teams)
        wooden_spoons = [team for team in teams if team['gw_points'] == min_points]
        
        return {
            'weekly_champion': [{
                'team_id': champ['team_id'],
                'team_name': champ['team_name'],
                'manager_name': champ['manager_name'],
                'points': champ['gw_points']
            } for champ in weekly_champions],
            'wooden_spoon': [{
                'team_id': spoon['team_id'],
                'team_name': spoon['team_name'],
                'manager_name': spoon['manager_name'],
                'points': spoon['gw_points']
            } for spoon in wooden_spoons]
        }
    
    def calculate_performance_of_week(self, gameweek, current_data, previous_data):
        """Calculate Performance of the Week based on gw_points delta from previous week."""
        if not previous_data:
            return []
        
        # Filter out teams with 0 points in current gameweek
        valid_current_teams = [team for team in current_data if team['gw_points'] > 0]
        if not valid_current_teams:
            return []
        
        improvements = []
        for current_team in valid_current_teams:
            if current_team['team_id'] in previous_data:
                prev = previous_data[current_team['team_id']]
                previous_gw_points = prev.get('gw_points', 0)
                # Calculate improvement: current GW points - previous GW points
                improvement = current_team['gw_points'] - previous_gw_points
                improvements.append((current_team, improvement))

        if not improvements:
            return []

        # Find the highest positive improvement, if any
        positive_improvements = [imp[1] for imp in improvements if imp[1] > 0]
        if positive_improvements:
            max_improvement = max(positive_improvements)
            champions = [imp for imp in improvements if imp[1] == max_improvement]
        else:
            # If no positive, use the highest (least negative or zero) improvement
            max_improvement = max(imp[1] for imp in improvements)
            champions = [imp for imp in improvements if imp[1] == max_improvement]

        return [{
            'team_id': champ[0]['team_id'],
            'team_name': champ[0]['team_name'],
            'manager_name': champ[0]['manager_name'],
            'points': champ[1]  # This is the difference
        } for champ in champions]
    
    def calculate_detailed_awards(self, teams_data, gameweek):
        """Calculate detailed awards (The Wall, Benchwarmer, Captain Fantastic)."""
        wall_scores = []
        benchwarmer_scores = []
        captain_scores = []
        
        print(f"Calculating detailed awards for gameweek {gameweek}...")
        
        # Check if we have any player performance data for this gameweek
        has_player_data = self._check_player_data_availability(gameweek)
        if not has_player_data:
            print(f"No player performance data available for gameweek {gameweek}, creating fallback awards")
            # Create fallback awards based on team performance
            return self._create_fallback_awards(teams_data, gameweek)
        
        for i, team in enumerate(teams_data):
            team_id = team['team_id']
            print(f"Processing team {i+1}/{len(teams_data)}: {team['team_name']}")
            
            # Get detailed team data from database
            detailed_data = self._get_team_detailed_data(team_id, gameweek)
            if not detailed_data:
                print(f"  Skipping {team['team_name']} - no detailed data")
                continue
            
            # Calculate The Wall award (GKP + DEF points from starting XI positions 1-11)
            wall_points = self._calculate_wall_points(detailed_data)
            if wall_points:
                wall_scores.append({
                    'team_id': team_id,
                    'team_name': team['team_name'],
                    'manager_name': team['manager_name'],
                    'points': wall_points['total'],
                    'details': wall_points['details']
                })
                print(f"  The Wall: {wall_points['total']} points ({wall_points['details']})")
            
            # Calculate Benchwarmer award (bench points from squad positions 12-15)
            bench_points = self._calculate_benchwarmer_points(detailed_data)
            if bench_points and bench_points['total'] > 0:
                benchwarmer_scores.append({
                    'team_id': team_id,
                    'team_name': team['team_name'],
                    'manager_name': team['manager_name'],
                    'points': bench_points['total'],
                    'details': bench_points['details']
                })
                print(f"  Benchwarmer: {bench_points['total']} points ({bench_points['details']})")
            
            # Calculate Captain Fantastic award
            captain_points = self._calculate_captain_points(detailed_data)
            if captain_points and captain_points['total'] > 0:
                captain_scores.append({
                    'team_id': team_id,
                    'team_name': team['team_name'],
                    'manager_name': team['manager_name'],
                    'points': captain_points['total'],
                    'details': captain_points['details']
                })
                print(f"  Captain Fantastic: {captain_points['total']} points ({captain_points['details']})")
        
        # Find winners
        awards = {}
        if wall_scores:
            max_wall = max(wall_scores, key=lambda x: x['points'])
            awards['the_wall'] = [w for w in wall_scores if w['points'] == max_wall['points']]
            print(f"The Wall winner(s): {[w['team_name'] for w in awards['the_wall']]} with {max_wall['points']} points")
        
        if benchwarmer_scores:
            max_bench = max(benchwarmer_scores, key=lambda x: x['points'])
            awards['benchwarmer'] = [w for w in benchwarmer_scores if w['points'] == max_bench['points']]
            print(f"Benchwarmer winner(s): {[w['team_name'] for w in awards['benchwarmer']]} with {max_bench['points']} points")
        
        if captain_scores:
            max_captain = max(captain_scores, key=lambda x: x['points'])
            awards['captain_fantastic'] = [w for w in captain_scores if w['points'] == max_captain['points']]
            print(f"Captain Fantastic winner(s): {[w['team_name'] for w in awards['captain_fantastic']]} with {max_captain['points']} points")
        
        print(f"Award calculation complete for gameweek {gameweek}")
        return awards
    
    def _create_fallback_awards(self, teams_data, gameweek):
        """Create fallback awards when player performance data is not available."""
        print(f"Creating fallback awards for gameweek {gameweek}")
        
        # Sort teams by gameweek points
        sorted_teams = sorted(teams_data, key=lambda x: x['gw_points'], reverse=True)
        
        awards = {}
        
        # The Wall: Best defensive performance (lowest goals conceded, or highest clean sheet bonus)
        # Since we don't have detailed data, award to team with highest gameweek points
        if sorted_teams:
            wall_winner = sorted_teams[0]
            awards['the_wall'] = [{
                'team_id': wall_winner['team_id'],
                'team_name': wall_winner['team_name'],
                'manager_name': wall_winner['manager_name'],
                'points': wall_winner['gw_points'],
                'details': 'Fallback: Highest gameweek points'
            }]
            print(f"Fallback The Wall: {wall_winner['team_name']} with {wall_winner['gw_points']} points")
        
        # Benchwarmer: Team with most points from bench (approximate using team value efficiency)
        if len(sorted_teams) > 1:
            # Find team with best points-to-value ratio (efficient use of budget)
            efficiency_scores = []
            for team in teams_data:
                if team['team_value'] > 0:
                    efficiency = team['gw_points'] / team['team_value']
                    efficiency_scores.append((team, efficiency))
            
            if efficiency_scores:
                best_efficiency = max(efficiency_scores, key=lambda x: x[1])
                awards['benchwarmer'] = [{
                    'team_id': best_efficiency[0]['team_id'],
                    'team_name': best_efficiency[0]['team_name'],
                    'manager_name': best_efficiency[0]['manager_name'],
                    'points': best_efficiency[0]['gw_points'],
                    'details': f'Fallback: Best efficiency ({best_efficiency[1]:.2f} points/£m)'
                }]
                print(f"Fallback Benchwarmer: {best_efficiency[0]['team_name']} with efficiency {best_efficiency[1]:.2f}")
        
        # Captain Fantastic: Team with best captain choice (approximate using overall performance)
        if len(sorted_teams) > 2:
            # Award to team with best improvement from previous week (if available)
            # For now, award to team with second-highest points
            captain_winner = sorted_teams[1] if len(sorted_teams) > 1 else sorted_teams[0]
            awards['captain_fantastic'] = [{
                'team_id': captain_winner['team_id'],
                'team_name': captain_winner['team_name'],
                'manager_name': captain_winner['manager_name'],
                'points': captain_winner['gw_points'],
                'details': 'Fallback: Strong gameweek performance'
            }]
            print(f"Fallback Captain Fantastic: {captain_winner['team_name']} with {captain_winner['gw_points']} points")
        
        print(f"Fallback awards created for gameweek {gameweek}")
        return awards
    
    def _check_player_data_availability(self, gameweek):
        """Check if player performance data is available for a gameweek."""
        with db_manager.get_connection() as conn:
            c = conn.cursor()
            c.execute('''SELECT COUNT(*) FROM player_performance WHERE gameweek = ?''', (gameweek,))
            count = c.fetchone()[0]
            return count > 0
    
    def _get_team_detailed_data(self, team_id, gameweek):
        """Get detailed team data from database."""
        with db_manager.get_connection() as conn:
            c = conn.cursor()
            c.execute('''SELECT player_id, player_name, position, element_type, 
                                gw_points, is_captain, chips_used
                         FROM player_performance 
                         WHERE gameweek = ? AND team_id = ?''', (gameweek, team_id))
            rows = c.fetchall()
            
            if not rows:
                return None
            
            players = []
            for row in rows:
                players.append({
                    'id': row[0],
                    'name': row[1],
                    'position': row[2],
                    'element_type': row[3],
                    'gw_points': row[4],
                    'is_captain': bool(row[5]),
                    'chips_used': row[6] or ''
                })
            
            return {'starting_xi': players}
    
    def _calculate_wall_points(self, detailed_data):
        """Calculate The Wall points (GKP + DEF from starting XI)."""
        wall_points = 0
        gkp_def_players = []
        gkp_count = 0
        def_count = 0
        
        for player in detailed_data['starting_xi']:
            # Only count players in starting XI positions 1-11 AND with element_type 1 (GKP) or 2 (DEF)
            if player['position'] <= 11 and player['element_type'] in [1, 2]:
                wall_points += player['gw_points']
                position_name = "GKP" if player['element_type'] == 1 else "DEF"
                gkp_def_players.append(f"{position_name}:{player['gw_points']}")
                if player['element_type'] == 1:
                    gkp_count += 1
                else:
                    def_count += 1
        
        if wall_points > 0:
            return {
                'total': wall_points,
                'details': f"GKP+DEF: {', '.join(gkp_def_players)} ({gkp_count} GKP, {def_count} DEF)"
            }
        return None
    
    def _calculate_benchwarmer_points(self, detailed_data):
        """Calculate Benchwarmer points (bench players)."""
        if detailed_data.get('chips_used') == 'bboost':  # Exclude bench boost
            return None
        
        bench_points = 0
        bench_players = []
        bench_count = 0
        
        for player in detailed_data['starting_xi']:
            # Only count players in squad positions 12-15 (bench players)
            if player['position'] >= 12 and player['position'] <= 15:
                bench_points += player['gw_points']
                bench_players.append(f"B{player['position']}:{player['gw_points']}")
                bench_count += 1
        
        if bench_count > 0:
            return {
                'total': bench_points,
                'details': f"Bench: {', '.join(bench_players)} ({bench_count} players)"
            }
        return None
    
    def _calculate_captain_points(self, detailed_data):
        """Calculate Captain Fantastic points."""
        for player in detailed_data['starting_xi']:
            if player['is_captain']:
                base_points = player['gw_points']
                # Both regular captain and triple captain use 2x multiplier
                captain_points = base_points * 2
                if detailed_data.get('chips_used') == '3xc':  # Triple captain
                    details = f"3x Captain: {base_points} × 2 = {captain_points}"
                else:
                    details = f"Captain: {base_points} × 2 = {captain_points}"
                
                return {
                    'total': captain_points,
                    'details': details
                }
        return None

# Global awards calculator instance
awards_calculator = AwardsCalculator()

