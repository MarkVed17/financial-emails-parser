from bs4 import BeautifulSoup
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

def setup_selenium_driver():
    """Setup Selenium WebDriver with Chrome options"""
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Disable headless for debugging
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"❌ Error setting up Chrome driver: {e}")
        return None

def load_all_cards_with_pagination(url):
    """Load all credit cards by handling pagination with Selenium"""
    driver = setup_selenium_driver()
    if not driver:
        return None
    
    try:
        print(f"🚀 Loading page: {url}")
        driver.get(url)
        
        # Wait for page to fully load and check for content
        time.sleep(5)
        print(f"✅ Page loaded: {driver.title}")
        
        # Check if we have content
        all_divs = driver.find_elements(By.TAG_NAME, 'div')
        print(f"📁 Found {len(all_divs)} div elements on page")
        
        # Look for any elements that might contain "credit card"
        elements_with_cc = driver.find_elements(By.XPATH, "//*[contains(text(), 'Credit Card') or contains(text(), 'credit card')]")
        print(f"💳 Found {len(elements_with_cc)} elements mentioning 'credit card'")
        
        # Click "Show More Cards" button repeatedly to load all 80 cards
        max_attempts = 15
        
        print("🔄 Starting pagination to load all cards...")
        
        for attempt in range(max_attempts):
            try:
                # Wait for page to stabilize
                time.sleep(3)
                
                # Try to find "Show More Cards" button
                show_more_button = None
                
                try:
                    # Look for button with "Show More Cards" text
                    show_more_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Show More Cards')]")
                except:
                    try:
                        # Fallback: look for any button with "Show More" 
                        show_more_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Show More')]")
                    except:
                        print(f"❌ No 'Show More' button found on attempt {attempt + 1}")
                        break
                
                if show_more_button and show_more_button.is_enabled() and show_more_button.is_displayed():
                    # Scroll to button and click
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", show_more_button)
                    time.sleep(2)
                    
                    # Click using JavaScript to avoid interception
                    driver.execute_script("arguments[0].click();", show_more_button)
                    print(f"✅ Clicked 'Show More Cards' button (attempt {attempt + 1})")
                    
                    # Wait for new content to load
                    time.sleep(5)
                    
                else:
                    print(f"✅ No more 'Show More Cards' button available. Pagination complete after {attempt + 1} attempts")
                    break
                    
            except Exception as e:
                print(f"⚠️ Error during pagination attempt {attempt + 1}: {e}")
                break
        
        # Get final HTML content
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print("✅ Successfully loaded page with pagination")
        return soup
        
    except Exception as e:
        print(f"❌ Error loading page with Selenium: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def extract_image_url(img_tag):
    """Extract image URL from img tag"""
    if not img_tag:
        return None
    return img_tag.get('src', '')

def parse_fee_amount(fee_text):
    """Extract numeric fee amount from text like '₹10,000+ Taxes'"""
    if not fee_text:
        return None
    
    numbers = re.findall(r'₹?([0-9,]+)', fee_text)
    if numbers:
        try:
            return int(numbers[0].replace(',', ''))
        except ValueError:
            pass
    return None

# Load the page with all cards
url = "https://www.paisabazaar.com/credit-cards/"
print("🚀 Starting credit card data extraction with pagination support...")
soup = load_all_cards_with_pagination(url)

if not soup:
    print("❌ Failed to load page")
    exit(1)

cards = []

# Find all potential card containers using multiple strategies
print("🔍 Looking for credit card containers...")

# Strategy 1: Look for divs that contain credit card information
card_sections = []

# Find all divs that might contain card data
all_divs = soup.find_all('div')
print(f"📊 Found {len(all_divs)} total divs on page")

# Look for divs with substantial content that mentions credit cards
for div in all_divs:
    text = div.get_text(strip=True)
    
    # Filter for divs that likely contain individual credit card information
    if (len(text) > 100 and len(text) < 2000 and  # Reasonable size
        'credit card' in text.lower() and  # Must mention credit card
        ('joining fee' in text.lower() or 'annual fee' in text.lower() or '₹' in text) and  # Must have fee info
        text.count('credit card') == 1):  # Likely a single card container
        
        # Avoid generic sections
        if not any(generic in text.lower() for generic in ['best credit cards', 'all credit cards', 'compare credit cards']):
            card_sections.append(div)

print(f"✅ Found {len(card_sections)} potential card sections")

# Extract data from each card section
seen_cards = set()
for i, section in enumerate(card_sections):
    print(f"🔄 Processing card {i+1}/{len(card_sections)}")
    
    section_text = section.get_text(strip=True)
    
    # Extract card name
    card_name = None
    
    # Look for headings or strong text with card names
    for element in section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b']):
        element_text = element.get_text(strip=True)
        if ('credit card' in element_text.lower() and 
            len(element_text) > 15 and len(element_text) < 150 and
            not any(generic in element_text.lower() for generic in ['best credit cards', 'all credit cards'])):
            card_name = element_text
            break
    
    # Fallback: use regex to find card names
    if not card_name:
        patterns = [
            r'([A-Z][A-Za-z\s]+Credit Card)',
            r'((?:HDFC|Axis|ICICI|SBI|YES|Kotak|American Express)[A-Za-z\s]+Credit Card)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, section_text)
            if matches:
                card_name = matches[0].strip()
                break
    
    if not card_name or card_name in seen_cards:
        continue
    
    seen_cards.add(card_name)
    
    # Extract card image
    card_image = None
    img_tag = section.find('img')
    if img_tag and 'card' in img_tag.get('src', '').lower():
        card_image = extract_image_url(img_tag)
    
    # Extract categories from images or text
    categories = []
    for img in section.find_all('img'):
        alt = img.get('alt', '').lower()
        if any(cat in alt for cat in ['travel', 'cashback', 'reward', 'premium', 'shopping', 'fuel', 'dining']):
            for cat in ['travel', 'cashback', 'reward', 'premium', 'shopping', 'fuel', 'dining']:
                if cat in alt and cat.title() not in categories:
                    categories.append(cat.title())
    
    # Extract features
    features = []
    feature_patterns = [
        r'(\d+(?:\.\d+)?%[^.]{10,100}(?:cashback|reward|value|back))',
        r'(unlimited[^.]{10,100}(?:access|visit|lounge))',
        r'(up to[^.]{10,100}(?:₹|reward|point))',
        r'((?:complimentary|free)[^.]{10,100}(?:lounge|visit|access))',
    ]
    
    for pattern in feature_patterns:
        matches = re.findall(pattern, section_text, re.IGNORECASE)
        for match in matches:
            clean_match = match.strip()
            if len(clean_match) > 15 and len(clean_match) < 200 and clean_match not in features:
                features.append(clean_match)
    
    features = features[:5]  # Limit to 5 features
    
    # Extract fees
    joining_fee = None
    annual_fee = None
    
    section_text_lower = section_text.lower()
    
    # Extract joining fee
    joining_matches = re.findall(r'joining fee[:\s]*₹?\s*([0-9,]+)', section_text_lower)
    if joining_matches:
        joining_fee = parse_fee_amount(joining_matches[0])
    
    # Extract annual/renewal fee
    annual_matches = re.findall(r'(?:annual|renewal)\s*fee[:\s]*₹?\s*([0-9,]+)', section_text_lower)
    if annual_matches:
        annual_fee = parse_fee_amount(annual_matches[0])
    
    # Determine bank
    bank = "Unknown"
    bank_patterns = {
        'hdfc': 'HDFC Bank',
        'axis': 'Axis Bank',
        'icici': 'ICICI Bank', 
        'sbi': 'State Bank of India',
        'yes bank': 'YES Bank',
        'american express': 'American Express',
        'kotak': 'Kotak Mahindra Bank',
    }
    
    card_name_lower = card_name.lower()
    for pattern, bank_name in bank_patterns.items():
        if pattern in card_name_lower:
            bank = bank_name
            break
    
    # Create card data structure
    card_data = {
        "id": len(cards) + 1,
        "card_name": card_name,
        "bank": bank,
        "official_card_image": card_image,
        "joining_fees": joining_fee,
        "annual_fees": annual_fee,
        "currency": "INR",
        "categories": categories,
        "features": features,
        "extracted_from": "paisabazaar.com"
    }
    
    cards.append(card_data)

# Output structured JSON
output_data = {
    "credit_cards": cards,
    "metadata": {
        "total_cards_extracted": len(cards),
        "source": "paisabazaar.com", 
        "extraction_date": "2025-08-22",
        "extraction_method": "Selenium pagination + BeautifulSoup parsing",
        "note": "Extracted using automated pagination to load all cards"
    }
}

# Save to JSON file
output_filename = 'indian_credit_cards_all_paginated.json'
with open(output_filename, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"✅ Successfully extracted {len(cards)} credit cards")
print(f"💾 Data saved to '{output_filename}'")
print(f"📊 Cards with images: {sum(1 for card in cards if card['official_card_image'])}")
print(f"💰 Cards with fee information: {sum(1 for card in cards if card['joining_fees'] or card['annual_fees'])}")

# Display sample of extracted data
print("\n🔍 Sample extracted cards:")
for card in cards[:3]:
    print(f"\n📋 {card['card_name']}")
    print(f"   🏦 Bank: {card['bank']}")
    print(f"   💳 Joining Fee: ₹{card['joining_fees']:,}" if card['joining_fees'] else "   💳 Joining Fee: Not found")
    print(f"   🔄 Annual Fee: ₹{card['annual_fees']:,}" if card['annual_fees'] else "   🔄 Annual Fee: Not found")
    print(f"   🖼️  Image: {'✅ Found' if card['official_card_image'] else '❌ Not found'}")
    print(f"   📂 Categories: {', '.join(card['categories']) if card['categories'] else 'None'}")

print(f"\n📄 Full data available in: {output_filename}")