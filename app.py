import logging
import json
from flask import Flask, jsonify
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config

# Configure JSON logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage()
        }
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

# Setup logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
root_logger = logging.getLogger()
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
cache = Cache(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[Config.RATELIMIT_DEFAULT],
    storage_uri=Config.RATELIMIT_STORAGE_URL
)

# Register blueprints
from api import player, players, headtohead, player_v2
app.register_blueprint(player.bp)
app.register_blueprint(players.bp)
app.register_blueprint(headtohead.bp)
app.register_blueprint(player_v2.bp)

@app.route('/health')
@cache.cached(timeout=60)
@limiter.exempt
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'wespa-api'}), 200

@app.route('/')
@limiter.exempt
def index():
    """Root endpoint - health check"""
    return jsonify({'status': 'healthy', 'service': 'wespa-api', 'endpoints': ['/health', '/player/<int:player_id>', '/players', '/headtohead']}), 200

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    return jsonify({'error': 'Rate limit exceeded. 100 requests per minute allowed.'}), 429

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
