# Backup y reemplaza config.yaml
Copy-Item config.yaml config.yaml.backup
@'
system:
  name: "Security Fuzzing System"
  version: "2.0.0"
  debug: false
  log_level: "INFO"
database:
  type: "sqlite"
  path: "data/databases/fuzzing.db"
  backup_enabled: true
web:
  host: "0.0.0.0"
  port: 5000
  secret_key: "change-this-key"
api:
  host: "0.0.0.0"
  port: 8000
  enable_cors: true
network:
  max_workers: 6
  timeout: 15
  verify_ssl: false
'@ | Out-File -FilePath "config.yaml" -Encoding UTF8

# Probar fuzzing engine
python -m core.fuzzing_engine --help