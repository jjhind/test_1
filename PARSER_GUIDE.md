# Parser Customization Guide

The generic parser may not work with all websites. This guide shows you how to customize it for https://sofasandstuff.com/discount-sofas (or any other site).

## Quick Start

Since the website blocks automated requests, you'll need to inspect it manually:

### Method 1: Using the Test Tool (Recommended)

1. **Save the webpage manually:**
   - Open https://sofasandstuff.com/discount-sofas in your browser
   - Right-click → "Save As" → Save as `page.html`

2. **Run the test tool:**
   ```bash
   python scripts/test_parser.py --file page.html
   ```

3. **Follow the interactive prompts** to find the right selectors

4. **Copy the generated code** into your parser

### Method 2: Manual Inspection

1. **Open the website in your browser:**
   - Go to https://sofasandstuff.com/discount-sofas

2. **Open Developer Tools:**
   - Right-click on a product → "Inspect" (or press F12)

3. **Find the product container:**
   - Look for the HTML element that wraps each product
   - Note the class name (e.g., `class="product-card"`)

4. **Find child elements:**
   - Title: Usually an `<h2>`, `<h3>`, or element with class like `product-title`
   - Price: Usually a `<span>` or `<div>` with class like `price`, `product-price`
   - Link: Usually an `<a>` tag

## Example: What to Look For

When you inspect the HTML, you might see something like this:

```html
<div class="product-item">
  <a href="/products/sofa-123">
    <img src="..." alt="...">
    <h3 class="product-name">Modern Grey Sofa</h3>
    <div class="product-pricing">
      <span class="price">£899.00</span>
      <span class="original-price">£1,299.00</span>
    </div>
  </a>
</div>
```

From this, you would extract:
- **Container:** `.product-item`
- **Title:** `.product-name` or `h3`
- **Price:** `.price`
- **Link:** `a`

## Updating the Parser

Once you have the selectors, update **both** files:

### 1. Update `website_monitor.py` (for self-hosted)

Find the `parse_items()` method around line 80 and replace:

```python
# Old generic selectors
product_selectors = [
    {'container': '.product', 'title': '.product-title', 'price': '.product-price', 'link': 'a'},
    {'container': '.item', 'title': '.item-title', 'price': '.price', 'link': 'a'},
    # ... more patterns
]
```

With your specific selectors (example for Sofas and Stuff):

```python
# Customized for sofasandstuff.com/discount-sofas
product_selectors = [
    {
        'container': '.product-item',      # Replace with actual class
        'title': '.product-name',          # Replace with actual class
        'price': '.price',                 # Replace with actual class
        'link': 'a'
    }
]
```

### 2. Update `lambda_handler.py` (for AWS Lambda)

Find the same `parse_items()` method and make the same changes.

## Testing Your Changes

### Test Locally (Self-Hosted Version)

```bash
# Run once to test
python website_monitor.py --once

# Check the log
tail monitor.log
```

Look for:
- "Found X products" - Should be > 0
- "New item detected:" - Should show product names
- "No items found" - Means selectors need adjustment

### Test Lambda Version

```bash
# Build and test
./scripts/build_lambda.sh

# Deploy and check CloudWatch logs
cd terraform
terraform apply
```

## Common Selector Patterns

### Container Selectors
```css
.product              /* Simple class */
.product-card         /* Specific class */
[class*="product"]    /* Any class containing "product" */
article               /* HTML5 article tag */
.grid-item            /* Grid layout */
li.product            /* List item with class */
```

### Title Selectors
```css
h2                    /* Direct tag */
h3                    /* Direct tag */
.product-title        /* Simple class */
.product-name         /* Alternative class */
.title                /* Generic class */
a > h2                /* H2 inside link */
```

### Price Selectors
```css
.price                /* Simple class */
.product-price        /* Specific class */
[class*="price"]      /* Any class containing "price" */
.price-now            /* Sale price */
.sale-price           /* Sale price */
span.price            /* Span with class */
```

### Link Selectors
```css
a                     /* Any link */
a.product-link        /* Link with class */
a[href*="/product"]   /* Link containing "/product" */
```

## Troubleshooting

### "No items found"

**Problem:** The container selector isn't matching

**Solutions:**
1. Use the test tool: `python scripts/test_parser.py --file page.html`
2. Try broader selectors like `[class*="product"]`
3. Check if products are loaded via JavaScript (may need Selenium)
4. Verify you saved the full page, not a redirect

### "Found products but title/price is 'Unknown' or 'N/A'"

**Problem:** Child selectors aren't matching

**Solutions:**
1. Inspect the HTML more carefully
2. Try different selectors (`.product-title` vs `h3` vs `.title`)
3. Use the test tool to try different combinations
4. Check if the element is nested deeper (e.g., `div > span.price`)

### "Items detected every time (duplicates)"

**Problem:** The state file isn't working or items have dynamic IDs

**Solutions:**
1. Check `items_state.json` exists and has data
2. Verify title and price are being extracted correctly
3. The hash is based on title+price+link, so all must be consistent

### Website blocks automated requests (403 error)

**Problem:** The site has bot protection

**Solutions:**
1. The parser uses proper User-Agent headers
2. Try adding delays: `time.sleep(2)` between requests
3. For testing, save the HTML manually
4. Once deployed, Lambda often has better success than local IPs

## Advanced: Multiple Selector Strategies

If products have different layouts, use multiple selector sets:

```python
product_selectors = [
    # Try this first
    {
        'container': '.product-main',
        'title': '.product-title',
        'price': '.price-main',
        'link': 'a.product-link'
    },
    # Fallback to this if first doesn't work
    {
        'container': '.item',
        'title': 'h3',
        'price': '.price',
        'link': 'a'
    }
]
```

The parser will try each set in order until it finds products.

## Need Help?

1. Run `python scripts/test_parser.py --file page.html` for interactive help
2. Check `monitor.log` for detailed error messages
3. Review CloudWatch Logs (for Lambda version)
4. Compare your selectors with the HTML in browser DevTools

## After Customizing

Once you have working selectors:

1. **For self-hosted:** Just restart the monitor
   ```bash
   python website_monitor.py
   ```

2. **For Lambda:** Rebuild and redeploy
   ```bash
   ./scripts/build_lambda.sh
   cd terraform
   terraform apply
   ```

3. **Test it:** Check logs to verify products are being detected

The first run will consider all current items as "new" and send one big email. After that, only genuinely new items will trigger notifications.
