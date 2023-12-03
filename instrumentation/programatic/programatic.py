import os
import logging
import httpx

#Httpx instrumentation
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

#Flask
from flask import Flask
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.wsgi import collect_request_attributes

#OpenTelemetry resources
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_INSTANCE_ID, Resource

#OpenTelemetry traces
from opentelemetry.trace import set_tracer_provider, get_current_span,  SpanKind
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

#OpenTelemetry logs
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler 
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

#OpenTelemetry metrics
from opentelemetry.metrics import set_meter_provider
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader


# Read variables
EXPOSE_PORT = int(os.environ.get("PROGRAMATIC_EXPOSE_PORT", 8000))
OTLP_ENDPOINT = os.environ.get("PROGRAMATIC_OTLP_ENDPOINT", "http://localhost:4317")
OTLP_SERVICE_NAME = os.environ.get("PROGRAMATIC_SERVICE_NAME", "programatic")
OTLP_SERVICE_INSTANCE_ID = os.environ.get("PROGRAMATIC__SERVICE_INSTANCE_ID", "programatic-instance-1")


# Flask instrumentator
instrumentor = FlaskInstrumentor()
LoggingInstrumentor()


app = Flask(__name__)

# Resource OpenTelemetry
resource = Resource(attributes={
    SERVICE_NAME: OTLP_SERVICE_NAME,
    SERVICE_INSTANCE_ID: OTLP_SERVICE_INSTANCE_ID
})


# Traces
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_ENDPOINT))
provider.add_span_processor(processor)

set_tracer_provider(provider)
tracer = provider.get_tracer(__name__)
instrumentor.instrument_app(app=app , tracer_provider=provider)


#Logs
LoggingInstrumentor().instrument(set_logging_format=True)
logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)

logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(endpoint=OTLP_ENDPOINT)))
handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)

logger=logging.getLogger("programatic")
logger.addHandler(handler)


# Metrics
configurationMetrics = {
    "system.memory.usage": ["used", "free", "cached"],
    "system.cpu.time": ["idle", "user", "system", "irq"],
    "process.runtime.memory": ["rss", "vms"],
    "process.runtime.cpu.time": ["user", "system"]
}

meter_provider = MeterProvider(resource=resource, metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=OTLP_ENDPOINT))])
set_meter_provider(meter_provider)
SystemMetricsInstrumentor(config=configurationMetrics).instrument()

#Httpx instrumentator
HTTPXClientInstrumentor().instrument()

#Routings
@app.route("/")
def read_root():
    with tracer.start_as_current_span(
       name="Run root method",
       kind=SpanKind.INTERNAL
    ) as parent :
        logger.error("Root method run")
        parent.add_event("Start root method")
        logger.error("Start request test method")
        with httpx.Client() as client:
            client.get(f"http://localhost:{EXPOSE_PORT}/test")
        logger.error("End request test method")        
        parent.add_event("End root method")
        get_current_span()
    return {"Hello": "World"}
    

@app.route("/test")
def read_test():
   with tracer.start_as_current_span(
       "Test method run",
       kind=SpanKind.INTERNAL
   ) as parent :
        logger.error("Test method run")
        parent.add_event("Start test method")
        parent.add_event("End test method")
        get_current_span()
   return {"tested":True}

if __name__ == "__main__":
    app.run(port=EXPOSE_PORT)