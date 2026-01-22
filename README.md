# Voice-to-CRM PWA

A **voice-first Progressive Web App** that converts speech into structured CRM data using free tools.

---

## Tech Stack
- **Frontend:** React 18 (PWA)  
- **Backend:** FastAPI (Python 3.10+)  
- **Speech-to-Text:** Whisper AI  
- **Data Extraction:** Regex & simple NLP  

---


![web application screenshots](https://github.com/user-attachments/assets/5508d4ee-896d-48e9-94c4-6ef4a1716665)





## Setup

### Prerequisites
- Node.js v18+  
- Python 3.10+  
- FFmpeg (in PATH)  
- Git  

### Backend
```bash
cd backend
python -m venv venv
# Activate venv
pip install -r requirements.txt
python main.py  # runs on http://localhost:8000

cd frontend
npm install
npm start  # opens http://localhost:3000



 


