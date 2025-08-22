from bs4 import BeautifulSoup
import json
import requests
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

def extract_image_url(img_tag):
    """Extract image URL from img tag using just the src attribute"""
    if not img_tag:
        return None
    
    return img_tag.get('src', '')

def parse_fee_amount(fee_text):
    """Extract numeric fee amount from text like '₹10,000+ Taxes'"""
    if not fee_text:
        return None
    
    # Extract numbers from fee text
    numbers = re.findall(r'₹?([0-9,]+)', fee_text)
    if numbers:
        try:
            return int(numbers[0].replace(',', ''))
        except ValueError:
            pass
    return None


def setup_selenium_driver():
    """Setup Selenium WebDriver with Chrome options"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
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
        print("📝 Make sure ChromeDriver is installed and in PATH")
        return None

def load_all_cards_with_pagination(url):
    """Load all credit cards by handling pagination with Selenium"""
    driver = setup_selenium_driver()
    if not driver:
        return None
    
    try:
        print(f"🚀 Loading page: {url}")
        driver.get(url)
        
        # Wait for initial page load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Wait for page to fully load
        time.sleep(3)
        print(f"✅ Page loaded: {driver.title}")
        
        # Click "Show More Cards" button repeatedly to load all 80 cards
        total_cards = 0
        max_attempts = 15  # Should be enough to load 80 cards
        
        print("🔄 Starting pagination to load all cards...")
        
        for attempt in range(max_attempts):
            try:
                # Wait for page to stabilize
                time.sleep(2)
                
                # Count current cards using multiple strategies
                current_cards = 0
                card_selectors = [
                    "div.w-full.flex.border.border-\\[\\#E4E4E3\\].rounded-lg",
                    "div[class*='w-full'][class*='flex'][class*='border'][class*='rounded-lg']",
                    "div[class*='border'][class*='rounded']"
                ]
                
                for selector in card_selectors:
                    try:
                        cards = driver.find_elements(By.CSS_SELECTOR, selector)
                        if len(cards) > current_cards:
                            current_cards = len(cards)
                    except:
                        continue
                
                print(f"🔄 Attempt {attempt + 1}: Found {current_cards} potential cards")
                
                # Find "Show More Cards" button using the exact class structure
                show_more_button = None
                
                try:
                    # Use XPath to find button with exact text
                    show_more_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Show More Cards')]")
                except:
                    try:
                        # Fallback: find button with partial text
                        show_more_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Show More')]")
                    except:
                        # Final fallback: look for buttons with specific classes
                        try:
                            buttons = driver.find_elements(By.CSS_SELECTOR, "button.inline-flex.items-center.justify-center")
                            for button in buttons:
                                if "show more" in button.text.lower():
                                    show_more_button = button
                                    break
                        except:
                            pass
                
                if show_more_button and show_more_button.is_enabled() and show_more_button.is_displayed():
                    try:
                        # Scroll to button
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", show_more_button)
                        time.sleep(1)
                        
                        # Click the button using JavaScript to avoid interception
                        driver.execute_script("arguments[0].click();", show_more_button)
                        print(f"✅ Clicked 'Show More Cards' button (attempt {attempt + 1})")
                        
                        # Wait for new content to load
                        time.sleep(4)
                        
                        # Check if more cards loaded
                        new_card_count = 0
                        for selector in card_selectors:
                            try:
                                cards = driver.find_elements(By.CSS_SELECTOR, selector)
                                if len(cards) > new_card_count:
                                    new_card_count = len(cards)
                            except:
                                continue
                        
                        if new_card_count <= current_cards:
                            print(f"✅ No new cards loaded. Final count: {current_cards}")
                            total_cards = current_cards
                            break
                        else:
                            total_cards = new_card_count
                            print(f"✅ Loaded {new_card_count - current_cards} new cards. Total: {new_card_count}")
                            
                            # If we've reached around 80 cards, we're probably done
                            if new_card_count >= 80:
                                print(f"✅ Reached target of 80+ cards: {new_card_count}")
                                break
                            
                    except Exception as e:
                        print(f"⚠️ Error clicking button: {e}")
                        break
                else:
                    print(f"✅ No more 'Show More Cards' button or button disabled. Final total: {current_cards}")
                    total_cards = current_cards
                    break
                    
            except Exception as e:
                print(f"⚠️ Error during pagination attempt {attempt + 1}: {e}")
                break
        
        # Get final HTML content
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print(f"✅ Successfully loaded page with pagination. Total cards loaded: {total_cards}")
        return soup
        
    except Exception as e:
        print(f"❌ Error loading page with Selenium: {e}")
        return None
    finally:
        if driver:
            driver.quit()

# Load the page with all cards
url = "https://www.paisabazaar.com/credit-cards/"
print("🚀 Starting credit card data extraction with pagination support...")
soup = load_all_cards_with_pagination(url)

cards = []

# Step 1: Find all card sections using the specified HTML structure
print("🔍 Looking for credit card containers using specified structure...")

# First, find the main container: <div class="flex gap-[30px]">
main_container = soup.find('div', class_=lambda x: x and isinstance(x, list) and 'flex' in x and 'gap-[30px]' in x)

if not main_container:
    print("❌ Could not find main container div.flex.gap-[30px]")
    card_sections = []
else:
    print("✅ Found main container div.flex.gap-[30px]")
    
    # Within main container, find child: <div class="flex flex-col gap-4 w-full">
    content_container = main_container.find('div', class_=lambda x: x and isinstance(x, list) and 
                                          'flex' in x and 'flex-col' in x and 'gap-4' in x and 'w-full' in x)
    
    if not content_container:
        print("❌ Could not find content container div.flex.flex-col.gap-4.w-full")
        card_sections = []
    else:
        print("✅ Found content container div.flex.flex-col.gap-4.w-full")
        
        # Find all card divs: <div class="w-full flex border border-[#E4E4E3] rounded-lg">
        card_sections = content_container.find_all('div', class_=lambda x: x and isinstance(x, list) and 
                                                  'w-full' in x and 'flex' in x and 'border' in x and 
                                                  'border-[#E4E4E3]' in x and 'rounded-lg' in x)
        
        print(f"✅ Found {len(card_sections)} card sections with exact target structure")
        
        # Fallback: if exact class match fails, try broader search within content container
        if len(card_sections) == 0:
            print("⚠️ Exact class match failed, trying broader search within content container...")
            card_sections = content_container.find_all('div', class_=lambda x: x and isinstance(x, list) and 
                                                      'w-full' in x and 'flex' in x and 'border' in x and 'rounded-lg' in x)
            print(f"📋 Broader search found {len(card_sections)} card sections")

# Debug: Let's see what we actually found
print(f"📋 Final card sections to process: {len(card_sections)}")

# Debug: Print first few card section snippets to understand structure
if card_sections:
    print("🔍 Debugging: First few card sections found:")
    for i, section in enumerate(card_sections[:3]):
        text_snippet = section.get_text(strip=True)[:200] + "..." if len(section.get_text(strip=True)) > 200 else section.get_text(strip=True)
        print(f"   Section {i+1}: {text_snippet}")
else:
    print("❌ No card sections found! Let's check what divs we have...")
    all_divs = soup.find_all('div')
    print(f"   Total divs found: {len(all_divs)}")
    # Show a few divs that mention credit card
    cc_divs = [div for div in all_divs if 'credit card' in div.get_text().lower()][:5]
    print(f"   Divs mentioning 'credit card': {len(cc_divs)}")
    for i, div in enumerate(cc_divs):
        text_snippet = div.get_text(strip=True)[:150] + "..." if len(div.get_text(strip=True)) > 150 else div.get_text(strip=True)
        print(f"     CC Div {i+1}: {text_snippet}")

# 2. Extract Card Data from all found sections
seen_cards = set()
for i, section in enumerate(card_sections):  # Process all found cards
    print(f"🔄 Processing section {i+1}/{min(200, len(card_sections))}")
    
    section_text = section.get_text(strip=True)
    
    # Extract Name: Look for card title in the first immediate <div>
    card_name = None
    
    # Method 1: Look for the first immediate div with card title (following the specified pattern)
    immediate_divs = section.find_all('div', recursive=False)  # Only direct children
    for div in immediate_divs:
        text = div.get_text(strip=True)
        # Look for text that starts with ### or contains "Credit Card"
        if (('###' in text and 'credit card' in text.lower()) or 
            ('credit card' in text.lower() and len(text) > 15 and len(text) < 150 and
             not any(generic in text.lower() for generic in ['best credit cards', 'credit card in india', 'all credit cards']))):
            # Clean up the name by removing ### if present
            card_name = text.replace('###', '').strip()
            break
    
    # Method 2: Look for headings with specific card names (most reliable)
    if not card_name:
        for heading in section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = heading.get_text(strip=True)
            if ('credit card' in heading_text.lower() and 
                len(heading_text) > 15 and len(heading_text) < 100 and
                not any(generic in heading_text.lower() for generic in ['best credit cards', 'credit card in india', 'all credit cards'])):
                card_name = heading_text
                break
    
    # Method 3: Look for specific patterns in strong/bold text (common for card names)
    if not card_name:
        for strong in section.find_all(['strong', 'b']):
            strong_text = strong.get_text(strip=True)
            if ('credit card' in strong_text.lower() and 
                len(strong_text) > 15 and len(strong_text) < 100 and
                not any(skip in strong_text.lower() for skip in ['apply', 'check', 'compare', 'eligibility', 'best credit cards'])):
                card_name = strong_text
                break
    
    # Skip if no valid card name found or if it's too generic
    if (not card_name or 
        card_name in seen_cards or 
        len(card_name) < 15 or
        any(generic in card_name.lower() for generic in ['credit card', 'best credit cards', 'all credit cards']) and len(card_name) < 25):
        continue
    
    seen_cards.add(card_name)
    
    # Find card image within this section
    card_image = None
    img_tag = section.find('img')
    
    # Look for credit card specific images
    if img_tag:
        src = img_tag.get('src', '')
        # Filter for actual credit card images, not icons
        if any(pattern in src.lower() for pattern in ['credit-card', 'card', '.png', '.jpg', '.jpeg', '.webp']):
            if not any(icon in src.lower() for icon in ['icon', 'logo', 'symbol', 'star', 'arrow']):
                card_image = extract_image_url(img_tag)
    
    # If no image found in section, look nearby
    if not card_image:
        # Look for images in parent or sibling elements
        parent = section.parent
        if parent:
            for img in parent.find_all('img'):
                src = img.get('src', '')
                if any(pattern in src.lower() for pattern in ['credit-card', 'card']) and 'png' in src.lower():
                    card_image = extract_image_url(img)
                    break
    
    # Extract Categories: Look for icons with alt text or class names like travel, premium, reward, etc.
    categories = []
    
    # Method 1: Check icon images for category information (alt attributes)
    for img in section.find_all('img'):
        alt = img.get('alt', '').lower()
        src = img.get('src', '').lower()
        
        # Category keywords to look for in alt text or src
        category_keywords = {
            'travel': 'Travel',
            'cashback': 'Cashback', 
            'reward': 'Rewards',
            'premium': 'Premium',
            'shopping': 'Shopping',
            'fuel': 'Fuel',
            'dining': 'Dining',
            'lifestyle': 'Lifestyle',
            'lounge': 'Lounge Access',
            'business': 'Business',
            'luxury': 'Luxury'
        }
        
        for keyword, category in category_keywords.items():
            if keyword in alt or keyword in src:
                if category not in categories:
                    categories.append(category)
    
    # Method 2: Look for category badges/tags in spans or divs
    category_indicators = section.find_all(['span', 'div'], class_=lambda x: x and any(cat in ' '.join(x).lower() for cat in ['tag', 'badge', 'category', 'label']) if isinstance(x, list) else False)
    
    for indicator in category_indicators:
        text = indicator.get_text(strip=True).lower()
        category_keywords = ['travel', 'cashback', 'rewards', 'premium', 'shopping', 'fuel', 'dining', 'lifestyle', 'lounge']
        for keyword in category_keywords:
            if keyword in text:
                categories.append(keyword.title())
    
    # Method 3: Look for category information in class names of elements
    for element in section.find_all():
        if element.get('class'):
            class_str = ' '.join(element.get('class')).lower()
            if any(cat in class_str for cat in ['travel', 'premium', 'reward', 'cashback', 'shopping']):
                for cat in ['travel', 'premium', 'reward', 'cashback', 'shopping']:
                    if cat in class_str and cat.title() not in categories:
                        categories.append(cat.title())
    
    # Extract Features: Look for bullet-point benefits following icons or in subsequent divs/spans
    features = []
    
    # Method 1: Look for structured bullet points or list items
    for element in section.find_all(['li', 'ul', 'ol']):
        element_text = element.get_text(strip=True)
        if (len(element_text) > 15 and len(element_text) < 200 and
            any(keyword in element_text.lower() for keyword in ['cashback', 'reward', 'lounge', 'complimentary', 'free', 'discount', 'points', 'value-back', 'savings', '%']) and
            not any(skip in element_text.lower() for skip in ['apply', 'check', 'compare', 'eligibility', 'terms', 'conditions'])):
            features.append(element_text)
    
    # Method 2: Look for spans or divs that contain benefit descriptions
    for element in section.find_all(['span', 'div']):
        element_text = element.get_text(strip=True)
        # Look for specific benefit patterns like "3.33% value-back across all spends"
        if (len(element_text) > 20 and len(element_text) < 200 and
            (re.search(r'\d+(?:\.\d+)?%', element_text) or  # Contains percentage
             any(keyword in element_text.lower() for keyword in ['cashback', 'reward', 'lounge', 'complimentary', 'free', 'unlimited', 'points', 'value-back'])) and
            not any(skip in element_text.lower() for skip in ['apply', 'check', 'compare', 'eligibility', 'terms', 'conditions', 'fee'])):
            if element_text not in features:  # Avoid duplicates
                features.append(element_text)
    
    # Method 3: Pattern matching for specific benefit formats
    if len(features) < 3:  # If we don't have enough structured features
        feature_patterns = [
            r'(\d+(?:\.\d+)?%[^.]{10,100}(?:cashback|reward|value|back))',
            r'(unlimited[^.]{10,100}(?:access|visit|lounge|airport))',
            r'(up to[^.]{10,100}(?:₹|rs\.?|reward|point))',
            r'((?:complimentary|free)[^.]{10,100}(?:lounge|visit|access|membership))',
            r'(₹\s*[0-9,]+[^.]{10,100}(?:cashback|reward|voucher|credit))',
            r'([0-9]+x[^.]{10,100}(?:points|reward|miles))'
        ]
        
        for pattern in feature_patterns:
            matches = re.findall(pattern, section_text, re.IGNORECASE)
            for match in matches:
                clean_match = match.strip()
                if len(clean_match) > 15 and len(clean_match) < 150 and clean_match not in features:
                    features.append(clean_match)
    
    # Remove duplicates and limit to top 5 features
    features = list(dict.fromkeys(features))[:5]  # Preserve order while removing duplicates
    
    # Extract Fees: Look for joining and annual/renewal fee information in structured format
    joining_fee = None
    annual_fee = None
    
    # Method 1: Look for fee information in structured divs or sections
    for element in section.find_all(['div', 'span', 'p']):
        element_text = element.get_text(strip=True)
        element_text_lower = element_text.lower()
        
        # Look for "Joining Fee: ₹10,000+ Taxes" pattern
        if 'joining fee' in element_text_lower:
            joining_matches = re.findall(r'joining fee[:\s]*₹?\s*([0-9,]+)', element_text_lower)
            if joining_matches and not joining_fee:
                joining_fee = parse_fee_amount(joining_matches[0])
        
        # Look for "Annual/Renewal Fee: ..." pattern
        if any(fee_type in element_text_lower for fee_type in ['annual fee', 'renewal fee', 'annual/renewal fee']):
            annual_matches = re.findall(r'(?:annual|renewal)[\s/]*fee[:\s]*₹?\s*([0-9,]+)', element_text_lower)
            if annual_matches and not annual_fee:
                annual_fee = parse_fee_amount(annual_matches[0])
    
    # Method 2: Fallback to broader text search if structured search failed
    if not joining_fee or not annual_fee:
        section_text_lower = section_text.lower()
        
        # Extract joining fee if not found
        if not joining_fee:
            joining_matches = re.findall(r'joining fee[:\s]*₹?\s*([0-9,]+)', section_text_lower)
            if joining_matches:
                joining_fee = parse_fee_amount(joining_matches[0])
        
        # Extract annual/renewal fee if not found
        if not annual_fee:
            annual_matches = re.findall(r'(?:annual|renewal)[\s/]*fee[:\s]*₹?\s*([0-9,]+)', section_text_lower)
            if annual_matches:
                annual_fee = parse_fee_amount(annual_matches[0])
    
    # Determine bank from card name
    bank = "Unknown"
    bank_patterns = {
        'hdfc': 'HDFC Bank',
        'axis': 'Axis Bank',
        'icici': 'ICICI Bank', 
        'sbi': 'State Bank of India',
        'yes bank': 'YES Bank',
        'american express': 'American Express',
        'kotak': 'Kotak Mahindra Bank',
        'standard chartered': 'Standard Chartered',
        'hsbc': 'HSBC India',
        'rbl': 'RBL Bank',
        'indusind': 'IndusInd Bank',
        'federal': 'Federal Bank'
    }
    
    card_name_lower = card_name.lower()
    for pattern, bank_name in bank_patterns.items():
        if pattern in card_name_lower:
            bank = bank_name
            break
    
    # 3. Structure the card data
    card_data = {
        "id": len(cards) + 1,
        "card_name": card_name,
        "bank": bank,
        "official_card_image": card_image,
        "joining_fees": joining_fee,
        "annual_fees": annual_fee,
        "currency": "INR",
        "categories": list(set(categories)) if categories else [],
        "features": list(set(features))[:5] if features else [],  # Limit to top 5 unique features
        "extracted_from": "paisabazaar.com"
    }
    
    cards.append(card_data)

# 4. Output structured JSON
output_data = {
    "credit_cards": cards,
    "metadata": {
        "total_cards_extracted": len(cards),
        "source": "paisabazaar.com", 
        "extraction_date": "2025-08-21",
        "extraction_method": "Targeted HTML structure parsing",
        "html_structure": "div.flex.gap-[30px] > div.flex.flex-col.gap-4.w-full > div.w-full.flex.border",
        "note": "Extracted using precise HTML structure targeting as specified"
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
