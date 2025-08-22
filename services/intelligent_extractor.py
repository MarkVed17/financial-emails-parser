import google.generativeai as genai
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

class IntelligentExtractor:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')  # Fixed model name
        else:
            self.model = None
            print("Warning: GEMINI_API_KEY not found. Using rule-based extraction only.")
    
    def extract_financial_insights(self, email_content: str, email_from: str, subject: str) -> Dict:
        """Extract comprehensive financial insights using Gemini AI"""
        
        if not self.model:
            return self._fallback_extraction(email_content, email_from, subject)
        
        prompt = f"""
Analyze this email for CREDIT CARD SPECIFIC financial insights. Focus ONLY on credit card transactions, statements, and card-related information.

Email From: {email_from}
Subject: {subject}
Content: {email_content}

Extract and return ONLY valid JSON (no markdown, no explanation):
{{
  "transaction": {{
    "merchant": "actual merchant name charged to credit card (null if not a card transaction)",
    "amount": numeric_amount_only,
    "currency": "INR/USD/etc",
    "date": "YYYY-MM-DD",
    "category": "Food/Shopping/Transportation/Entertainment/Bills/Healthcare/Education/Travel/Other",
    "transaction_type": "expense/income/transfer",
    "card_type": "credit_card/debit_card/null",
    "card_last_four": "last 4 digits if available or null",
    "confidence": 0.0-1.0
  }},
  "subscription": {{
    "service": "subscription service charged to credit card",
    "amount": numeric_amount,
    "billing_cycle": "monthly/yearly/weekly", 
    "next_billing": "YYYY-MM-DD",
    "charged_to_card": true/false
  }},
  "travel": {{
    "airline": "airline name (if charged to card)",
    "hotel": "hotel chain name (if charged to card)", 
    "destination": "city/country",
    "travel_date": "YYYY-MM-DD",
    "booking_amount": numeric_amount,
    "charged_to_card": true/false
  }},
  "bills": {{
    "utility_type": "electricity/gas/internet/mobile/insurance (if charged to card)",
    "provider": "company name",
    "amount": numeric_amount,
    "due_date": "YYYY-MM-DD",
    "charged_to_card": true/false
  }},
  "card_info": {{
    "card_statement": true/false,
    "statement_period": "YYYY-MM to YYYY-MM",
    "total_amount_due": numeric_amount,
    "minimum_due": numeric_amount,
    "due_date": "YYYY-MM-DD",
    "available_limit": numeric_amount,
    "rewards_earned": numeric_amount,
    "cashback_earned": numeric_amount
  }},
  "is_relevant": true/false
}}

FOCUS RULES:
- ONLY extract if it's related to CREDIT CARD usage, statements, or payments
- Ignore salary, bank transfers, UPI payments, wallet transactions unless charged to credit card
- Set is_relevant to false for non-credit card financial activities
- Prioritize card transaction data over other categories
- Extract card-specific information like last 4 digits, card statements, rewards
"""

        try:
            response = self.model.generate_content(prompt)
            # Clean response to extract JSON
            response_text = response.text.strip()
            
            # Remove markdown formatting if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            return json.loads(response_text)
            
        except Exception as e:
            print(f"Gemini extraction failed: {e}")
            return self._fallback_extraction(email_content, email_from, subject)
    
    def _fallback_extraction(self, email_content: str, email_from: str, subject: str) -> Dict:
        """Fallback rule-based extraction when AI is not available - CREDIT CARD FOCUSED"""
        
        # Initialize default structure - CREDIT CARD FOCUSED
        result = {
            "transaction": None,
            # "income": None,  # COMMENTED OUT - Not relevant for credit card focus
            "subscription": None,
            "travel": None,
            "bills": None,
            # "investment": None,  # COMMENTED OUT - Not relevant for credit card focus
            "card_info": None,
            "is_relevant": False
        }
        
        text = f"{subject} {email_content}".lower()
        
        # Check if it's a CREDIT CARD email - Updated keywords
        credit_card_keywords = ['card', 'credit card', 'transaction', 'charged', 'statement', 'payment', 'purchase', 'bill']
        if not any(keyword in text for keyword in credit_card_keywords):
            return result
        
        result["is_relevant"] = True
        
        # Extract credit card transaction
        merchant = self._extract_clean_merchant(email_from, subject)
        amount = self._extract_amount(text)
        
        if merchant and amount:
            result["transaction"] = {
                "merchant": merchant,
                "amount": amount,
                "currency": "INR",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "category": self._categorize_merchant(merchant),
                "transaction_type": "expense",
                "card_type": "credit_card",  # Assume credit card for fallback
                "card_last_four": None,  # Can't extract in fallback
                "confidence": 0.7
            }
        
        return result
    
    def _extract_clean_merchant(self, email_from: str, subject: str) -> Optional[str]:
        """Extract clean merchant name, filtering out noise"""
        
        # Known merchants mapping
        merchant_patterns = {
            'swiggy': 'Swiggy',
            'zomato': 'Zomato',
            'amazon': 'Amazon',
            'flipkart': 'Flipkart',
            'uber': 'Uber',
            'ola': 'Ola',
            'paytm': 'Paytm',
            'phonepe': 'PhonePe',
            'gpay': 'Google Pay',
            'myntra': 'Myntra',
            'bigbasket': 'BigBasket',
            'netflix': 'Netflix',
            'spotify': 'Spotify',
            'airtel': 'Airtel',
            'jio': 'Jio',
            'hdfc': 'HDFC Bank',
            'icici': 'ICICI Bank',
            'sbi': 'SBI',
            'axis': 'Axis Bank'
        }
        
        text = f"{email_from} {subject}".lower()
        
        # Check known merchants first
        for pattern, name in merchant_patterns.items():
            if pattern in text:
                return name
        
        # Extract from domain
        domain_match = re.search(r'@([^.]+)', email_from)
        if domain_match:
            domain = domain_match.group(1).lower()
            for pattern, name in merchant_patterns.items():
                if pattern in domain:
                    return name
        
        # Avoid noise words
        noise_words = {'you', 'your', 'rs', 'view', 'fwd', 'account', 'alert', 'update', 'payment', 'scheduled'}
        
        # Extract merchant from subject
        words = re.findall(r'\b[A-Z][a-z]+\b', subject)
        for word in words:
            if word.lower() not in noise_words and len(word) > 2:
                return word
        
        return None
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract amount from text"""
        patterns = [
            r'(?:₹|inr|rs\.?)\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'([0-9,]+(?:\.[0-9]{2})?)\s*(?:₹|inr|rs\.?)',
            r'(?:amount|total|paid|charged).*?(?:₹|inr|rs\.?)\s*([0-9,]+(?:\.[0-9]{2})?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    amount = float(matches[0].replace(',', ''))
                    if 1 <= amount <= 1000000:  # Reasonable range
                        return amount
                except ValueError:
                    continue
        
        return None
    
    def _categorize_merchant(self, merchant: str) -> str:
        """Categorize merchant"""
        categories = {
            'Food': ['swiggy', 'zomato', 'dominos', 'kfc', 'mcdonald'],
            'Shopping': ['amazon', 'flipkart', 'myntra', 'ajio'],
            'Transportation': ['uber', 'ola', 'rapido'],
            'Entertainment': ['netflix', 'spotify', 'hotstar', 'prime'],
            'Bills': ['airtel', 'jio', 'bsnl', 'electricity', 'gas'],
            'Healthcare': ['practo', 'apollo', 'pharmeasy'],
            'Travel': ['makemytrip', 'goibibo', 'cleartrip', 'irctc']
        }
        
        merchant_lower = merchant.lower()
        for category, merchants in categories.items():
            if any(m in merchant_lower for m in merchants):
                return category
        
        return 'Other'
    
    def extract_insights_batch(self, emails: List[Dict], batch_size: int = 5) -> List[Dict]:
        """Process multiple emails in batches for better performance"""
        
        if not emails:
            return []
        
        results = []
        
        # Process in smaller batches to avoid timeout
        for i in range(0, len(emails), batch_size):
            batch = emails[i:i+batch_size]
            
            if self.model:
                # Try batch processing with AI
                try:
                    batch_results = self._process_batch_with_ai(batch)
                    results.extend(batch_results)
                except Exception as e:
                    print(f"Batch AI processing failed: {e}")
                    # Fallback to individual processing
                    for email in batch:
                        result = self.extract_financial_insights(
                            email.get('bodyText', ''),
                            email.get('from', ''),
                            email.get('subject', '')
                        )
                        result['email_id'] = email.get('id')
                        results.append(result)
            else:
                # Use rule-based extraction for batch
                for email in batch:
                    result = self.extract_financial_insights(
                        email.get('bodyText', ''),
                        email.get('from', ''),
                        email.get('subject', '')
                    )
                    result['email_id'] = email.get('id')
                    results.append(result)
        
        return results
    
    def _process_batch_with_ai(self, emails: List[Dict]) -> List[Dict]:
        """Process multiple emails in a single AI call"""
        
        if not self.model or not emails:
            return []
        
        # Format emails for batch processing
        email_texts = []
        for i, email in enumerate(emails):
            email_text = f"""
