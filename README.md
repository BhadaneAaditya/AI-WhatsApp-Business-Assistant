A production-ready MVP for an AI-powered WhatsApp business assistant that automatically responds to customer messages using LLMs while maintaining conversation memory and extracting structured business data.

## Features

- **WhatsApp Cloud API Integration**: Receive and send messages via Meta's WhatsApp Business API
- **AI-Powered Responses**: OpenAI GPT-3.5 integration for contextual, intelligent replies
- **Conversation Memory**: PostgreSQL database stores all conversations for context
- **Lead Classification**: Automatic classification as hot/warm/cold based on keywords
- **Order Extraction**: Extracts product, quantity, and price from messages
- **Follow-up Automation**: Automatic follow-up messages for inactive customers
- **Dashboard**: REST endpoints to view conversations and statistics

## Project Structure

```
whatsapp-ai-assistant/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── database/               # Database configuration
│   │   ├── __init__.py
│   ├── models/                 # SQLAlchemy models
│   │   ├── user.py            # User model with lead status
│   │   ├── message.py        # Message model for conversations
│   ├── routes/                # API endpoints
│   │   ├── webhook.py        # WhatsApp webhook handler
│   │   ├── message.py        # Send message endpoints
│   │   ├── dashboard.py      # Dashboard endpoints
│   ├── services/              # Business logic
│   │   ├── user_service.py   # User & lead management
│   │   ├── ai_service.py     # OpenAI integration
│   │   ├── whatsapp_service.py # WhatsApp API client
│   │   ├── scheduler_service.py # Follow-up automation
│   └── utils/                 # Utilities
│       ├── config.py         # Configuration management
│       ├── logging.py        # Logging setup
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Prerequisites

1. **Python 3.9+** installed
2. **PostgreSQL** database running locally or remotely
3. **WhatsApp Cloud API** credentials from Meta Developer Portal
4. **OpenAI API Key** from OpenAI platform

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
cd whatsapp-ai-assistant
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/whatsapp_ai

# WhatsApp Cloud API
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_secure_token
WHATSAPP_ACCESS_TOKEN=your_access_token

# OpenAI
OPENAI_API_KEY=sk-...

# Application
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
FOLLOWUP_TIMEOUT_HOURS=24
```

### 3. Create Database

```bash
psql -U postgres -c "CREATE DATABASE whatsapp_ai;"
```

### 4. Run the Application

```bash
python -m app.main
```

The server will start at `http://localhost:8000`

## API Endpoints

### Webhook

- **GET** `/webhook` - WhatsApp webhook verification
- **POST** `/webhook` - Receive WhatsApp messages

### Message

- **POST** `/send-message` - Send a manual message
- **POST** `/send-message/ai-generate` - Generate AI response without sending

### Dashboard

- **GET** `/dashboard/users` - List all users
- **GET** `/dashboard/users/{phone_number}` - Get specific user
- **GET** `/dashboard/users/{phone_number}/messages` - Get conversation history
- **GET** `/dashboard/stats` - Get statistics

## WhatsApp Configuration

1. Create a Meta Developer account at https://developers.facebook.com/
2. Create a new App and add WhatsApp product
3. Get your Phone Number ID and Access Token
4. Set webhook URL to your deployed endpoint (e.g., ngrok)
5. Verify webhook with the token you set in `.env`

## Testing with ngrok

For local development, use ngrok to expose your local server:

```bash
ngrok http 8000
```

Use the ngrok URL as your webhook callback URL in Meta Developer Portal.

## Example Conversations

- User: "I want to buy some shoes" → Classification: WARM
- User: "What's the price? I'll buy 2 pairs" → Classification: HOT, Order: {product: "shoes", quantity: 2}
- User: "Thanks, that's all for now" → No lead status change
