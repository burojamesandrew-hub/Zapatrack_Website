# ERROR HANDLING VERIFICATION & API CONNECTION TEST

## Overview

All errors in this system are now **human-readable and comprehensive**. Every error message tells the user what went wrong and how to fix it.

---

## ✅ Error Messages Are Improved

### Frontend Errors

| Scenario               | Old Message              | New Message                                                                                                                                  |
| ---------------------- | ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Empty search           | _(silently ignored)_     | "Please enter a Request ID."                                                                                                                 |
| Backend offline        | "Request failed"         | "Connection error: Unable to reach the server. Please check if the barangay server is running. (Backend should be on http://localhost:8000)" |
| Request not found      | "Request not found."     | "Request not found. Please check your Request ID or try the QR code scanner."                                                                |
| Appointment error      | _(generic error)_        | "Cannot schedule appointment. Current status: 'Pending', required status: 'Ready for Pickup'."                                               |
| Successful appointment | "Appointment confirmed!" | "✓ Appointment confirmed! See you at the barangay hall on **2026-05-20** at **8:00 AM – 9:00 AM**."                                          |

### Backend Errors

| Scenario                  | Old Behavior                        | New Behavior                                                         |
| ------------------------- | ----------------------------------- | -------------------------------------------------------------------- |
| Database connection fails | _(silently returns None)_           | "Server error: Database error: Unable to retrieve data. [Details]"   |
| Query fails               | "Not found"                         | "Server error: Unable to retrieve request details. [Specific error]" |
| Data serialization fails  | _(crashes or returns corrupt data)_ | "Server error: Data serialization error: [Specific error]"           |
| Invalid input             | _(might crash)_                     | "Request ID cannot be empty"                                         |

---

## 🔧 How to Test Each Scenario

### Test 1: Backend Offline

```bash
# 1. Make sure backend is NOT running
# 2. Go to http://localhost:5173
# 3. Try to search for any Request ID
# 4. Expected Error: "Connection error: Unable to reach the server..."
```

**Browser Console Output**:

```
[API] GET http://localhost:8000/api/status/test-id/
[API] Connection failed: Connection error: Unable to reach the server...
```

### Test 2: Backend Online, Request Not Found

```bash
# 1. Start backend: cd backend && python manage.py runserver
# 2. Go to http://localhost:5173
# 3. Try Request ID: "not-a-real-id-12345"
# 4. Expected Error: "Request not found. Please verify the Request ID or QR code and try again."
```

**Browser Console Output**:

```
[API] GET http://localhost:8000/api/requests/not-a-real-id-12345/
[API] Error 404: Request not found. Please verify the Request ID or QR code and try again.
```

### Test 3: Health Check

```bash
curl http://localhost:8000/api/health/
# If working: {"status":"ok","message":"Server and database are operational"}
# If DB down: {"status":"degraded","message":"Database connection issue"}
# If completely down: Connection refused
```

### Test 4: Valid Request (If You Have Test Data)

```bash
# 1. Backend running
# 2. Search for a valid Request ID
# 3. Should show full details with NO errors
# 4. Status tracker should display correctly
# 5. Can schedule appointment if status = "Ready for Pickup"
```

### Test 5: Appointment Scheduling Error

```bash
# 1. Find a request with status NOT "Ready for Pickup"
# 2. Try to schedule appointment
# 3. Expected Error: "Cannot schedule appointment. Current status: 'Pending', required status: 'Ready for Pickup'."
```

### Test 6: Missing Camera/Permissions

```bash
# 1. Click "Scan QR Code"
# 2. Block camera access when browser asks
# 3. Expected Error: "Unable to access camera." or "Camera access not supported"
```

### Test 7: Invalid QR Image Upload

```bash
# 1. Click "Upload QR Image"
# 2. Select a non-QR image (like a photo)
# 3. Expected Error: "No QR code found in uploaded image."
```

### Test 8: Empty Request ID Search

```bash
# 1. Click search without entering ID
# 2. Expected: Button disabled
# 3. Or if submitted: Error "Please enter a Request ID."
```

