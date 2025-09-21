# PRSummarizer.ai

Always-on multi-agent PR copilot built for the Coral Protocol hackathon. The project keeps a Coral session alive so an orchestrator agent can instantly rally summarizer, risk, and voice specialists, stream their insights to a React dashboard, and even narrate the results with ElevenLabs.

## Why It Matters
- **Slash review fatigue**: Condense long pull requests into actionable summaries and risk calls in seconds.
- **Coral-native**: Agents register and collaborate through Coral Server, ensuring they are always reachable and composable.
- **Voice-ready**: Optional ElevenLabs narration makes PR findings accessible and demo-friendly.
- **Extensible**: Add new agents (tests, compliance, analytics) without touching the core UI.

## System Snapshot
- **Frontend**: React + TypeScript web client with SSE-driven action timeline and analysis panels (`webapp/web`).
- **Backend**: Python FastAPI service that spawns Coral sessions, relays agent updates, and exposes the `/prompt` SSE endpoint (`backend_server.py`).
- **Orchestration**: Coral Server (Kotlin/Ktor) hosting the agent graph (`coral-server`).
- **Agents**: Python workers powered by AIML GPT models plus ElevenLabs TTS (`agents/`).
- **Shared Toolkit**: GitHub fetcher, input parser, and voice utilities (`shared/`).

## Quick Start
1. **Install deps**
   ```bash
   # Backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements_backend.txt

   # Frontend
   cd webapp/web
   npm install
   ```
2. **Set environment** – create a `.env` file in the repo root with the keys described in `README_BACKEND.md` (AIML/NEBIUS API keys, GitHub token, ElevenLabs credentials).
3. **Run Coral Server**
   ```bash
   cd coral-server
   ./gradlew run
   ```
4. **Start backend**
   ```bash
   python backend_server.py
   ```
5. **Launch web UI**
   ```bash
   cd webapp/web
   npm start
   ```
6. Visit `http://localhost:3000`, paste a GitHub PR URL, and watch the agent timeline stream updates in real time.

## Demo Tips
- Use the Action Timeline screenshot (`webapp/web`) alongside Coral Studio view to show the same session in both interfaces.
- Trigger the voice-over option to play the ElevenLabs narration for judges.
- Highlight the monetization roadmap (team tiers, Coral marketplace agents, Solana/Jupiter payouts).

## Pitch Assets
- Slide plan: `presentation_plan.md`
- Pitch deck (editable): `PRSummarizer_ai_pitch.pptx`
- Architecture deep dive: `COMPREHENSIVE_ARCHITECTURE_ANALYSIS.md`

Built by the PRSummarizer.ai team for the Coral Protocol hackathon—download, run, and join our Coral agent squad!
