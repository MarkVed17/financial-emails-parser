from bs4 import BeautifulSoup
import base64
import re

class EmailParser:
    def __init__(self):
        pass
    
    def parse_email(self, email_data):
        """Parse Gmail API response to extract required fields"""
        parsed_email = {
            'id': email_data.get('id', ''),
            'internalDate': email_data.get('internalDate', ''),
            'from': '',
            'subject': '',
            'bodyText': ''
        }
        
        # Extract headers
        headers = email_data.get('payload', {}).get('headers', [])
        parsed_email['from'] = self._get_header_value(headers, 'From')
        parsed_email['subject'] = self._get_header_value(headers, 'Subject')
        
        # Extract body text
        parsed_email['bodyText'] = self._extract_body_text(email_data.get('payload', {}))
        
        return parsed_email
    
    def _get_header_value(self, headers, name):
        """Extract header value by name"""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return ""
    
    def _extract_body_text(self, payload):
        """Extract text content from email payload"""
        body_text = ""
        
        # Handle multipart messages
        if 'parts' in payload:
            for part in payload['parts']:
                body_text += self._extract_text_from_part(part)
        else:
            # Single part message
            body_text = self._extract_text_from_part(payload)
        
        return self._clean_text(body_text)
    
    def _extract_text_from_part(self, part):
        """Extract text from a single message part"""
        mime_type = part.get('mimeType', '')
        
        if mime_type == 'text/plain':
            data = part.get('body', {}).get('data', '')
            if data:
                return self._decode_base64(data)
        
        elif mime_type == 'text/html':
            data = part.get('body', {}).get('data', '')
            if data:
                html_content = self._decode_base64(data)
                return self._html_to_text(html_content)
        
        elif 'parts' in part:
            # Recursive for nested multipart
            text = ""
            for subpart in part['parts']:
                text += self._extract_text_from_part(subpart)
            return text
        
        return ""
    
    def _decode_base64(self, data):
        """Decode base64 encoded data"""
        try:
            decoded = base64.urlsafe_b64decode(data).decode('utf-8')
            return decoded
        except Exception:
            return ""
    
    def _html_to_text(self, html_content):
        """Convert HTML to plain text"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text(separator=' ', strip=True)
        except Exception:
            return html_content
    
    def _clean_text(self, text):
        """Clean and normalize text content"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove common email artifacts
        text = re.sub(r'=\d{2}', '', text)  # Remove quoted-printable artifacts
        text = text.strip()
        return text