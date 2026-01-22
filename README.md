# Voice-to-CRM PWA

A **voice-first Progressive Web App** that converts speech into structured CRM data using free tools.

---

## Tech Stack
- **Frontend:** React 18 (PWA)  
- **Backend:** FastAPI (Python 3.10+)  
- **Speech-to-Text:** Whisper AI  
- **Data Extraction:** Regex & simple NLP  

---

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



![Screenshot 1](https://raw.githubusercontent.com/user-attachments/assets/16262ff3-d6ef-43e7-a2ce-452a63f5da62)
![Screenshot 2](https://raw.githubusercontent.com/user-attachments/assets/0737ddcf-4c4d-4992-8263-d999152aabf6)
![Screenshot 3](https://raw.githubusercontent.com/user-attachments/assets/19d5d4ac-e329-425d-a0ce-c43e909cf977)

