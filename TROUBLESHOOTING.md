<!-- Error Handling & Troubleshooting Guide -->

## Frontend-Backend API Connection Issues

### Quick Diagnostics

#### 1. **Backend Server Not Running**

**Error Message**: "Connection error: Unable to reach the server. Please check if the barangay server is running."

**Solution**:

```bash
cd backend
python manage.py runserver
```

The backend should run on `http://localhost:8000`

#### 2. **API URL Misconfiguration**

**Error Message**: "Connection error: Unable to reach the server..."

**Solution**:

- Check `frontend/.env` file
- Ensure `VITE_API_URL=http://localhost:8000/api` matches your backend URL
- If backend is on different host/port, update this value

#### 3. **Database Connection Error**

**Error Message**: "Server error: Database error: Unable to retrieve data..."

**Backend Setup**:

```bash
# Make sure database connection is configured in backend/.env:
DATABASE_URL=postgresql://postgres:PASSWORD@localhost:PORT/DATABASE_NAME
DB_HOST=localhost
DB_PORT=10617  # or your actual port
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password
```

#### 4. **Request Not Found**

**Error Message**: "Request not found. Please verify the Request ID or QR code and try again."

**Possible Causes**:

- Request ID doesn't exist in the database
- Wrong Request ID format
- Database doesn't have the test data

#### 5. **Appointment Scheduling Failed**

**Error Message**: "Cannot schedule appointment. Current status: 'Pending', required status: 'Ready for Pickup'."

**Solution**:

- Your request must be in "Ready for Pickup" status before scheduling
- Contact barangay office to update the request status

#### 6. **Invalid Time Slot**

**Error Message**: "Invalid time slot. Available slots: 8:00 AM – 9:00 AM, ..."

**Solution**:

- Select one of the available time slots from the dropdown

### Testing API Endpoints

#### Test Database Connection:

```bash
cd backend
python manage.py shell
>>> from api.db import query
>>> result = query('SELECT 1')
>>> print(result)
```

#### Test API Endpoint (using curl):

```bash
# Test get_status endpoint
curl http://localhost:8000/api/status/your-request-id/

# Test list requests
curl "http://localhost:8000/api/requests/?page=1&page_size=10"

# Test create appointment
curl -X POST http://localhost:8000/api/appointments/ \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "your-request-id",
    "pickup_date": "2026-05-20",
    "pickup_time_slot": "8:00 AM – 9:00 AM"
  }'
```

### Common Error Messages Explained

| Error Message                                    | Meaning                                 | Action                                        |
| ------------------------------------------------ | --------------------------------------- | --------------------------------------------- |
| "Connection error: Unable to reach the server"   | Backend is not running or URL is wrong  | Start backend or fix VITE_API_URL in .env     |
| "Request not found"                              | Request ID doesn't exist in database    | Check Request ID spelling or use QR scanner   |
| "Cannot schedule appointment. Current status: X" | Status doesn't match requirement        | Wait until request reaches "Ready for Pickup" |
| "Server error: Database error..."                | Database connection failed              | Check DATABASE_URL and DB credentials         |
| "An appointment is already scheduled"            | This request already has an appointment | Can only have one appointment per request     |

### Browser Console Debugging

1. Open Developer Tools: **F12** or **Right-click → Inspect**
2. Go to **Console** tab
3. Look for detailed error messages
4. Copy and share full error for troubleshooting

### Logs to Check

#### Backend Logs:

```
[DB] Pool init failed: ...
[DB] Database error: ...
[API] get_request error: ...
[API] create_appointment error: ...
```

#### Frontend Console:

```
Connection error messages
Request/Response details
Network tab in DevTools
```

### Restart Both Services

If errors persist, restart both frontend and backend:

**Terminal 1 - Backend**:

```bash
cd backend
python manage.py runserver
```

**Terminal 2 - Frontend**:

```bash
cd frontend
npm run dev
```

Then clear browser cache: **Ctrl+Shift+Delete** and retry.
