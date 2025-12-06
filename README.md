# Website Item Monitor

A Python application that monitors websites for new items and sends email notifications when new products appear. Perfect for tracking outlet sales, limited stock items, or any website where items appear and disappear quickly.

## Features

- 🔍 **Automated Website Monitoring** - Continuously checks websites at configurable intervals
- 📧 **Email Notifications** - Sends formatted email alerts when new items are detected
- 💾 **State Tracking** - Remembers previously seen items to avoid duplicate notifications
- ⏰ **Flexible Scheduling** - Check hourly, daily, or at any custom interval
- 📊 **Detailed Logging** - Track all monitoring activity with timestamped logs
- 🎯 **Customizable Parsing** - Easy to adapt for different website structures

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd test_1
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create configuration file**
   ```bash
   cp config.example.json config.json
   ```

4. **Edit `config.json` with your settings**

## Configuration

Edit `config.json` with your specific settings:

```json
{
  "website_name": "Sofas and Stuff Outlet",
  "website_url": "https://www.sofasandstuff.com/outlet",
  "check_interval_hours": 1,
  "state_file": "items_state.json",
  "email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "from_email": "your-email@gmail.com",
    "password": "your-app-password",
    "to_email": "notification-recipient@gmail.com"
  }
}
```

### Configuration Options

- **website_name**: Display name for the website (used in notifications)
- **website_url**: The URL to monitor
- **check_interval_hours**: How often to check (in hours)
- **state_file**: File to store item history (default: items_state.json)
- **email.enabled**: Set to `true` to enable email notifications
- **email.smtp_server**: Your email provider's SMTP server
- **email.smtp_port**: SMTP port (usually 587 for TLS)
- **email.from_email**: Email address to send from
- **email.password**: Email account password or app-specific password
- **email.to_email**: Email address to receive notifications

### Email Setup (Gmail Example)

If using Gmail, you'll need to:

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to https://myaccount.google.com/security
   - Select "2-Step Verification"
   - Scroll down to "App passwords"
   - Generate a new app password for "Mail"
   - Use this password in your `config.json`

**Note:** Never commit `config.json` with real credentials to version control!

## Usage

### Run Continuously (Scheduled Monitoring)

This will check the website at your configured interval and keep running:

```bash
python website_monitor.py
```

Press `Ctrl+C` to stop.

### Run Once (Single Check)

To perform a single check and exit:

```bash
python website_monitor.py --once
```

### Use Custom Config File

```bash
python website_monitor.py --config my-config.json
```

## How It Works

1. **Fetch**: The application fetches the webpage HTML
2. **Parse**: Extracts item information (title, price, link) using BeautifulSoup
3. **Compare**: Compares current items against previously seen items
4. **Notify**: Sends email notification if new items are detected
5. **Save**: Updates the state file with current items
6. **Repeat**: Waits for the next scheduled check

## Customizing for Different Websites

The parser in `website_monitor.py` uses common HTML selectors, but you may need to customize it for your specific website:

1. Inspect the target website's HTML structure (use browser Developer Tools)
2. Modify the `parse_items()` method in `website_monitor.py`
3. Update the selectors to match the website's structure

Example customization:

```python
# In the parse_items method, modify the product_selectors list:
product_selectors = [
    {
        'container': '.your-product-class',  # Container for each product
        'title': '.your-title-class',        # Product title
        'price': '.your-price-class',        # Product price
        'link': 'a'                           # Link element
    }
]
```

## Output Files

- **monitor.log** - Detailed log of all monitoring activity
- **items_state.json** - Current state of tracked items (auto-generated)
- **config.json** - Your configuration (you create this)

## Running in the Background

### Linux/Mac (using nohup)

```bash
nohup python website_monitor.py &
```

### Using screen

```bash
screen -S monitor
python website_monitor.py
# Press Ctrl+A then D to detach
# Reattach with: screen -r monitor
```

### Using systemd (Linux)

Create `/etc/systemd/system/website-monitor.service`:

```ini
[Unit]
Description=Website Item Monitor
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/test_1
ExecStart=/usr/bin/python3 /path/to/test_1/website_monitor.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable website-monitor
sudo systemctl start website-monitor
sudo systemctl status website-monitor
```

## Troubleshooting

### No items detected

- Check that the website URL is correct
- Verify the website is accessible (try opening it in a browser)
- The HTML selectors may need customization for your specific website
- Run with `--once` and check `monitor.log` for details

### Email not sending

- Verify SMTP settings are correct
- For Gmail, ensure you're using an App Password (not your regular password)
- Check that "Less secure app access" is enabled (if not using App Password)
- Review `monitor.log` for error messages

### Too many notifications

- Increase `check_interval_hours` in config.json
- The state file may have been deleted, causing all items to be seen as "new"

## Example Notification

When new items are detected, you'll receive an email like:

```
Subject: 🔔 3 New Item(s) Detected on Sofas and Stuff Outlet

New Items Detected!

The following new items have appeared on Sofas and Stuff Outlet:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Modern Fabric Sofa
£899.00
View Item
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

...
```

## Security Notes

- Never commit `config.json` with real credentials
- Use app-specific passwords instead of main account passwords
- Keep your `config.json` file permissions restricted (chmod 600)
- Consider using environment variables for sensitive data

## Contributing

Feel free to submit issues or pull requests!

## License

MIT License - feel free to use and modify as needed.
