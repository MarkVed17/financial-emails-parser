import re
from datetime import datetime
from typing import List, Dict, Optional

class TransactionExtractor:
    def __init__(self):
        # Common merchant patterns
        self.merchant_patterns = {
            'swiggy': r'(?i)swiggy',
            'zomato': r'(?i)zomato', 
            'amazon': r'(?i)amazon',
            'flipkart': r'(?i)flipkart',
            'paytm': r'(?i)paytm',
            'uber': r'(?i)uber',
            'ola': r'(?i)ola',
            'myntra': r'(?i)myntra',
            'bigbasket': r'(?i)bigbasket',
            'phonepe': r'(?i)phonepe',
            'gpay': r'(?i)google pay|gpay',
        }
        
        # Amount patterns - support multiple currencies
        self.amount_patterns = [
            r'(?:₹|INR|Rs\.?)\s*([0-9,]+(?:\.[0-9]{2})?)',  # Indian Rupee
            r'(?:\$|USD)\s*([0-9,]+(?:\.[0-9]{2})?)',       # US Dollar
            r'(?:€|EUR)\s*([0-9,]+(?:\.[0-9]{2})?)',        # Euro
            r'([0-9,]+(?:\.[0-9]{2})?)\s*(?:₹|INR|Rs\.?)',  # Amount before currency
            r'(?:amount|total|paid|charged).*?(?:₹|INR|Rs\.?)\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'(?:₹|INR|Rs\.?)\s*([0-9,]+)',  # Without decimal
        ]
        
        # Date patterns
        self.date_patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',  # DD/MM/YYYY or MM/DD/YYYY
            r'(\d{2,4}[-/]\d{1,2}[-/]\d{1,2})',  # YYYY/MM/DD
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{2,4})',  # DD MMM YYYY
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{2,4})',  # MMM DD, YYYY
        ]
        
        # Transaction keywords to filter relevant emails
        self.transaction_keywords = [
            'order', 'payment', 'invoice', 'receipt', 'transaction', 'purchase',
            'charged', 'paid', 'booking', 'confirmation', 'bill', 'checkout'
        ]
        
        # Category mapping
        self.category_mapping = {
            'swiggy': 'Food',
            'zomato': 'Food',
            'amazon': 'Shopping',
            'flipkart': 'Shopping',
            'myntra': 'Shopping',
            'bigbasket': 'Groceries',
            'uber': 'Transportation',
            'ola': 'Transportation',
            'paytm': 'Digital Wallet',
            'phonepe': 'Digital Wallet',
            'gpay': 'Digital Wallet',
        }
    
    def extract_transactions(self, parsed_email: Dict) -> List[Dict]:
        """Extract transaction data from parsed email"""
        transactions = []
        
        # Check if email is transaction-related
        if not self._is_transaction_email(parsed_email):
            return transactions
        
        # Extract merchant
        merchant = self._extract_merchant(parsed_email)
        if not merchant:
            return transactions
        
        # Extract amount
        amount = self._extract_amount(parsed_email)
        if not amount:
            return transactions
        
        # Extract date (fallback to email date)
        date = self._extract_date(parsed_email)
        
        # Get category
        category = self._get_category(merchant)
        
        transaction = {
            'merchant': merchant,
            'amount': amount,
            'date': date,
            'category': category,
            'email_id': parsed_email.get('id', ''),
            'confidence': self._calculate_confidence(merchant, amount, date)
        }
        
        transactions.append(transaction)
        return transactions
    
    def _is_transaction_email(self, email: Dict) -> bool:
        """Check if email contains transaction-related content"""
        text = (email.get('subject', '') + ' ' + email.get('bodyText', '')).lower()
        
        # Check for transaction keywords
        for keyword in self.transaction_keywords:
            if keyword in text:
                return True
        
        # Check for amount patterns
        for pattern in self.amount_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _extract_merchant(self, email: Dict) -> Optional[str]:
        """Extract merchant name from email"""
        text = email.get('subject', '') + ' ' + email.get('bodyText', '') + ' ' + email.get('from', '')
        
        # Check against known merchant patterns
        for merchant, pattern in self.merchant_patterns.items():
            if re.search(pattern, text):
                return merchant.title()
        
        # Extract from email sender domain
        from_email = email.get('from', '')
        domain_match = re.search(r'@([^.]+)', from_email)
        if domain_match:
            domain = domain_match.group(1).lower()
            # Check if domain matches known merchants
            for merchant in self.merchant_patterns.keys():
                if merchant in domain:
                    return merchant.title()
        
        # Fallback: extract from subject line
        subject = email.get('subject', '')
        words = re.findall(r'\b[A-Z][a-z]+\b', subject)
        if words:
            return words[0]
        
        return None
    
    def _extract_amount(self, email: Dict) -> Optional[float]:
        """Extract transaction amount from email"""
        text = email.get('subject', '') + ' ' + email.get('bodyText', '')
        
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        # Clean amount string
                        amount_str = match.replace(',', '')
                        amount = float(amount_str)
                        # Filter out unreasonable amounts
                        if 1 <= amount <= 1000000:  # Between ₹1 and ₹10L
                            return amount
                    except ValueError:
                        continue
        
        return None
    
    def _extract_date(self, email: Dict) -> str:
        """Extract transaction date from email"""
        text = email.get('subject', '') + ' ' + email.get('bodyText', '')
        
        # Try to find date in email content
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    # Parse and format date
                    date_str = matches[0]
                    parsed_date = self._parse_date(date_str)
                    if parsed_date:
                        return parsed_date.strftime('%Y-%m-%d')
                except:
                    continue
        
        # Fallback to email internal date
        internal_date = email.get('internalDate', '')
        if internal_date:
            try:
                # Convert milliseconds to datetime
                timestamp = int(internal_date) / 1000
                date = datetime.fromtimestamp(timestamp)
                return date.strftime('%Y-%m-%d')
            except:
                pass
        
        # Final fallback to current date
        return datetime.now().strftime('%Y-%m-%d')
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        date_formats = [
            '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d',
            '%d-%m-%Y', '%m-%d-%Y', '%Y-%m-%d',
            '%d %b %Y', '%d %B %Y',
            '%b %d, %Y', '%B %d, %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _get_category(self, merchant: str) -> str:
        """Get category for merchant"""
        merchant_lower = merchant.lower()
        return self.category_mapping.get(merchant_lower, 'Other')
    
    def _calculate_confidence(self, merchant: str, amount: float, date: str) -> float:
        """Calculate confidence score for extraction"""
        confidence = 0.0
        
        # Merchant confidence
        if merchant and merchant.lower() in self.merchant_patterns:
            confidence += 0.4
        elif merchant:
            confidence += 0.2
        
        # Amount confidence
        if amount and 1 <= amount <= 100000:
            confidence += 0.4
        elif amount:
            confidence += 0.2
        
        # Date confidence
        if date:
            confidence += 0.2
        
        return min(confidence, 1.0)