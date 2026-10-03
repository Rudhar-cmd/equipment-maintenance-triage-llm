# Quick Start

Open four terminals.

## 1. MongoDB
Run local MongoDB, or change `backend/.env` to your MongoDB Atlas URI.

## 2. AI service
```bash
cd ai-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Set:
```env
OPENAI_API_KEY=your_real_key
OPENAI_MODEL=gpt-4o-mini
```
Then:
```bash
uvicorn main:app --reload --port 8002
```

Test:
```bash
curl http://localhost:8002/health
```

## 3. Backend
```bash
cd backend
npm install
cp .env.example .env
npm run dev
```

## 4. Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open the Vite URL.

Never put the OpenAI API key in the frontend.
