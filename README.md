# Focus Attention Tracker

A webcam-based attention/focus tracker. Uses a pretrained MediaPipe FaceMesh
model for head-pose estimation and eye-closure detection to compute a live
attention score, with full user auth and session history.

## Stack

- **Backend:** FastAPI, SQLAlchemy, SQLite, JWT auth, MediaPipe + OpenCV
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, React Router, Recharts

## Running locally

### Backend

```bash
cd backend
python -m venv venv
./venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```
