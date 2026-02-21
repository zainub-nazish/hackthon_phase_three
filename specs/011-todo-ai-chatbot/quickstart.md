# Quickstart: Todo AI Chatbot (011)

## Prerequisites

- Python 3.11+
- Node.js 18+
- Neon PostgreSQL database
- OpenAI API key

## Environment Setup

### Backend (`backend/.env`)

```env
DATABASE_URL=postgresql+asyncpg://neondb_owner:<password>@<host>/neondb?ssl=require
OPENAI_API_KEY=sk-proj-...
BETTER_AUTH_URL=http://localhost:3000
DEBUG=true
ENVIRONMENT=development
```

### Frontend (`frontend/.env.local`)

```env
BETTER_AUTH_SECRET=<your-secret>
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
DATABASE_URL=postgresql://<neon-connection-string>
```

## Run Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

## Verify

1. Open `http://localhost:3000` — login via Better Auth
2. Navigate to Chat page
3. Type "add a task to buy groceries" — verify task creation
4. Type "show my tasks" — verify task listing
5. Type "complete the groceries task" — verify completion

## Test Backend

```bash
cd backend
pytest tests/ -v
```
