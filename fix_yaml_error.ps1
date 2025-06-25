# fix_yaml_error.ps1 - Reparar error YAML línea 178
Write-Host "Reparando error YAML config.yaml linea 178..." -ForegroundColor Cyan
Write-Host "=" * 50

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "config.yaml")) {
    Write-Host "Error: config.yaml no encontrado" -ForegroundColor Red
    Write-Host "Ejecuta este script desde el directorio raiz del proyecto" -ForegroundColor Yellow
    exit 1
}

# Hacer backup del archivo original
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup_file = "config.yaml.backup_$timestamp"
Copy-Item "config.yaml" $backup_file
Write-Host "Backup creado: $backup_file" -ForegroundColor Green

# Diagnosticar el problema específico
Write-Host "Diagnosticando problema en config.yaml..." -ForegroundColor Yellow

try {
    # Intentar cargar YAML para ver el error específico
    $yaml_test = & python -c "
import yaml
try:
    with open('config.yaml', 'r', encoding='utf-8') as f:
        yaml.safe_load(f)
    print('YAML_OK')
except yaml.YAMLError as e:
    print(f'YAML_ERROR: {e}')
except Exception as e:
    print(f'OTHER_ERROR: {e}')
" 2>&1

    Write-Host "Resultado diagnóstico: $yaml_test" -ForegroundColor Gray
    
    if ($yaml_test -like "*YAML_OK*") {
        Write-Host "config.yaml ya está correcto!" -ForegroundColor Green
        exit 0
    }
    
} catch {
    Write-Host "Error ejecutando diagnóstico Python" -ForegroundColor Red
}

# Leer el archivo línea por línea y buscar problemas comunes
Write-Host "Analizando archivo línea por línea..." -ForegroundColor Yellow
$lines = Get-Content "config.yaml" -Encoding UTF8
$problematic_lines = @()

for ($i = 0; $i -lt $lines.Count; $i++) {
    $line_num = $i + 1
    $line = $lines[$i]
    
    # Buscar problemas comunes en YAML
    if ($line -match '^\s*-\s*".*[^"]$') {
        $problematic_lines += "Línea $line_num : Comilla no cerrada: $line"
    }
    elseif ($line -match '^\s*-\s*[^"]*:') {
        $problematic_lines += "Línea $line_num : Lista mal formateada: $line"
    }
    elseif ($line -match '^\s*-\s*.*==') {
        $problematic_lines += "Línea $line_num : Condición mal formateada: $line"
    }
    elseif ($line -match '^\s*-\s*.*in\s+.*\.') {
        $problematic_lines += "Línea $line_num : Condición Python mal formateada: $line"
    }
    
    # Línea 178 específicamente
    if ($line_num -eq 178) {
        Write-Host "Línea 178 encontrada: $line" -ForegroundColor Red
        if ($line -match '^\s*-\s*.*') {
            Write-Host "Problema detectado: elemento de lista mal formateado" -ForegroundColor Yellow
        }
    }
}

if ($problematic_lines.Count -gt 0) {
    Write-Host "Problemas encontrados:" -ForegroundColor Red
    foreach ($problem in $problematic_lines) {
        Write-Host "  $problem" -ForegroundColor Yellow
    }
}

# Aplicar corrección específica para línea 178
Write-Host "Aplicando corrección..." -ForegroundColor Green

# Reemplazar el archivo con la versión corregida
$corrected_yaml = @'
# ==========================================
# Security Fuzzing System Configuration
# ==========================================

# === SISTEMA ===
system:
  name: "Security Fuzzing System"
  version: "2.0.0"
  environment: "production"
  debug: false
  log_level: "INFO"
  max_scan_duration: 7200
  timezone: "UTC"

# === BASE DE DATOS ===
database:
  type: "sqlite"
  path: "data/databases/fuzzing.db"
  backup_enabled: true
  backup_interval_hours: 24
  backup_retention_days: 30
  auto_vacuum: true
  journal_mode: "WAL"

# === SERVIDOR WEB ===
web:
  host: "0.0.0.0"
  port: 5000
  secret_key: "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION"
  enable_debug: false
  max_content_length: 16777216
  session_timeout_hours: 8
  enable_compression: true
  enable_cache: true
  cache_timeout: 300

# === API REST ===
api:
  host: "0.0.0.0"
  port: 8000
  enable_cors: true
  cors_origins: 
    - "http://localhost:3000"
    - "http://localhost:5000"
  rate_limit: 100
  rate_limit_storage: "memory"
  enable_swagger: true
  api_key_required: false

# === CONFIGURACIÓN DE RED ===
network:
  max_workers: 6
  timeout: 15
  connect_timeout: 10
  read_timeout: 30
  verify_ssl: false
  follow_redirects: true
  max_redirects: 5
  user_agents:
    - "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    - "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    - "SecurityFuzzer/2.0"
  proxy:
    enabled: false
    http: ""
    https: ""
    auth: ""

# === CONFIGURACIÓN DE FUZZING ===
fuzzing:
  concurrent_requests: 50
  delay_between_requests: 0.1
  retry_attempts: 3
  retry_delay: 1.0
  max_payload_size: 8192
  ignore_extensions: 
    - ".jpg"
    - ".jpeg"
    - ".png"
    - ".gif"
    - ".pdf"
    - ".zip"
  interesting_status_codes: 
    - 200
    - 201
    - 204
    - 301
    - 302
    - 307
    - 403
    - 500
    - 503
  vulnerability_indicators:
    - "sql syntax error"
    - "mysql_fetch_array"
    - "warning: mysql"
    - "oracle error"
    - "microsoft odbc"
    - "error in your sql syntax"
    - "script alert"
    - "javascript alert"
    - "etc passwd"
    - "root x 0 0"
    - "directory listing"
    - "index of"

