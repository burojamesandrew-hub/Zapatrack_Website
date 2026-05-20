# Barangay Zapatera CertTrack — Web Portal

## Setup

### Backend (Django)

```bash
cd backend
pip install -r requirements.txt
# Edit .env and set DATABASE_URL=postgresql://...
python manage.py runserver
```

### Frontend (React + Vite)

```bash
cd frontend
npm install
# Edit .env and set VITE_API_URL=http://localhost:8000/api (default is already set)
npm run dev
```

Open http://localhost:5173

## Pages

- `/` Home — UUID search + QR scanner + how it works
- `/track` Track a request with QR scanner or manual ID entry
- `/track/:id` View status of a specific request
- `*` 404 page

## API Endpoints (Django, port 8000)

- GET /api/health/ Health check endpoint
- GET /api/status/<id>/ Get request status
- GET /api/requests/ List all requests (with pagination & filters)
- GET /api/requests/<id>/ Get full request details
- GET /api/summary/ Get status summary
- GET /api/appointments/<id>/ Get appointment details
- POST /api/appointments/ Schedule a new appointment
- GET /api/timeslots/ Get available timeslots

## Error Handling

All API errors now return human-readable messages:

### Common Errors & Solutions

| Error                                    | Cause                         | Solution                                           |
| ---------------------------------------- | ----------------------------- | -------------------------------------------------- |
| Connection error: Unable to reach server | Backend not running           | Run `python manage.py runserver` in backend folder |
| Request not found                        | Invalid Request ID            | Check Request ID or use QR scanner                 |
| Cannot schedule appointment              | Request not in correct status | Status must be "Ready for Pickup"                  |
| Database error                           | Connection failed             | Check DATABASE_URL in .env                         |

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for detailed debugging guide.

## Configuration

### Frontend (.env)

```
VITE_API_URL=http://localhost:8000/api
```

### Backend (.env)

```
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=10617
DATABASE_URL=postgresql://postgres:password@localhost:10617/postgres
```

## Testing Connection

### Check if backend is running:

```bash
curl http://localhost:8000/api/health/
```

Expected response:

```json
{ "status": "ok", "message": "Server and database are operational" }
```

### Check a request:

```bash
curl http://localhost:8000/api/requests/your-request-id/
```
