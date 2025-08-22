from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta
import base64

class GmailService:
    def __init__(self):
        self.service = None
        self.credentials = None
    
    def set_credentials(self, access_token: str):
        """Set credentials using access token"""
        self.credentials = Credentials(token=access_token)
        self.service = build('gmail', 'v1', credentials=self.credentials)
    
    def fetch_emails_last_6_months(self, max_results=None, smart_sampling=False):
        """Fetch ALL emails from the last 6 months (no limit)"""
        if not self.service:
            raise ValueError("Gmail service not initialized. Set credentials first.")
        
        # Calculate date 6 months ago
        six_months_ago = datetime.now() - timedelta(days=180)
        query = f'after:{six_months_ago.strftime("%Y/%m/%d")}'
        
        try:
            # Get ALL messages (no maxResults limit)
            all_messages = []
            page_token = None
            
            while True:
                # Fetch messages page by page
                results = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    pageToken=page_token
                ).execute()
                
                messages = results.get('messages', [])
                all_messages.extend(messages)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            print(f"Found {len(all_messages)} emails in last 6 months")
            
            # Fetch full message details for all emails
            emails = []
            for i, msg in enumerate(all_messages):
                email_data = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                emails.append(email_data)
                
                # Progress indicator for large email volumes
                if (i + 1) % 100 == 0:
                    print(f"Processed {i + 1}/{len(all_messages)} emails...")
            
            return emails
            
        except Exception as e:
            raise Exception(f"Error fetching emails: {str(e)}")
    
    def decode_email_body(self, data):
        """Decode base64 email body"""
        try:
            decoded_data = base64.urlsafe_b64decode(data).decode('utf-8')
            return decoded_data
        except Exception:
            return ""
    
    def get_header_value(self, headers, name):
        """Extract header value by name"""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return ""