---

## 📊 Error Logging for Debugging

### Frontend Console (Press F12 → Console)

When something goes wrong, you'll see:

```javascript
[API] GET http://localhost:8000/api/requests/test-id/
[API] Error 404: Request not found. Please verify the Request ID or QR code and try again.
[Fetch Request Error] Request not found. Please verify the Request ID or QR code and try again.
```

### Backend Console

Check the terminal where you ran `python manage.py runserver`:

```
[DB] Database error: connection refused
[API] get_request error: Database error: connection refused
[API] Error serializing rows: unexpected error
```

---

## 🧪 Complete System Test Flow

### Prerequisites

- Backend running: `cd backend && python manage.py runserver`
- Frontend running: `cd frontend && npm run dev`
- Browser at: http://localhost:5173

### Step-by-Step Test

1. **Check Backend Health**

   ```bash
   curl http://localhost:8000/api/health/
   # Should return: {"status":"ok",...}
   ```

2. **Open Browser Console** (F12)
   - Should see: `[API] Using backend URL: http://localhost:8000/api`

3. **Test Invalid Search**
   - Search for "invalid-id"
   - Should see error: "Request not found..."

4. **Test Valid Request** (if data exists)
   - Search for a valid Request ID
   - Should see status details
   - Status tracker should work

5. **Test QR Scanner**
   - Click "Scan QR Code"
   - Should prompt for camera permission

6. **Test Appointment Scheduling**
   - If status = "Ready for Pickup", try to schedule
   - Should work (or show appropriate error)

---

## 📋 Error Checklist

When you encounter an error, use this checklist:

- [ ] **Read the error message carefully** - It tells you exactly what's wrong
- [ ] **Check browser console** (F12 → Console) for detailed logs
- [ ] **Check backend console** for database/API errors
- [ ] **Run health check**: `curl http://localhost:8000/api/health/`
- [ ] **Verify backend is running** on http://localhost:8000
- [ ] **Verify frontend .env** has correct API URL
- [ ] **Check database connection** in backend/.env
- [ ] **Clear browser cache** (Ctrl+Shift+Delete) and refresh

---

## 🎯 Key Improvements Made

### Frontend (frontend/src/)

- ✅ All API calls have try-catch blocks
- ✅ All error messages are user-friendly
- ✅ Console logging shows what's happening
- ✅ Empty inputs show appropriate errors
- ✅ Network errors clearly identified

### Backend (backend/api/)

- ✅ All database operations wrapped in error handlers
- ✅ Descriptive error messages with context
- ✅ Data serialization errors caught
- ✅ HTTP status codes used appropriately
- ✅ All endpoints validate input

### Configuration

- ✅ Frontend .env for API URL configuration
- ✅ Error messages updated throughout
- ✅ Console logging for debugging
- ✅ Health check endpoint for monitoring

---

## 🚀 How to Troubleshoot

### If backend won't start:

```bash
cd backend
python manage.py runserver
# Check for error messages - they'll be clear now
```

### If frontend won't load:

```bash
cd frontend
npm run dev
# Check for build errors
# Check browser console (F12)
```

### If API calls fail:

1. Check health: `curl http://localhost:8000/api/health/`
2. Check .env files
3. Check browser console for error messages
4. Check backend console for logs

### If appointment scheduling fails:

- Error message will say exactly why
- Usually: "Status must be 'Ready for Pickup'"
- Check request status first

---

## ✨ Example Error Flow

**User searches for invalid ID:**

```
User enters "test-123" → Clicks Search
    ↓
Frontend sends: GET /api/requests/test-123/
    ↓
Backend database query returns: NULL
    ↓
Backend returns 404: {"error": "Request not found. Please verify..."}
    ↓
Frontend console logs: [API] Error 404: Request not found...
    ↓
User sees: Red box with "Request not found. Please verify..."
    ↓
User understands what went wrong and what to do
```

All errors are now **clear, helpful, and actionable**! ✅
