# Arvind HR Pulse — One-click setup for Windows
# Right-click this file → "Run with PowerShell"

Write-Host "=== Arvind HR Pulse Setup ===" -ForegroundColor Cyan

# Create .env
Write-Host "`nCreating .env..." -ForegroundColor Yellow
@"
GEMINI_API_KEY=AIzaSyCWwae8gLtlplLwuNMaUXFEZi0y7VyCmn8
VITE_GEMINI_API_KEY=AIzaSyCWwae8gLtlplLwuNMaUXFEZi0y7VyCmn8
"@ | Out-File -FilePath ".env" -Encoding utf8
Write-Host ".env created." -ForegroundColor Green

# Install Python packages
Write-Host "`nInstalling Python packages..." -ForegroundColor Yellow
pip install fastapi uvicorn chromadb pdfplumber python-docx langchain-text-splitters python-dotenv google-generativeai
Write-Host "Python packages installed." -ForegroundColor Green

# Install Node packages
Write-Host "`nInstalling Node packages..." -ForegroundColor Yellow
npm install
Write-Host "Node packages installed." -ForegroundColor Green

# Run ingestion
Write-Host "`nBuilding ChromaDB knowledge base from policies..." -ForegroundColor Yellow
python ingest.py
Write-Host "Knowledge base ready." -ForegroundColor Green

Write-Host "`n=== Setup complete! ===" -ForegroundColor Cyan
Write-Host "Now run start.ps1 to launch the chatbot." -ForegroundColor White
pause
