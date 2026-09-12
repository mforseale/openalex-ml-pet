from fastapi import FastAPI

app = FastAPI(
    title="OpenAlex Platform",
    version="0.1.0"
)


@app.get("/")
def root():
    return {"message": "OpenAlex Platform is running"}


@app.get("/health")
def health():
    return {"status": "ok"}
