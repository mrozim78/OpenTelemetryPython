import os

from flask import Flask, request


#OpenTelemetry methods
from opentelemetry.instrumentation.wsgi import collect_request_attributes
from opentelemetry.propagate import extract

#OpenTelemetry resources
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_INSTANCE_ID,  Resource

#OpenTelemetry traces
from opentelemetry.trace import set_tracer_provider, SpanKind, get_current_span
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

EXPOSE_PORT = int(os.environ.get("MANUAL_EXPOSE_PORT", 8000))
OTLP_ENDPOINT = os.environ.get("MANUAL_OTLP_ENDPOINT", "http://localhost:4317")
OTLP_SERVICE_NAME = os.environ.get("MANUAL_SERVICE_NAME", "manual")
OTLP_SERVICE_INSTANCE_ID = os.environ.get("MANUAL_SERVICE_INSTANCE_ID", "manual-instance-1")

app = Flask(__name__)

#OpenTelemetry resources
resource = Resource(attributes={
    SERVICE_NAME: OTLP_SERVICE_NAME,
    SERVICE_INSTANCE_ID: OTLP_SERVICE_INSTANCE_ID
})

#Traces
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_ENDPOINT))
provider.add_span_processor(processor)
set_tracer_provider(provider)
tracer = provider.get_tracer(__name__)


@app.route("/")
def read_root():
    with tracer.start_as_current_span ( 
        name= "/",
        context = extract(request.headers),
        kind= SpanKind.SERVER,
        attributes=collect_request_attributes(request.environ)
    ) as parent : 
        with tracer.start_as_current_span (
            name = "Run root method",
            kind = SpanKind.INTERNAL
        ) as child : 
            child.add_event("Start root method")
            child.add_event("End root method")
            get_current_span()
        get_current_span()
    return {"Hello": "World"}
    

@app.route("/test")
def read_test():
   with tracer.start_as_current_span (
        name= "/test",
        context = extract(request.headers),
        kind= SpanKind.SERVER,
        attributes=collect_request_attributes(request.environ)
    ) as parent : 
        with tracer.start_as_current_span (
            name= "Run test method",
            kind = SpanKind.INTERNAL
        ) as child : 
            child.add_event("Start test method")
            child.add_event("End test method")
            get_current_span()
        get_current_span()    
   return {"tested":True}

if __name__ == "__main__":
    app.run(port=EXPOSE_PORT)