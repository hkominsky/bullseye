import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import threading
import time
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)
from model.data_pipeline.data_manager import DataManager
from src.model.utils.env_validation import EnvValidation, EnvValidationError
from src.model.utils.logger_config import LoggerSetup
from src.model.utils.progress_tracker import ProgressTracker


class EarningsWebhookController:
    """
    Webhook server that receives earnings event notifications from Finnhub for specified tickers
    and automates sending the market brief email.
    """
    
    def __init__(self, user_email, tickers_list, finnhub_api_key, webhook_url):
        """Initialize the webhook controller with configuration and dependencies."""
        self.logger = LoggerSetup.setup_logger(__name__)
        self.user_email = user_email
        self.tickers = set(tickers_list)
        self.finnhub_api_key = finnhub_api_key
        self.webhook_url = webhook_url
        self.sec_manager = DataManager(user_email)
        self.start_time = datetime.now()
        
        self.app = Flask(__name__)
        self.setup_routes()
    
    def _is_valid_request(self, data):
        """Validate incoming webhook payload."""
        if not data or not isinstance(data, dict):
            return False
        
        if not data.get('symbol') or not isinstance(data.get('symbol'), str): 
            return False
        
        if data.get('event') != 'earnings':
            return False
        
        if data.get('symbol').upper() not in self.tickers:
            return False
        
        return True
    
    def setup_routes(self):
        """Configure Flask routes for the webhook server."""
        @self.app.route('/webhook/earnings', methods=['POST'])
        def handle_earnings():
            request_id = f"req_{int(time.time() * 1000)}"
            
            try:
                data = request.get_json()
                
                if not self._is_valid_request(data):
                    return jsonify({'error': 'Invalid request', 'request_id': request_id}), 400
                
                ticker = data['symbol'].upper()
                
                thread = threading.Thread(
                    target=self._process_earnings_async, 
                    args=(ticker, request_id)
                )
                thread.daemon = True
                thread.start()
                
                return jsonify({
                    'success': True,
                    'ticker': ticker,
                    'request_id': request_id,
                    'timestamp': datetime.now().isoformat()
                }), 200
                
            except Exception as e:
                self.logger.error(f"Webhook error [{request_id}]: {e}")
                return jsonify({
                    'error': str(e),
                    'request_id': request_id,
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Simple health check endpoint."""
            uptime = (datetime.now() - self.start_time).total_seconds()
            return jsonify({
                'status': 'ok',
                'tickers': list(self.tickers),
                'uptime_seconds': uptime
            })
        
        @self.app.route('/setup-webhooks', methods=['POST'])
        def setup_webhooks_endpoint():
            """Manual endpoint to configure Finnhub webhooks."""
            success_count = self.setup_finnhub_webhooks()
            return jsonify({
                'message': f'Set up {success_count}/{len(self.tickers)} webhooks',
                'tickers': list(self.tickers)
            })
    
    def setup_finnhub_webhooks(self):
        """Set up webhooks on Finnhub for all monitored tickers."""
        self.logger.info("Setting up Finnhub webhooks")
        
        headers = {
            'X-Finnhub-Token': self.finnhub_api_key,
            'Content-Type': 'application/json'
        }
        
        success_count = 0
        for ticker in self.tickers:
            try:
                data = {
                    'event': 'earnings',
                    'symbol': ticker,
                    'url': f"{self.webhook_url}/webhook/earnings"
                }
                
                response = requests.post(
                    'https://finnhub.io/api/v1/webhook',
                    headers=headers,
                    json=data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.logger.info(f"Webhook created for {ticker}")
                    success_count += 1
                else:
                    self.logger.error(f"Failed to create webhook for {ticker}: {response.status_code}")
                    
            except Exception as e:
                self.logger.error(f"Error setting up webhook for {ticker}: {e}")
        
        self.logger.info(f"Webhook setup complete: {success_count}/{len(self.tickers)} successful")
        return success_count
    
    def _process_earnings_async(self, ticker, request_id):
        """Process earnings data asynchronously in background thread."""
        try:
            self.logger.info(f"Processing earnings for {ticker} [{request_id}]")
            
            progress = ProgressTracker()
            progress.start(ticker)
            
            self.sec_manager.process_ticker(ticker, progress)
            progress.complete(ticker)
            
            self.logger.info(f"Successfully processed {ticker} [{request_id}]")
            
        except Exception as e:
            self.logger.error(f"Failed processing {ticker} [{request_id}]: {e}")
    
    def run(self, host='0.0.0.0', port=8080):
        """Start the webhook server and initialize webhooks."""
        self.logger.info(f"Starting webhook server on {host}:{port}")
        self.logger.info(f"Webhook URL: {self.webhook_url}")
        self.logger.info(f"Monitoring tickers: {', '.join(sorted(self.tickers))}")
        
        self.setup_finnhub_webhooks()
        
        self.logger.info("Server is running!")
        self.app.run(host=host, port=port, debug=False)


def main():
    """Main entry point for the webhook controller application."""
    load_dotenv()
    logger = LoggerSetup.setup_logger(__name__, console=True)
    
    try:
        required_vars = ["USER_EMAIL", "TICKERS", "FINNHUB_API_KEY", "WEBHOOK_URL"]
        env_vars = EnvValidation.validate_env_vars(required_vars)
        tickers = EnvValidation.parse_tickers(env_vars["TICKERS"])
        
        controller = EarningsWebhookController(
            user_email=env_vars["USER_EMAIL"],
            tickers_list=tickers,
            finnhub_api_key=env_vars["FINNHUB_API_KEY"],
            webhook_url=env_vars["WEBHOOK_URL"]
        )
        
        host = os.getenv('WEBHOOK_HOST', '0.0.0.0')
        port = int(os.getenv('WEBHOOK_PORT', 8080))
        
        controller.run(host=host, port=port)
        
    except EnvValidationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()