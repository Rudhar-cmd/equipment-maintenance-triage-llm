# Equipment Maintenance Triage Assistant

Full-stack maintenance triage application with React, Node/Express, MongoDB, Python/FastAPI, OpenAI LLM assistance, deterministic threshold checks, evidence retrieval, structured recommendations, human review, and work-order approval.

## Setup

### AI service
```bash
cd ai-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Set `OPENAI_API_KEY` in `ai-service/.env`, then:
```bash
uvicorn main:app --reload --port 8002
```

### Backend
```bash
cd backend
npm install
cp .env.example .env
npm run dev
```

Backend runs on port 5000. `AI_SERVICE_URL` must be `http://localhost:8002`.

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Workflow

React -> Node/Express -> MongoDB -> FastAPI -> deterministic checks + knowledge retrieval -> OpenAI LLM -> Node -> React -> technician review.

The LLM never performs threshold calculations, equipment control, automatic maintenance approval, or confirmation of findings. Possible causes remain possible until a technician confirms them.

See `RUN.md` for commands.
