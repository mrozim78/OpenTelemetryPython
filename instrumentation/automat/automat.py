import logging
import os
import uvicorn
from fastapi import FastAPI, Response

app = FastAPI()
EXPOSE_PORT = int(os.environ.get("AUTOMAT_EXPOSE_PORT", 8000))

@app.get("/")
async def read_root():
    logging.error("Root method")
    return {"Hello": "World"}


@app.get("/test")
async def read_test():
    logging.error("Test method")
    return {"tested":True}


if __name__ == "__main__":
    # update uvicorn access logger format
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s] - %(message)s"
    uvicorn.run(app, host="0.0.0.0", port=EXPOSE_PORT , log_config= log_config)