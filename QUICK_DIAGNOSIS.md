# Quick Diagnosis Checklist

## Is the backend running?

### Step 1: Check if Django server is running

```bash
# In a terminal, try to reach the health endpoint:
curl http://localhost:8000/api/health/
```

**Expected Response**:

```json
{ "status": "ok", "message": "Server and database are operational" }
```

**If you get Connection Refused**:

```bash
# Terminal 1: Start the backend
cd backend
python manage.py runserver
# You should see: "Starting development server at http://127.0.0.1:8000/"
```

---

## Is the frontend connecting to the backend?

### Step 2: Check frontend configuration

```bash
# Make sure .env file exists in frontend folder with:
cat frontend/.env
# Should show: VITE_API_URL=http://localhost:8000/api
```

**If .env doesn't exist**:

```bash
# Create it:
echo "VITE_API_URL=http://localhost:8000/api" > frontend/.env
```

---

## Is the database connected?

### Step 3: Check database connection from backend

```bash
cd backend

# Quick Python check:
python -c "from api.db import query; print(query('SELECT 1'))"

# Should print: (1,) or similar result

# If error, check .env DATABASE_URL:
cat .env
# Make sure DATABASE_URL matches your actual database connection
```

**If database error**:

1. Check DATABASE_URL in `backend/.env`
2. Make sure PostgreSQL server is running
3. Make sure credentials are correct: username, password, host, port

---

## Frontend to Backend Communication

### Step 4: Test from browser console

```javascript
// Open browser Developer Tools: F12
// Go to Console tab and paste:

fetch("http://localhost:8000/api/health/")
  .then((r) => r.json())
  .then((d) => console.log("✓ Connected!", d))
  .catch((e) => console.error("✗ Failed:", e.message));
```

**Expected Output**:

```
✓ Connected! {status: 'ok', message: 'Server and database are operational'}
```

**If Failed**:

- Backend URL in .env is wrong
- Backend is not running
- CORS issue (check Django CORS settings)

---

## Common Issues & Fixes

| Symptom                                          | Cause                  | Fix                                               |
| ------------------------------------------------ | ---------------------- | ------------------------------------------------- |
| "Connection error: Unable to reach server"       | Backend not running    | `cd backend && python manage.py runserver`        |
| Page loads but "Request not found" on any search | Database not connected | Check `DATABASE_URL` in `backend/.env`            |
| Console shows "TypeError: fetch failed"          | Backend URL wrong      | Check `VITE_API_URL` in `frontend/.env`           |
| Backend shows error about database               | Wrong credentials      | Update `backend/.env` with correct DB credentials |
| 404 errors on API endpoints                      | Routes not defined     | Check `backend/api/urls.py` has all endpoints     |

---

## Full System Startup (Clean)

```bash
# Terminal 1: Start Backend
cd backend
python manage.py runserver
# Wait for: "Starting development server at http://127.0.0.1:8000/"

# Terminal 2: Start Frontend
cd frontend
npm run dev
# Wait for: "➜  Local:   http://localhost:5173/"

# Terminal 3: Test
curl http://localhost:8000/api/health/
# Should return: {"status":"ok",...}

# Open browser: http://localhost:5173
# Try searching for a request
```

---

## When Everything Works

✅ Backend console shows no errors
✅ Frontend loads at http://localhost:5173
✅ `curl http://localhost:8000/api/health/` returns OK
✅ Browser console shows `[API] Using backend URL: http://localhost:8000/api`
✅ Can search and see results
✅ Error messages are clear and helpful

---

## Still Having Issues?

1. **Clear all caches**:
   - Browser: Ctrl+Shift+Delete (clear cache)
   - Frontend rebuild: `npm run dev`
   - Stop and restart both servers

2. **Check logs**:
   - Backend console: Look for [DB] or [API] prefix
   - Frontend console: F12 → Console tab

3. **Verify installation**:

   ```bash
   # Backend
   cd backend
   pip list | grep -i django
   pip list | grep -i rest_framework

   # Frontend
   cd frontend
   npm list jsqr
   ```

4. **Test database directly**:

   ```bash
   cd backend
   python manage.py shell
   >>> from api.db import query
   >>> print(query('SELECT 1'))
   # Should print a result
   ```

5. **Check network tab**:
   - Open F12 → Network tab
   - Try a search
   - Look at network requests
   - Check if requests go to correct URL
   - Check response status codes (404, 500, etc.)
