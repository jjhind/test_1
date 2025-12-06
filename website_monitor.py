#!/usr/bin/env python3
"""
Website Item Monitor
Monitors a website for new items and sends email notifications
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import time
import schedule
import hashlib
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WebsiteMonitor:
    def __init__(self, config_file='config.json'):
        """Initialize the website monitor with configuration"""
        self.config = self.load_config(config_file)
        self.state_file = self.config.get('state_file', 'items_state.json')
        self.previous_items = self.load_state()

    def load_config(self, config_file):
        """Load configuration from JSON file"""
        if not os.path.exists(config_file):
            logger.error(f"Configuration file {config_file} not found!")
            raise FileNotFoundError(f"Please create {config_file}")

        with open(config_file, 'r') as f:
            return json.load(f)

    def load_state(self):
        """Load previous items state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("State file corrupted, starting fresh")
                return {}
        return {}

    def save_state(self, items):
        """Save current items state to file"""
        with open(self.state_file, 'w') as f:
            json.dump(items, f, indent=2)
        logger.info(f"State saved with {len(items)} items")

    def fetch_page(self, url):
        """Fetch webpage content"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching page: {e}")
            return None

    def parse_items(self, html):
        """
        Parse HTML to extract items
        This is a generic parser - you'll need to customize based on the actual website structure
        """
        soup = BeautifulSoup(html, 'html.parser')
        items = {}

        # Generic parsing - customize based on actual website structure
        # Look for common patterns in product listings

        # Try different common selectors
        product_selectors = [
            {'container': '.product', 'title': '.product-title', 'price': '.product-price', 'link': 'a'},
            {'container': '.item', 'title': '.item-title', 'price': '.price', 'link': 'a'},
            {'container': '[class*="product"]', 'title': 'h2, h3', 'price': '[class*="price"]', 'link': 'a'},
        ]

        for selector_set in product_selectors:
            products = soup.select(selector_set['container'])
            if products:
                logger.info(f"Found {len(products)} products using selector: {selector_set['container']}")

                for product in products:
                    try:
                        # Extract title
                        title_elem = product.select_one(selector_set['title'])
                        title = title_elem.get_text(strip=True) if title_elem else "Unknown"

                        # Extract price
                        price_elem = product.select_one(selector_set['price'])
                        price = price_elem.get_text(strip=True) if price_elem else "N/A"

                        # Extract link
                        link_elem = product.select_one(selector_set['link'])
                        link = link_elem.get('href', '') if link_elem else ""

                        # Make link absolute if relative
                        if link and not link.startswith('http'):
                            base_url = self.config['website_url'].rstrip('/')
                            link = base_url + ('/' if not link.startswith('/') else '') + link

                        # Create unique ID for item
                        item_id = hashlib.md5(f"{title}{price}{link}".encode()).hexdigest()

                        items[item_id] = {
                            'title': title,
                            'price': price,
                            'link': link,
                            'first_seen': datetime.now().isoformat()
                        }
                    except Exception as e:
                        logger.warning(f"Error parsing product: {e}")
                        continue

                break  # Stop if we found products

        if not items:
            logger.warning("No items found - you may need to customize the parser for your specific website")

        return items

    def compare_items(self, current_items):
        """Compare current items with previous state to find new items"""
        new_items = {}

        for item_id, item_data in current_items.items():
            if item_id not in self.previous_items:
                new_items[item_id] = item_data
                logger.info(f"New item detected: {item_data['title']}")

        return new_items

    def send_email_notification(self, new_items):
        """Send email notification about new items"""
        if not new_items:
            return

        email_config = self.config.get('email', {})
        if not email_config.get('enabled', False):
            logger.info("Email notifications disabled")
            return

        try:
            # Create email content
            subject = f"🔔 {len(new_items)} New Item(s) Detected on {self.config.get('website_name', 'Website')}"

            # HTML email body
            html_body = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                        .item {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                        .title {{ font-size: 18px; font-weight: bold; color: #333; }}
                        .price {{ font-size: 16px; color: #e74c3c; font-weight: bold; }}
                        .link {{ margin-top: 10px; }}
                        a {{ color: #3498db; text-decoration: none; }}
                    </style>
                </head>
                <body>
                    <h2>New Items Detected!</h2>
                    <p>The following new items have appeared on {self.config.get('website_name', 'the website')}:</p>
            """

            for item_id, item in new_items.items():
                html_body += f"""
                    <div class="item">
                        <div class="title">{item['title']}</div>
                        <div class="price">{item['price']}</div>
                        <div class="link"><a href="{item['link']}">View Item</a></div>
                    </div>
                """

            html_body += f"""
                    <p><em>Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
                </body>
            </html>
            """

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = email_config['from_email']
            msg['To'] = email_config['to_email']

            # Add HTML part
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['from_email'], email_config['password'])
                server.send_message(msg)

            logger.info(f"Email notification sent for {len(new_items)} new items")

        except Exception as e:
            logger.error(f"Error sending email: {e}")

    def check_website(self):
        """Main method to check website for new items"""
        logger.info("Starting website check...")

        # Fetch page
        html = self.fetch_page(self.config['website_url'])
        if not html:
            logger.error("Failed to fetch website")
            return

        # Parse items
        current_items = self.parse_items(html)
        logger.info(f"Found {len(current_items)} total items")

        # Compare with previous state
        new_items = self.compare_items(current_items)

        if new_items:
            logger.info(f"Found {len(new_items)} new items!")
            self.send_email_notification(new_items)
        else:
            logger.info("No new items detected")

        # Update state
        self.save_state(current_items)
        logger.info("Check complete")

    def run_once(self):
        """Run a single check"""
        self.check_website()

    def run_scheduled(self):
        """Run on a schedule"""
        check_interval = self.config.get('check_interval_hours', 1)
        logger.info(f"Starting scheduled monitoring (checking every {check_interval} hour(s))")
        logger.info(f"Monitoring: {self.config['website_url']}")

        # Run immediately on start
        self.check_website()

        # Schedule regular checks
        schedule.every(check_interval).hours.do(self.check_website)

        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute for scheduled tasks


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Website Item Monitor')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--once', action='store_true', help='Run once and exit (no scheduling)')

    args = parser.parse_args()

    try:
        monitor = WebsiteMonitor(args.config)

        if args.once:
            logger.info("Running single check...")
            monitor.run_once()
        else:
            monitor.run_scheduled()

    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
