# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a financial transaction tracking system that extracts purchase and payment information from Gmail emails. The system uses Google OAuth to access emails, parses them for transaction data, and transforms unstructured email content into structured financial records.

### Core Features
- Google OAuth 2.0 authentication with Gmail API access
- Fetch and parse emails from the past 6 months
- Extract structured transaction data: merchant, amount, date, category
- Transform emails into financial insights and spending analytics

### Data Pipeline
1. **Email Ingestion**: Gmail API → Raw email data
2. **Email Parsing**: Extract `{id, internalDate, from, subject, bodyText}`
3. **Information Extraction**: Transform to `{merchant, amount, date, category}`
4. **Data Storage**: Structured transaction records for analysis

## Development Setup

### Technology Stack
**Backend Options:**
- **Node.js**: Express, googleapis, cheerio, natural/compromise
- **Python**: FastAPI, google-api-python-client, beautifulsoup4, spacy

**Database**: PostgreSQL/MongoDB for emails and transactions

**AI/ML**: OpenAI API or local NLP models for intelligent extraction

### Required Dependencies

**Node.js:**
```bash
npm install express googleapis passport-google-oauth20 cheerio natural mongoose joi dotenv
```

**Python (Poetry - Recommended):**
```bash
poetry install
```

**Python (pip):**
```bash
pip install fastapi uvicorn google-auth google-auth-oauthlib google-api-python-client beautifulsoup4 google-generativeai pydantic python-dotenv
```

### Environment Variables
- `GOOGLE_CLIENT_ID`: OAuth client ID
- `GOOGLE_CLIENT_SECRET`: OAuth client secret  
- `GOOGLE_REDIRECT_URI`: OAuth redirect URI
- `GEMINI_API_KEY`: Google Gemini API key for intelligent extraction

## Common Commands

```bash
# Install dependencies (Poetry - Recommended)
poetry install

# Install dependencies (pip alternative)
pip install -r requirements.txt

# Run the application
poetry run python main.py
# OR
python main.py

# Set up environment variables
cp .env.example .env
# Edit .env with your Google OAuth + Gemini API credentials
```

### API Endpoints
- `GET /`: Health check
- `GET /auth/login`: Get Google OAuth login URL
- `GET /auth/callback?code=<auth_code>`: Handle OAuth callback
- `GET /emails/fetch?access_token=<token>&limit=<number>`: Fetch and parse emails
- `GET /transactions/extract?access_token=<token>&limit=<number>`: Extract basic transactions (legacy)
- `GET /insights/intelligent?access_token=<token>&limit=<number>`: AI-powered financial insights extraction
- `GET /analytics/comprehensive?access_token=<token>&limit=<number>`: Complete financial analytics and patterns

## Architecture Notes

### System Components

1. **Auth Service**: Google OAuth 2.0 flow management
2. **Gmail Sync Service**: Email fetching with pagination and rate limiting
3. **Email Parser**: Extract core email fields from JSON response
4. **Legacy Transaction Extractor**: Rule-based transaction extraction
5. **Intelligent Extractor**: Gemini AI-powered comprehensive financial insights
6. **Analytics Service**: Advanced financial pattern analysis and insights
7. **API Layer**: RESTful endpoints for different extraction methods

### New AI-Powered Features

**Intelligent Extraction (`/insights/intelligent`)**:
- Gemini AI analyzes email content for comprehensive financial data
- Extracts: transactions, income, subscriptions, travel, bills, investments
- Filters out noise and irrelevant emails automatically
- Provides confidence scoring for all extractions

**Comprehensive Analytics (`/analytics/comprehensive`)**:
- **Spending Analysis**: Category breakdown, monthly trends, top merchants
- **Income Analysis**: Employer detection, pay cycles, monthly income tracking
- **Subscription Analysis**: Recurring services, monthly costs, billing cycles
- **Travel Analysis**: Preferred airlines, hotels, destinations, travel spending
- **Bills Analysis**: Utility breakdown, service providers, monthly bills
- **Investment Analysis**: Platforms, instruments, net investment tracking
- **Financial Health**: Savings rate, subscription ratio, health score

### Database Schema
```sql
-- Users table
users (id, google_id, email, tokens, created_at)

-- Raw emails table  
emails (id, user_id, gmail_id, internal_date, from_address, subject, body_text, processed)

-- Extracted transactions
transactions (id, email_id, merchant, amount, currency, date, category, confidence_score)

-- Categories reference
categories (id, name, type, keywords)
```

### Information Extraction Pipeline

**Stage 1: Email Filtering**
- Filter emails from known merchants/financial institutions
- Identify transactional patterns (receipts, confirmations, statements)

**Stage 2: Content Parsing**
- Extract HTML/plain text content
- Clean and normalize text data
- Handle multiple languages and formats

**Stage 3: Data Extraction**
- **Rule-based**: Regex patterns for common email formats
- **NLP-based**: Named entity recognition, keyword extraction  
- **AI-powered**: OpenAI/Claude API for complex extraction
- **Hybrid approach**: Combine methods for highest accuracy

**Stage 4: Data Validation**
- Validate extracted amounts and dates
- Categorize transactions automatically
- Flag uncertain extractions for manual review

## Key Considerations

### Security & Privacy
- Secure token storage and refresh handling
- Encrypt sensitive financial data in database
- Implement proper OAuth scopes (readonly Gmail access)
- Handle user consent and data deletion requests (GDPR compliance)
- Never log or expose actual financial amounts in plaintext

### Gmail API Specifics
- Rate limiting: 250 quota units per user per second
- Batch requests for efficiency (up to 100 emails per batch)
- Handle partial failures and retry logic
- Email threading and conversation management
- Process only relevant emails (skip newsletters, promotions)

### Information Extraction Challenges
- **Email Format Diversity**: Merchants use different templates
- **Multi-language Support**: Handle emails in different languages
- **Currency Handling**: Parse various currency formats (₹, $, €)
- **Date Parsing**: Handle different date formats across regions
- **False Positives**: Distinguish actual transactions from marketing emails
- **Ambiguous Data**: Handle cases where amount/merchant is unclear

### Performance & Scalability
- **Incremental Syncing**: Only fetch new emails after initial sync
- **Background Processing**: Queue-based email processing
- **Caching**: Cache extracted data to avoid reprocessing
- **Database Optimization**: Index frequently queried fields
- **Memory Management**: Stream large email volumes instead of loading all

### Data Quality & Accuracy
- **Confidence Scoring**: Rate extraction accuracy (0-1 scale)
- **Manual Review**: Flag low-confidence extractions
- **Learning System**: Improve extraction rules based on user feedback
- **Duplicate Detection**: Avoid processing same transaction multiple times
- **Category Intelligence**: Auto-suggest categories based on merchant patterns

### Development Best Practices
- **Modular Architecture**: Separate extraction engines for different email types
- **Testing Strategy**: Unit tests for extraction logic, integration tests for Gmail API
- **Error Handling**: Graceful degradation when extraction fails
- **Logging**: Detailed logs for debugging extraction issues (without sensitive data)
- **Configuration**: Easily configurable extraction rules and patterns