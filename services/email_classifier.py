import re
from typing import List, Dict, Tuple
from enum import Enum

class EmailRelevance(Enum):
    DEFINITELY_FINANCIAL = "definitely_financial"
    MAYBE_FINANCIAL = "maybe_financial"
    PROBABLY_NOT_FINANCIAL = "probably_not"

class EmailClassifier:
    def __init__(self):
        # CREDIT CARD FOCUSED FILTERING - High confidence patterns
        self.definitely_financial_patterns = [
            # Direct credit card transaction patterns
            r'\b(credit card|card|transaction|charged|payment|purchase)\b.*[₹$€]\s*\d+',
            r'\b(card ending|card.*\d{4}|xxxx\d{4}|\*{4}\d{4})\b',
            # Credit card transaction confirmations
            r'\b(transaction.*successful|payment.*completed|purchase.*confirmed)\b',
            # Credit card statement patterns
            r'\b(statement|monthly statement|billing statement|card statement)\b',
            # Card merchant transactions with amounts
            r'\b(swiggy|zomato|amazon|flipkart|uber|ola|paytm|phonepe|gpay)\b.*[₹$€]\s*\d+',
            # Credit card payment confirmations
            r'\b(payment.*received|bill.*paid|auto.*debit|emi.*deducted)\b',
            # Credit card specific terms with amounts
            r'\b(available.*limit|credit.*limit|outstanding.*amount|minimum.*due)\b'
        ]
        
        # CREDIT CARD FOCUSED - Potential patterns  
        self.maybe_financial_patterns = [
            # Credit card brands and issuers
            r'\b(hdfc.*card|icici.*card|sbi.*card|axis.*card|kotak.*card|yes.*bank.*card|citibank.*card)\b',
            r'\b(visa|mastercard|rupay|amex|american express)\b',
            # Credit card related services
            r'\b(card.*blocked|card.*unblocked|card.*activated|card.*deactivated)\b',
            r'\b(reward.*points|cashback|reward.*earned|points.*credited)\b',
            r'\b(credit.*limit.*increased|limit.*enhanced|credit.*line)\b',
            # Credit card EMI and finance
            r'\b(emi|equated monthly installment|convert.*emi|emi.*conversion)\b',
            # Credit card security and alerts
            r'\b(card.*used|international.*transaction|online.*transaction|pos.*transaction)\b',
            r'\b(otp.*card|cvv|card.*verification|secure.*transaction)\b',
            # Credit card bill and statement related
            r'\b(due.*date|payment.*due|bill.*generated|statement.*ready)\b',
            r'\b(auto.*pay|autopay|scheduled.*payment|standing.*instruction)\b'
        ]
        
        # COMMENTED OUT - Broader financial patterns not credit card specific
        # # Travel and hospitality  
        # r'\b(booking|reservation|hotel|flight|airline|travel|trip)\b',
        # r'\b(marriott|taj|hilton|hyatt|radisson|oberoi|itc|airline|airways)\b',
        # r'\b(makemytrip|goibibo|cleartrip|yatra|booking\.com|agoda)\b',
        # # Subscriptions and services
        # r'\b(subscription|renewal|plan|membership|premium)\b', 
        # r'\b(netflix|spotify|amazon prime|hotstar|zee5|sony liv|youtube premium)\b',
        # r'\b(adobe|microsoft|google workspace|office 365)\b',
        # # Utilities and services
        # r'\b(electricity|gas|water|internet|mobile|broadband|wifi)\b',
        # r'\b(airtel|jio|vodafone|bsnl|tata|reliance)\b',
        # # Employment and income
        # r'\b(salary|payroll|bonus|incentive|commission|freelance)\b',
        # r'\b(credited to your account|salary credit|payment received)\b',
        # # General banking
        # r'\b(transfer|withdrawal|deposit|balance|account)\b',
        
        # AGGRESSIVE EXCLUDE PATTERNS - Exclude everything that's not credit card related
        self.exclude_patterns = [
            # Marketing and promotional
            r'\b(newsletter|unsubscribe|promotional|marketing|advertisement)\b',
            r'\b(sale|discount|offer|deal|coupon|cashback offer|mega sale)\b',
            r'\b(limited time|hurry|don\'t miss|exclusive offer|special price)\b',
            # Social and notifications  
            r'\b(notification|reminder|update|news|blog|article)\b',
            r'\b(facebook|twitter|instagram|linkedin|youtube|social)\b',
            # Security and IT (unless card related)
            r'\b(password|login|verification code|2fa)\b(?!.*card)',
            r'\b(virus|malware|phishing|spam|suspicious activity)\b',
            # Non-credit card banking (bank transfers, deposits, etc)
            r'\b(bank transfer|wire transfer|neft|rtgs|imps|upi)\b(?!.*card)',
            r'\b(fixed deposit|fd|savings|salary credit|bonus credit)\b',
            # Non-credit card payments
            r'\b(wallet|digital wallet|paytm wallet|phonepe wallet)\b(?!.*card)',
            # Utilities and services (unless charged to card)
            r'\b(electricity bill|gas bill|water bill|internet bill|mobile bill)\b(?!.*card)',
            # Investments and insurance (unless charged to card)
            r'\b(mutual fund|sip|systematic|insurance premium|policy)\b(?!.*card)',
            # Employment related (unless charged to card)
            r'\b(salary|payroll|bonus|hr|human resources)\b(?!.*card)'
        ]
    
    def classify_email(self, email: Dict) -> EmailRelevance:
        """Classify email relevance using rule-based patterns"""
        
        # Combine subject, from, and first 200 chars of body
        text = f"{email.get('subject', '')} {email.get('from', '')} {email.get('bodyText', '')[:200]}".lower()
        
        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return EmailRelevance.PROBABLY_NOT_FINANCIAL
        
        # Check definitely financial patterns
        for pattern in self.definitely_financial_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return EmailRelevance.DEFINITELY_FINANCIAL
        
        # Check maybe financial patterns
        for pattern in self.maybe_financial_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return EmailRelevance.MAYBE_FINANCIAL
        
        return EmailRelevance.PROBABLY_NOT_FINANCIAL
    
    def classify_emails_batch(self, emails: List[Dict]) -> Dict[str, List[Dict]]:
        """Classify a batch of emails into categories"""
        
        definitely_financial = []
        maybe_financial = []
        probably_not = []
        
        for email in emails:
            classification = self.classify_email(email)
            
            if classification == EmailRelevance.DEFINITELY_FINANCIAL:
                definitely_financial.append(email)
            elif classification == EmailRelevance.MAYBE_FINANCIAL:
                maybe_financial.append(email)
            else:
                probably_not.append(email)
        
        return {
            "definitely_financial": definitely_financial,
            "maybe_financial": maybe_financial,
            "probably_not": probably_not
        }
    
    def get_classification_stats(self, classification_result: Dict) -> Dict:
        """Get statistics about email classification"""
        
        total = sum(len(emails) for emails in classification_result.values())
        
        return {
            "total_emails": total,
            "definitely_financial": len(classification_result["definitely_financial"]),
            "maybe_financial": len(classification_result["maybe_financial"]),
            "probably_not": len(classification_result["probably_not"]),
            "will_process_with_ai": len(classification_result["definitely_financial"]) + len(classification_result["maybe_financial"]),
            "ai_processing_reduction": round((len(classification_result["probably_not"]) / total * 100), 1) if total > 0 else 0
        }