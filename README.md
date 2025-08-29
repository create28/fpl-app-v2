# FPL Data Server - Modular Architecture

This is a modular rewrite of the FPL Data Server, broken down into smaller, more manageable Python files for easier development and maintenance.

## Project Structure

```
14 FPL Updated/
├── main.py                 # Main application entry point
├── database_manager.py     # Database operations and management
├── fpl_api.py             # FPL API interactions
├── awards_calculator.py   # Award calculation logic
├── data_processor.py      # Data processing and rankings
├── web_server.py          # HTTP server and API endpoints
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── index.html            # Frontend HTML
├── script.js             # Frontend JavaScript
└── fpl_history.db        # SQLite database
```

## Module Descriptions

### `main.py`
- **Purpose**: Main application orchestrator
- **Responsibilities**: 
  - Start/stop the server
  - Manage periodic data refresh
  - Coordinate between modules
- **Dependencies**: All other modules

### `database_manager.py`
- **Purpose**: Database operations
- **Responsibilities**:
  - Database initialization and connection management
  - CRUD operations for FPL data, awards, and player performance
  - Data retrieval for rankings and calculations
- **Dependencies**: None (uses sqlite3 from standard library)

### `fpl_api.py`
- **Purpose**: External FPL API interactions
- **Responsibilities**:
  - Fetch data from FPL API endpoints
  - Handle retry logic and error handling
  - API response processing
- **Dependencies**: `requests` library

### `awards_calculator.py`
- **Purpose**: Award calculation logic
- **Responsibilities**:
  - Calculate basic awards (weekly champion, wooden spoon)
  - Calculate detailed awards (The Wall, Benchwarmer, Captain Fantastic)
  - Calculate Performance of the Week
- **Dependencies**: `database_manager`

### `data_processor.py`
- **Purpose**: Data processing and rankings
- **Responsibilities**:
  - Calculate overall league rankings
  - Calculate rank changes between gameweeks
  - Process awards and attach them to teams
  - Main data retrieval function
- **Dependencies**: `database_manager`, `awards_calculator`

### `web_server.py`
- **Purpose**: HTTP server and API endpoints
- **Responsibilities**:
  - Serve HTTP requests
  - Handle API endpoints
  - Serve static files (HTML, CSS, JS)
  - Coordinate data operations
- **Dependencies**: `data_processor`, `database_manager`, `awards_calculator`, `fpl_api`

## Benefits of This Structure

1. **Easier to Navigate**: Each file has a single, clear responsibility
2. **Better for Cursor**: Smaller files are easier to work with in Cursor
3. **Easier Debugging**: Issues can be isolated to specific modules
4. **Better Testing**: Each module can be tested independently
5. **Easier Maintenance**: Changes to one area don't affect others
6. **Clear Dependencies**: Import statements show module relationships

## Running the Application

### Option 1: Run the main application
```bash
python3 main.py
```

### Option 2: Run just the web server
```bash
python3 web_server.py
```

### Option 3: Run individual modules for testing
```bash
python3 -c "from database_manager import db_manager; print('Database manager loaded successfully')"
```

## Development Workflow

1. **Database Changes**: Modify `database_manager.py`
2. **API Changes**: Modify `fpl_api.py`
3. **Award Logic**: Modify `awards_calculator.py`
4. **Data Processing**: Modify `data_processor.py`
5. **Web Endpoints**: Modify `web_server.py`
6. **Main Logic**: Modify `main.py`

## Troubleshooting

- **Import Errors**: Ensure all modules are in the same directory
- **Database Issues**: Check `database_manager.py` for connection problems
- **API Issues**: Check `fpl_api.py` for network or authentication problems
- **Award Issues**: Check `awards_calculator.py` for calculation logic problems

## Future Improvements

- Add configuration files for database paths, API keys, etc.
- Add logging to each module
- Add unit tests for each module
- Add error handling and recovery mechanisms
- Add monitoring and health checks
