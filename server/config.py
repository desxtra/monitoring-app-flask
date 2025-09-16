import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Server Configuration
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 6000))
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Data retention (in seconds)
    DATA_RETENTION = int(os.getenv('DATA_RETENTION', 300))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'server.log')
    
    # Group Configuration - Dapat ditambah sesuai jumlah kelompok
    GROUPS = {
        'group1': 'Smart Light',
        'group2': 'Smart Trash',
        'group3': 'Smart Garden',
        'group4': 'Smart Security', 
        'group5': 'Smart Energy'
    }