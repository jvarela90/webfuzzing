# 🔍 Dashboard-Diagnostic.ps1
# Herramienta de diagnóstico para el dashboard

Write-Host "🔍 DIAGNÓSTICO DEL DASHBOARD" -ForegroundColor Cyan
Write-Host "=" * 50

# Verificar archivos necesarios
Write-Host "📁 Verificando archivos del dashboard..." -ForegroundColor Yellow
$dashboard_files = @(
    "web\app.py",
    "web\__init__.py",
    "web\templates",
    "web\static"
)

foreach ($file in $dashboard_files) {
    if (Test-Path $file) {
        Write-Host "✅ $file existe" -ForegroundColor Green
    } else {
        Write-Host "❌ $file NO EXISTE" -ForegroundColor Red
    }
}

# Verificar dependencias específicas del dashboard
Write-Host "`n🔍 Verificando dependencias del dashboard..." -ForegroundColor Yellow
$dependencies = @("flask", "flask_cors", "flask_socketio", "jinja2", "werkzeug")

foreach ($dep in $dependencies) {
    try {
        $result = & .\venv\Scripts\python.exe -c "import $dep; print('✅ $dep OK')" 2>&1
        if ($result -like "*OK*") {
            Write-Host "✅ $dep instalado" -ForegroundColor Green
        } else {
            Write-Host "❌ $dep ERROR: $result" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ $dep NO INSTALADO" -ForegroundColor Red
    }
}

# Probar importar el dashboard directamente
Write-Host "`n🧪 Probando importar dashboard..." -ForegroundColor Yellow
try {
    $import_test = & .\venv\Scripts\python.exe -c @"
import sys
sys.path.append('.')
try:
    import web.app
    print('✅ Dashboard importa correctamente')
except ImportError as e:
    print(f'❌ Error importando dashboard: {e}')
except Exception as e:
    print(f'❌ Error general: {e}')
"@ 2>&1
    Write-Host $import_test
} catch {
    Write-Host "❌ Error ejecutando test de importación" -ForegroundColor Red
}

# Verificar puerto 5000
Write-Host "`n🔍 Verificando puerto 5000..." -ForegroundColor Yellow
try {
    $port_test = Test-NetConnection -ComputerName localhost -Port 5000 -InformationLevel Quiet
    if ($port_test) {
        Write-Host "⚠️ Puerto 5000 está ocupado" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Puerto 5000 disponible" -ForegroundColor Green
    }
} catch {
    Write-Host "ℹ️ No se pudo verificar puerto (comando Test-NetConnection no disponible)" -ForegroundColor Gray
}

# Verificar procesos Python
Write-Host "`n🔍 Verificando procesos Python..." -ForegroundColor Yellow
$python_processes = Get-Process -Name python -ErrorAction SilentlyContinue
if ($python_processes) {
    Write-Host "🐍 Procesos Python encontrados:" -ForegroundColor Yellow
    foreach ($proc in $python_processes) {
        Write-Host "   PID: $($proc.Id) - Memoria: $([math]::Round($proc.WorkingSet64/1MB, 2))MB" -ForegroundColor Gray
    }
} else {
    Write-Host "❌ No hay procesos Python ejecutándose" -ForegroundColor Red
}

# Probar ejecutar dashboard directamente
Write-Host "`n🚀 Probando ejecutar dashboard directamente..." -ForegroundColor Yellow
Write-Host "Intentando: python web\app.py" -ForegroundColor Gray

$dashboard_test = Start-Process -FilePath ".\venv\Scripts\python.exe" -ArgumentList "web\app.py" -PassThru -WindowStyle Hidden
Start-Sleep 5

if ($dashboard_test -and -not $dashboard_test.HasExited) {
    Write-Host "✅ Dashboard se inició correctamente (PID: $($dashboard_test.Id))" -ForegroundColor Green
    
    # Probar conexión HTTP
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 5 -UseBasicParsing
        Write-Host "✅ Dashboard responde HTTP $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Dashboard no responde: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Detener proceso de prueba
    Stop-Process -Id $dashboard_test.Id -Force
    Write-Host "🛑 Proceso de prueba detenido" -ForegroundColor Yellow
} else {
    Write-Host "❌ Dashboard no se pudo iniciar" -ForegroundColor Red
}

# Verificar logs si existen
Write-Host "`n📋 Verificando logs..." -ForegroundColor Yellow
if (Test-Path "logs") {
    $log_files = Get-ChildItem -Path "logs" -Filter "*.log" | Sort-Object LastWriteTime -Descending
    if ($log_files) {
        Write-Host "📄 Logs encontrados:" -ForegroundColor Green
        foreach ($log in $log_files) {
            Write-Host "   $($log.Name) - $($log.LastWriteTime)" -ForegroundColor Gray
        }
    } else {
        Write-Host "ℹ️ No hay archivos de log" -ForegroundColor Gray
    }
} else {
    Write-Host "ℹ️ Directorio logs no existe" -ForegroundColor Gray
}

# Probar comando alternativo
Write-Host "`n🔄 Probando comando alternativo..." -ForegroundColor Yellow
Write-Host "Intentando: python -m web.app" -ForegroundColor Gray

try {
    $alt_test = & .\venv\Scripts\python.exe -m web.app --help 2>&1
    if ($alt_test -like "*usage:*" -or $alt_test -like "*help*") {
        Write-Host "✅ Comando 'python -m web.app' disponible" -ForegroundColor Green
    } else {
        Write-Host "❌ Comando 'python -m web.app' no funciona: $alt_test" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error probando comando alternativo" -ForegroundColor Red
}

# Resumen y recomendaciones
Write-Host "`n" + "=" * 50
Write-Host "📊 RESUMEN DEL DIAGNÓSTICO" -ForegroundColor Cyan
Write-Host "=" * 50

Write-Host "`n🎯 RECOMENDACIONES:" -ForegroundColor Yellow
Write-Host "1. Verificar que web\app.py existe y tiene el código correcto" -ForegroundColor White
Write-Host "2. Instalar dependencias faltantes si las hay" -ForegroundColor White
Write-Host "3. Verificar que no hay errores en el código del dashboard" -ForegroundColor White
Write-Host "4. Probar ejecutar manualmente: python web\app.py" -ForegroundColor White
Write-Host "5. Revisar logs para errores específicos" -ForegroundColor White

Write-Host "`n🔧 COMANDOS PARA PROBAR:" -ForegroundColor Yellow
Write-Host "# Activar entorno virtual" -ForegroundColor Gray
Write-Host ".\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "" 
Write-Host "# Probar dashboard manualmente" -ForegroundColor Gray
Write-Host "python web\app.py" -ForegroundColor Gray
Write-Host ""
Write-Host "# Ver errores específicos" -ForegroundColor Gray
Write-Host "python -c `"import web.app`"" -ForegroundColor Gray

Write-Host "`n🆘 SI EL PROBLEMA PERSISTE:" -ForegroundColor Red
Write-Host "Ejecuta: python -c `"import web.app`" y comparte el error exacto" -ForegroundColor White