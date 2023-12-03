$Env:MANUAL_EXPOSE_PORT = 8000
$Env:MANUAL_SERVICE_NAME = "manual"
$Env:MANUAL_SERVICE_INSTANCE_ID = "manual-instance-1"
$Env:MANUAL_OTLP_ENDPOINT = "http://localhost:4317"
python manual.py