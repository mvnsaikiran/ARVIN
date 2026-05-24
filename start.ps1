# Arvind HR Pulse — Launch both servers
# Right-click → "Run with PowerShell"

Write-Host "=== Starting Arvind HR Pulse ===" -ForegroundColor Cyan

# Start Python backend in a new window
Write-Host "Starting Python RAG backend on port 8001..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python backend.py"

Start-Sleep -Seconds 3

# Start Node.js server in a new window
Write-Host "Starting frontend server on port 3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npx tsx --env-file=.env server.ts"

Start-Sleep -Seconds 4

Write-Host "`nChatbot is running!" -ForegroundColor Green
Write-Host "Open your browser and go to: http://localhost:3000" -ForegroundColor Cyan

Start-Process "http://localhost:3000"
