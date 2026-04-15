# Aptitude Test - Troubleshooting Guide

## "Failed to fetch" Error - Quick Fix

This error occurs when the frontend cannot connect to the backend server.

### Step 1: Ensure Backend is Running

```cmd
python main.py
```

You should see: `Running on http://127.0.0.1:5001`

### Step 2: Check Browser Console

Press `F12` → Console tab → Look for errors:

| Error | Meaning | Fix |
|-------|---------|-----|
| `Failed to fetch` | Backend not running | Run `python main.py` |
| `CORS policy` | Opened via file:// | Double-click HTML file normally |
| `400 Bad Request` | Invalid data | Refresh and retry |
| `500 Internal Error` | Backend crash | Check terminal output |

## Common Issues

### Backend won't start
```cmd
netstat -ano | findstr :5001
taskkill /PID <PID> /F
```

### MongoDB connection error
The backend works without MongoDB (demo mode). Results stored in-memory.

### Questions not loading
Ensure `question_bank.json` exists in `phase2_test_portal\aptitude_backend\`

## Still Having Issues?

1. Run: `python main.py`
2. Wait for all services to start
3. Open the aptitude test HTML file
4. Check terminal for detailed error logs
