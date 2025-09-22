import json
from database_manager import db_manager

def export_gameweek(gameweek: int) -> dict:
    """Export standings and awards for a gameweek from the local database."""
    teams = db_manager.get_fpl_data(gameweek)
    awards = db_manager.get_award_winners(gameweek)
    return {
        'gameweek': gameweek,
        'standings': teams or [],
        'awards': awards or {}
    }

def save_export(gameweek: int, path: str) -> None:
    data = export_gameweek(gameweek)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('Usage: python data_export_import.py <gameweek> <output.json>')
        sys.exit(1)
    gw = int(sys.argv[1])
    out = sys.argv[2]
    save_export(gw, out)
    print(f'Exported GW{gw} to {out}')



