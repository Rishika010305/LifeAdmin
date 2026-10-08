# LifeAdmin — Complete Version

A full-stack Personal Digital Life Management & Intelligence Platform.

## Included
- Dashboard
- Documents CRUD
- Bills & Payments CRUD
- Subscriptions CRUD
- Mobile & Recharge CRUD
- Warranties CRUD
- Appointments & Important Dates CRUD
- Life Timeline
- Analytics
- Global search
- Rule-based Life Assistant
- Calendar `.ics` export
- Browser notification permission
- Flask REST API
- MySQL persistence
- Automatic database/table creation
- Responsive UI

## Run

### 1. Database
Make sure MySQL Server is running.

Create `backend/.env` from `.env.example` and put your existing MySQL password there.

### 2. Backend
Open a terminal:
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The API runs at:
`http://127.0.0.1:5000`

### 3. Frontend
Open the project folder in VS Code and use Live Server on `index.html`.

The frontend expects:
`http://127.0.0.1:5000/api`

## Important
Do not put your MySQL password into GitHub. Keep `backend/.env` in `.gitignore`.

## Suggested Git commits
1. Initial LifeAdmin UI
2. Add CRUD modules
3. Add Flask REST API
4. Add MySQL persistence
5. Add timeline and analytics
6. Add Life Assistant and calendar export
7. Final responsive polish