Email {i+1}:
From: {email.get('from', '')}
Subject: {email.get('subject', '')}
Content: {email.get('bodyText', '')[:500]}
---
"""
            email_texts.append(email_text)
        
        batch_prompt = f"""
Analyze these {len(emails)} emails for CREDIT CARD SPECIFIC insights. Focus ONLY on credit card transactions, statements, and card-related information.

{chr(10).join(email_texts)}

Return ONLY a JSON array with {len(emails)} objects in this exact format:
[
  {{
    "email_index": 1,
    "transaction": {{"merchant": "name or null", "amount": number_or_null, "currency": "INR", "date": "YYYY-MM-DD", "category": "Food/Shopping/etc", "transaction_type": "expense", "card_type": "credit_card/debit_card/null", "card_last_four": "digits or null", "confidence": 0.8}},
    "subscription": {{"service": "name or null", "amount": number_or_null, "billing_cycle": "monthly", "next_billing": "YYYY-MM-DD", "charged_to_card": true_or_false}},
    "travel": {{"airline": "name or null", "hotel": "name or null", "destination": "city", "travel_date": "YYYY-MM-DD", "booking_amount": number_or_null, "charged_to_card": true_or_false}},
    "bills": {{"utility_type": "type or null", "provider": "name or null", "amount": number_or_null, "due_date": "YYYY-MM-DD", "charged_to_card": true_or_false}},
    "card_info": {{"card_statement": true_or_false, "statement_period": "YYYY-MM to YYYY-MM", "total_amount_due": number_or_null, "minimum_due": number_or_null, "due_date": "YYYY-MM-DD", "available_limit": number_or_null, "rewards_earned": number_or_null, "cashback_earned": number_or_null}},
    "is_relevant": true_or_false
  }}
]

FOCUS RULES:
- ONLY extract if related to CREDIT CARD usage, statements, or payments
- Set is_relevant to false for non-credit card financial activities
- Prioritize card transaction data over other categories
"""
        
        try:
            response = self.model.generate_content(batch_prompt)
            response_text = response.text.strip()
            
            # Clean response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            batch_results = json.loads(response_text)
            
            # Map results back to emails
            final_results = []
            for i, email in enumerate(emails):
                if i < len(batch_results):
                    result = batch_results[i]
                    result['email_id'] = email.get('id')
                    final_results.append(result)
                else:
                    # Fallback if batch result is missing
                    result = self._fallback_extraction(
                        email.get('bodyText', ''),
                        email.get('from', ''),
                        email.get('subject', '')
                    )
                    result['email_id'] = email.get('id')
                    final_results.append(result)
            
            return final_results
            
        except Exception as e:
            print(f"Batch AI processing error: {e}")
            # Fallback to individual processing
            results = []
            for email in emails:
                result = self.extract_financial_insights(
                    email.get('bodyText', ''),
                    email.get('from', ''),
                    email.get('subject', '')
                )
                result['email_id'] = email.get('id')
                results.append(result)
            return results