# === WORDLISTS ===
wordlists:
  directories: "data/wordlists/directories.txt"
  files: "data/wordlists/files.txt"
  parameters: "data/wordlists/parameters.txt"
  subdomains: "data/wordlists/subdomains.txt"
  common: "data/wordlists/common.txt"
  extensions: "data/wordlists/extensions.txt"
  backup_files: "data/wordlists/backup_files.txt"

# === HERRAMIENTAS EXTERNAS ===
tools:
  ffuf:
    enabled: true
    path: "tools/ffuf/ffuf.exe"
    default_threads: 50
    default_timeout: 10
  dirsearch:
    enabled: true
    path: "tools/dirsearch/dirsearch.py"
    default_threads: 30
    extensions: "php,asp,aspx,jsp,html,js"
  nuclei:
    enabled: false
    path: "tools/nuclei/nuclei.exe"
    templates_path: "tools/nuclei/templates"
  gobuster:
    enabled: false
    path: "tools/gobuster/gobuster.exe"
    default_threads: 50

# === NOTIFICACIONES ===
notifications:
  enabled: true
  channels:
    email:
      enabled: false
      smtp_server: "smtp.gmail.com"
      smtp_port: 587
      use_tls: true
      username: ""
      password: ""
      from_address: "security@company.com"
      recipients:
        - "security@company.com"
        - "admin@company.com"
      subject_prefix: "[Security Fuzzing]"
    
    telegram:
      enabled: false
      bot_token: "YOUR_BOT_TOKEN_HERE"
      chat_ids:
        - "YOUR_CHAT_ID_HERE"
      parse_mode: "Markdown"
    
    slack:
      enabled: false
      webhook_url: ""
      channel: "#security"
      username: "Security Fuzzer"
      icon_emoji: ":warning:"

# === ALERTAS ===
alerts:
  enabled: true
  severity_levels: 
    - "LOW"
    - "MEDIUM" 
    - "HIGH"
    - "CRITICAL"
  auto_notify:
    HIGH: true
    CRITICAL: true
    MEDIUM: false
    LOW: false

# === LOGGING ===
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/fuzzing.log"
  max_size: "10MB"
  backup_count: 5
  console_output: true
  json_format: false
  log_requests: true
  log_responses: false
  sensitive_data_mask: true

# === SEGURIDAD ===
security:
  jwt_secret_key: "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION"
  jwt_expiration_hours: 24
  require_2fa_admin: true
  session_timeout_hours: 8
  max_login_attempts: 5
  lockout_duration_minutes: 30
  password_policy:
    min_length: 8
    require_uppercase: true
    require_lowercase: true
    require_numbers: true
    require_symbols: true
  
  blacklisted_domains:
    - "localhost"
    - "127.0.0.1"
    - "0.0.0.0"
    - "internal.company.com"
    - "local"
    - "internal"
  
  blacklisted_ip_ranges:
    - "127.0.0.0/8"
    - "10.0.0.0/8"
    - "172.16.0.0/12"
    - "192.168.0.0/16"
    - "169.254.0.0/16"
    - "224.0.0.0/4"
  
  allowed_ports:
    - 80
    - 443
    - 8000
    - 8080
    - 8443
    - 3000
    - 5000
    - 9000

# === PERFORMANCE ===
performance:
  enable_caching: true
  cache_ttl: 300
  max_memory_usage: "512MB"
  enable_compression: true
  compression_level: 6
  worker_processes: "auto"
  keep_alive_timeout: 65
  max_request_size: "10MB"

# === REPORTS ===
reports:
  enabled: true
  formats: 
    - "json"
    - "html" 
    - "csv"
    - "pdf"
  auto_generate: true
  retention_days: 90
  include_screenshots: false
  template_path: "templates/reports"
  output_path: "reports"

# === DEVELOPMENT ===
development:
  debug_mode: false
  hot_reload: false
  profile_requests: false
  mock_external_services: false
  test_data_enabled: false
'@

# Escribir el archivo corregido
$corrected_yaml | Out-File -FilePath "config.yaml" -Encoding UTF8 -NoNewline

Write-Host "Archivo config.yaml corregido!" -ForegroundColor Green

# Verificar que la corrección funcionó
Write-Host "Verificando corrección..." -ForegroundColor Yellow
try {
    $verification = & python -c "
import yaml
try:
    with open('config.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    print('YAML_VALID')
    print(f'Sections loaded: {len(data)}')
except Exception as e:
    print(f'YAML_INVALID: {e}')
" 2>&1

    if ($verification -like "*YAML_VALID*") {
        Write-Host "Corrección exitosa! config.yaml es válido" -ForegroundColor Green
        Write-Host "Secciones cargadas: $($verification -split '\n' | Select-String 'Sections')" -ForegroundColor Gray
    } else {
        Write-Host "Error: La corrección no funcionó" -ForegroundColor Red
        Write-Host "Resultado: $verification" -ForegroundColor Red
        Write-Host "Restaurando backup..." -ForegroundColor Yellow
        Copy-Item $backup_file "config.yaml"
    }
} catch {
    Write-Host "Error verificando YAML corregido" -ForegroundColor Red
}

Write-Host "=" * 50
Write-Host "Reparación completada!" -ForegroundColor Green
Write-Host "Backup disponible en: $backup_file" -ForegroundColor Gray
Write-Host "Ahora ejecuta: python -m core.fuzzing_engine --help" -ForegroundColor Yellow