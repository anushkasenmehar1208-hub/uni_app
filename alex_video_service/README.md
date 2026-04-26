# Alex Video Service

Standalone microservice that turns a topic + prompt into a 3Blue1Brown-style
educational video using Manim Community Edition.

Architecture: `LLM (claude-opus-4-7) → Manim Python code → manim CLI → MP4`.
Deployed as a separate Railway service so the Manim+LaTeX toolchain
(~2.5 GB) does not bloat the main Alex AI image.

## Endpoints

| Method | Path                  | Purpose                                    |
| ------ | --------------------- | ------------------------------------------ |
| POST   | `/render`             | Enqueue a job. Returns `{job_id, status}`. |
| GET    | `/status/{job_id}`    | Poll a job. Returns status + `video_url`.  |
| GET    | `/videos/{file}.mp4`  | Static MP4 served by FastAPI.              |
| GET    | `/health`             | Liveness probe.                            |

### POST /render — request body

```json
{
  "topic": "Fourier series",
  "prompt": "Show how sine waves sum into a square wave, then morph back.",
  "style": "cinematic",
  "use_3d": false
}
```

### Status lifecycle

`queued → generating → rendering → done` (or `error`).

When `status == "done"`, `video_url` points at the MP4 (absolute URL when
`PUBLIC_BASE_URL` is set, otherwise relative).

## Deploy on Railway

1. **Create a new Railway service** from this directory (separate from the
   Alex AI service so the Manim toolchain doesn't bloat the main image).
2. Add an env var **`OPENROUTER_API_KEY`** (same key the main app uses).
3. Add **`PUBLIC_BASE_URL`** = the Railway-assigned URL of this service
   (e.g. `https://alex-video-service.up.railway.app`). This gets baked into
   the `video_url` returned to the main app.
4. Optional: `RENDER_QUALITY` (`low` | `medium` | `high`, default `medium`)
   and `MAX_RENDER_SECONDS` (default `180`).
5. **Volume:** mount a Railway volume at `/data` so videos persist across
   restarts. Without a volume, videos disappear on redeploy.
6. Build settings — Railway auto-detects the `Dockerfile`. Build will take
   8–12 minutes the first time (texlive is heavy).

Once live, copy the public URL into the main Alex AI app as
`ALEX_VIDEO_SERVICE_URL` and use it from the chat UI.

## Local dev

```bash
cd /Users/lenujan/Desktop/alex_video_service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Manim's LaTeX backend needs MacTeX or BasicTeX installed system-wide.
cp .env.example .env  # then fill in OPENROUTER_API_KEY
./start.sh
```

Smoke test:

```bash
curl -X POST http://localhost:8090/render \
  -H 'content-type: application/json' \
  -d '{"topic":"Pythagoras","prompt":"Animate a^2+b^2=c^2 with a square proof.","use_3d":false}'

# poll the returned job_id
curl http://localhost:8090/status/<job_id>
```

## Safety

The LLM output is filtered for forbidden patterns (`os.system`, `subprocess`,
`eval`, `exec`, `open`, `__import__`, network libs) before being written to
disk. The Manim CLI then runs as a subprocess with a hard timeout.

For production, also consider:
- Running the renderer container as a non-root user.
- Network egress firewall — the rendering process itself should not need
  outbound network.
- Per-IP rate limiting at the edge (Railway → Cloudflare or similar).

## Wiring into the main app

In `uni_app/uni_app.py`, point at this service:

```python
ALEX_VIDEO_SERVICE_URL = os.environ.get("ALEX_VIDEO_SERVICE_URL", "")

async def request_video(topic: str, prompt: str, use_3d: bool = False) -> str:
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(
            f"{ALEX_VIDEO_SERVICE_URL}/render",
            json={"topic": topic, "prompt": prompt, "use_3d": use_3d},
        )
        r.raise_for_status()
        return r.json()["job_id"]
```

Then poll `/status/{job_id}` from the chat UI until `status == "done"` and
embed the returned `video_url` in the chat as a `<video>` element.
