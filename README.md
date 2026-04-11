# Alex Studies 🚀
**A Full-Stack Academic Platform for University Students.**

Built with **Python** and the **Reflex** framework, Alex Studies is designed to centralize complex academic modules like Pure Mathematics, Statistics, and Physics into one high-performance dashboard.

## ✨ Key Features
* **Custom Dashboard:** Tailored for University of Kelaniya curriculum.
* **Integrated Tools:** Specialized calculators for advanced mathematics.
* **Fast Deployment:** Hosted on Railway for 99.9% uptime.
* **Seamless UI:** Minimalist dark-mode design for focused studying.

## 🛠 Tech Stack
* **Frontend/Backend:** [Reflex](https://reflex.dev/) (Python-based full stack)
* **Hosting:** Railway
* **Domain Management:** Cloudflare

## Voice Setup
For the cheapest natural-sounding Alex voice stack, keep `OPENROUTER_API_KEY` for chat and add OpenAI only for speech.

Recommended server env:

```bash
OPENROUTER_API_KEY=your_openrouter_key
OPENAI_API_KEY=your_openai_key
OPENAI_STT_MODEL=gpt-4o-mini-transcribe
OPENAI_TTS_MODEL=gpt-4o-mini-tts
OPENAI_TTS_VOICE=alloy
ALEX_VOICE_BROWSER_ONLY=0
```

Notes:
- `OPENROUTER_API_KEY` still powers Alex's teaching/chat model.
- `OPENAI_API_KEY` is used only for voice transcription and voice output.
- `ALEX_VOICE_BROWSER_ONLY=0` is important. Browser TTS sounds flatter and more like reading.

---
*Created by [Lenujan Paramanantham](https://alexstudies.com)*
