Write-Host "🛑 Deteniendo Security Fuzzing System..." -ForegroundColor Red
Write-Host "=" * 50

# Buscar y detener procesos de Python relacionados
$python_processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*web\app.py*" -or 
    $_.CommandLine -like "*api\app.py*" -or
    $_.CommandLine -like "*fuzzing_engine*"
}

if ($python_processes) {
    Write-Host "Deteniendo procesos de Python..." -ForegroundColor Yellow
    $python_processes | Stop-Process -Force
    Write-Host "✅ Procesos detenidos" -ForegroundColor Green
} else {
    Write-Host "No se encontraron procesos de Python ejecutándose" -ForegroundColor Gray
}

Write-Host "🔚 Sistema detenido" -ForegroundColor Green