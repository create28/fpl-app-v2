import os

class Config:
    """Configuration class for different environments."""
    
    # Environment detection
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'local')
    IS_PRODUCTION = ENVIRONMENT == 'production'
    
    # Server configuration
    PORT = int(os.getenv('PORT', 8000))
    HOST = os.getenv('HOST', 'localhost')
    
    # FPL API configuration
    FPL_LEAGUE_ID = 874353
    
    # Database configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'fpl_history.db')
    
    # API base URLs
    if IS_PRODUCTION:
        # Production (Render) - will be set by environment variable
        API_BASE_URL = os.getenv('API_BASE_URL', 'https://fpl-app-v2.onrender.com')
    else:
        # Local development
        API_BASE_URL = f'http://{HOST}:{PORT}'
    
    # Rate limiting
    API_DELAY_SECONDS = 2  # Delay between API calls to respect FPL limits
    
    # Cache settings
    CACHE_DURATION_HOURS = 24
    
    @classmethod
    def get_api_url(cls, endpoint):
        """Get full API URL for an endpoint."""
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]  # Remove leading slash
        return f"{cls.API_BASE_URL}/{endpoint}"
    
    @classmethod
    def print_config(cls):
        """Print current configuration."""
        print("=== FPL App Configuration ===")
        print(f"Environment: {cls.ENVIRONMENT}")
        print(f"Port: {cls.PORT}")
        print(f"Host: {cls.HOST}")
        print(f"API Base URL: {cls.API_BASE_URL}")
        print(f"Database: {cls.DATABASE_PATH}")
        print(f"League ID: {cls.FPL_LEAGUE_ID}")
        print("=============================")
