"""
Lambda Handler for Website Item Monitor
AWS Lambda function that monitors websites for new items
"""

import json
import os
import boto3
import requests
from bs4 import BeautifulSoup
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# S3 client for storing state
s3 = boto3.client('s3')


class WebsiteMonitorLambda:
    def __init__(self):
        """Initialize with environment variables"""
        self.config = {
            'website_name': os.environ.get('WEBSITE_NAME', 'Website'),
            'website_url': os.environ['WEBSITE_URL'],
            'bucket_name': os.environ['STATE_BUCKET'],
            'state_key': os.environ.get('STATE_KEY', 'items_state.json'),
        }

        self.email_config = {
            'enabled': os.environ.get('EMAIL_ENABLED', 'true').lower() == 'true',
            'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.environ.get('SMTP_PORT', '587')),
            'from_email': os.environ.get('FROM_EMAIL'),
            'password': os.environ.get('EMAIL_PASSWORD'),
            'to_email': os.environ.get('TO_EMAIL'),
        }

        self.previous_items = self.load_state()

    def load_state(self):
        """Load previous items state from S3"""
        try:
            response = s3.get_object(
                Bucket=self.config['bucket_name'],
                Key=self.config['state_key']
            )
            state = json.loads(response['Body'].read().decode('utf-8'))
            logger.info(f"Loaded state with {len(state)} items from S3")
            return state
        except s3.exceptions.NoSuchKey:
            logger.info("No previous state found, starting fresh")
            return {}
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return {}

    def save_state(self, items):
        """Save current items state to S3"""
        try:
            s3.put_object(
                Bucket=self.config['bucket_name'],
                Key=self.config['state_key'],
                Body=json.dumps(items, indent=2),
                ContentType='application/json'
            )
            logger.info(f"State saved with {len(items)} items to S3")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
            raise

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
        """Parse HTML to extract items"""
        soup = BeautifulSoup(html, 'html.parser')
        items = {}

        # Generic parsing - customize based on actual website structure
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

                break

        if not items:
            logger.warning("No items found - you may need to customize the parser")

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

        if not self.email_config.get('enabled', False):
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
            msg['From'] = self.email_config['from_email']
            msg['To'] = self.email_config['to_email']

            # Add HTML part
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['from_email'], self.email_config['password'])
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
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to fetch website'})
            }

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

        return {
            'statusCode': 200,
            'body': json.dumps({
                'total_items': len(current_items),
                'new_items': len(new_items),
                'new_item_titles': [item['title'] for item in new_items.values()]
            })
        }


def lambda_handler(event, context):
    """
    AWS Lambda handler function

    Environment variables required:
    - WEBSITE_URL: URL to monitor
    - STATE_BUCKET: S3 bucket for state storage
    - FROM_EMAIL: Sender email address
    - EMAIL_PASSWORD: Email password/app password
    - TO_EMAIL: Recipient email address

    Optional:
    - WEBSITE_NAME: Display name (default: "Website")
    - STATE_KEY: S3 key for state file (default: "items_state.json")
    - EMAIL_ENABLED: Enable/disable email (default: "true")
    - SMTP_SERVER: SMTP server (default: "smtp.gmail.com")
    - SMTP_PORT: SMTP port (default: "587")
    """
    try:
        monitor = WebsiteMonitorLambda()
        result = monitor.check_website()
        return result
    except Exception as e:
        logger.error(f"Error in lambda handler: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
