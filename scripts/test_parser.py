#!/usr/bin/env python3
"""
Parser Testing Tool
Helps you customize the HTML parser for your specific website
"""

import requests
from bs4 import BeautifulSoup
import json
import sys

def fetch_page(url):
    """Fetch webpage with proper headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return None

def test_selectors(html, selectors):
    """Test CSS selectors against HTML"""
    soup = BeautifulSoup(html, 'html.parser')

    print(f"\nTesting selector: {selectors['container']}")
    print("=" * 80)

    products = soup.select(selectors['container'])
    print(f"Found {len(products)} products\n")

    if not products:
        print("❌ No products found! Try a different container selector.\n")

        # Suggest common patterns
        print("Common product container patterns to try:")
        print("  - .product")
        print("  - .product-card")
        print("  - .item")
        print("  - [class*='product']")
        print("  - .grid-item")
        print("  - article")
        return False

    # Test on first 3 products
    for i, product in enumerate(products[:3], 1):
        print(f"Product {i}:")
        print("-" * 40)

        # Test title
        title_elem = product.select_one(selectors['title'])
        title = title_elem.get_text(strip=True) if title_elem else "NOT FOUND"
        print(f"  Title: {title}")
        if not title_elem:
            print(f"    ❌ Title selector '{selectors['title']}' failed")

        # Test price
        price_elem = product.select_one(selectors['price'])
        price = price_elem.get_text(strip=True) if price_elem else "NOT FOUND"
        print(f"  Price: {price}")
        if not price_elem:
            print(f"    ❌ Price selector '{selectors['price']}' failed")

        # Test link
        link_elem = product.select_one(selectors['link'])
        link = link_elem.get('href', '') if link_elem else "NOT FOUND"
        print(f"  Link: {link}")
        if not link_elem:
            print(f"    ❌ Link selector '{selectors['link']}' failed")

        print()

    return True

def interactive_mode(html):
    """Interactive mode to find selectors"""
    soup = BeautifulSoup(html, 'html.parser')

    print("\n🔍 Interactive Parser Finder")
    print("=" * 80)
    print("I'll help you find the right CSS selectors for this website.\n")

    # Find container
    print("Step 1: Find the product container")
    print("-" * 40)
    container = input("Enter CSS selector for product container (e.g., '.product', '.item'): ").strip()

    products = soup.select(container)
    print(f"✓ Found {len(products)} elements\n")

    if not products:
        print("❌ No products found. Please try again with a different selector.\n")
        return None

    # Show first product HTML
    print("First product HTML (first 500 chars):")
    print("-" * 40)
    print(str(products[0])[:500])
    print("...\n")

    # Find title
    print("Step 2: Find the product title")
    print("-" * 40)
    title_selector = input("Enter CSS selector for title (e.g., 'h2', '.product-title'): ").strip()

    # Find price
    print("\nStep 3: Find the product price")
    print("-" * 40)
    price_selector = input("Enter CSS selector for price (e.g., '.price', '.product-price'): ").strip()

    # Find link
    print("\nStep 4: Find the product link")
    print("-" * 40)
    link_selector = input("Enter CSS selector for link (e.g., 'a', 'a.product-link'): ").strip()

    return {
        'container': container,
        'title': title_selector,
        'price': price_selector,
        'link': link_selector
    }

def save_html(html, filename='page.html'):
    """Save HTML to file for inspection"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✓ HTML saved to {filename}")

def main():
    print("Website Parser Testing Tool")
    print("=" * 80)

    # Get URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter website URL to test: ").strip()

    if not url:
        print("Error: No URL provided")
        sys.exit(1)

    # Fetch page
    print(f"\nFetching: {url}")
    html = fetch_page(url)

    if not html:
        print("\n❌ Failed to fetch page.")
        print("\nTroubleshooting:")
        print("1. Check if the URL is correct")
        print("2. Try opening the URL in a browser")
        print("3. The site may have bot protection - you may need to save the HTML manually")
        print("4. Use browser DevTools: Right-click → Save As → Save as 'page.html'")
        print("5. Then run: python scripts/test_parser.py --file page.html")
        sys.exit(1)

    # Save HTML for manual inspection
    save_html(html)
    print(f"✓ Page fetched successfully ({len(html)} bytes)\n")

    while True:
        print("\nWhat would you like to do?")
        print("1. Test custom selectors")
        print("2. Interactive selector finder")
        print("3. Try common selector patterns")
        print("4. Exit")

        choice = input("\nChoice (1-4): ").strip()

        if choice == '1':
            print("\nEnter CSS selectors to test:")
            selectors = {
                'container': input("Product container: ").strip(),
                'title': input("Product title: ").strip(),
                'price': input("Product price: ").strip(),
                'link': input("Product link: ").strip()
            }

            if test_selectors(html, selectors):
                print("\n✅ Selectors look good!")
                print("\nAdd this to your website_monitor.py or lambda_handler.py:")
                print("-" * 80)
                print("product_selectors = [")
                print("    {")
                print(f"        'container': '{selectors['container']}',")
                print(f"        'title': '{selectors['title']}',")
                print(f"        'price': '{selectors['price']}',")
                print(f"        'link': '{selectors['link']}'")
                print("    }")
                print("]")
                print("-" * 80)

        elif choice == '2':
            selectors = interactive_mode(html)
            if selectors:
                test_selectors(html, selectors)

        elif choice == '3':
            print("\nTrying common patterns...")

            patterns = [
                {'container': '.product', 'title': 'h2', 'price': '.price', 'link': 'a'},
                {'container': '.product', 'title': '.product-title', 'price': '.product-price', 'link': 'a'},
                {'container': '.item', 'title': 'h3', 'price': '.price', 'link': 'a'},
                {'container': '[class*="product"]', 'title': 'h2, h3', 'price': '[class*="price"]', 'link': 'a'},
                {'container': 'article', 'title': 'h2', 'price': '.price', 'link': 'a'},
                {'container': '.grid-item', 'title': '.title', 'price': '.price', 'link': 'a'},
            ]

            for i, pattern in enumerate(patterns, 1):
                print(f"\nPattern {i}:")
                if test_selectors(html, pattern):
                    break

        elif choice == '4':
            print("\nExiting...")
            break

        else:
            print("Invalid choice")

if __name__ == "__main__":
    # Support loading from file
    if len(sys.argv) > 1 and sys.argv[1] == '--file':
        if len(sys.argv) < 3:
            print("Usage: python test_parser.py --file <html_file>")
            sys.exit(1)

        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            html = f.read()

        print(f"Loaded HTML from {sys.argv[2]}")

        # Run interactive mode
        selectors = interactive_mode(html)
        if selectors:
            test_selectors(html, selectors)
    else:
        main()
