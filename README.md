# PartSelect RAG Chat

## Tech Stack
- **Frontend**: React + Vite
- **Backend**: FastAPI, Pydantic AI
- **Database**: Supabase (vector storage)
- **Embedding**: OpenAI Embeddings

## Architecture Highlights

### Tool Chaining
- Processes user queries through specialized tools based on content
- Combines results from multiple tools for comprehensive answers

### Memory Storage
- Maintains conversation history across user sessions
- Preserves context for follow-up questions and references

### Recursive Processing
- Uses recursion to gather links on a page

## Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Frontend
```bash
cd frontend/rag_app
npm install
npm run dev
```

### Database
Run the sql script in Supabase SQL Editor to create tables and functions

## Environment Variables
Create a `.env` file with:
```
OPENAI_API_KEY=your_key_here
SUPABASE_URL=your_url_here
SUPABASE_SERVICE_KEY=your_key_here
```
