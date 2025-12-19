# 🎙️ Podcast Rescue

**Your AI Audio Engineer. Instantly restore clarity and master dynamic range.**

## 🚀 Key Features (核心功能)

1.  **AI Voice Restoration:**
    * Powered by Replicate (`resemble-enhance` / `voice-fixer`).
    * Removes background hiss, echo, and electrical noise.

2.  **Smart Dynamic Leveling:**
    * Uses **Adaptive Dynamic Range Compression** (via FFmpeg `dynaudnorm`).
    * Automatically normalizes loudness to **-16 LUFS** (Industry Standard).

3.  **Content Insight:**
    * Integration with **SiliconFlow (DeepSeek-V3)** for shownotes generation.

## 🛠️ Tech Stack
* **Frontend:** Streamlit
* **AI Models:** SiliconFlow, Replicate
* **Audio Processing:** FFmpeg
