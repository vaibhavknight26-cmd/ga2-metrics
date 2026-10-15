import time
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response

app = FastAPI()

EMAIL = "24f2000638@ds.study.iitm.ac.in"
ALLOWED_ORIGIN = "https://dash-8kkk8n.example.com"


@app.middleware("http")
async def request_headers_and_cors(request, call_next):
    start = time.perf_counter()
    request_id = str(uuid.uuid4())
    origin = request.headers.get("origin")

    if request.method == "OPTIONS" and request.url.path == "/stats":
        if origin == ALLOWED_ORIGIN:
            response = Response(status_code=200)
            response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            requested_headers = request.headers.get(
                "access-control-request-headers"
            )
            if requested_headers:
                response.headers["Access-Control-Allow-Headers"] = requested_headers
        else:
            response = Response(status_code=403)
    else:
        response = await call_next(request)

    if origin == ALLOWED_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
        response.headers["Vary"] = "Origin"

    response.headers["X-Request-ID"] = request_id
    elapsed = max(time.perf_counter() - start, 0.0)
    response.headers["X-Process-Time"] = f"{elapsed:.6f}"
    return response


@app.get("/stats")
def stats(values: str):
    try:
        numbers = [int(value.strip()) for value in values.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Values must be integers")

    if not numbers or any(value == "" for value in values.split(",")):
        raise HTTPException(status_code=400, detail="Provide comma-separated integers")

    return JSONResponse({
        "email": EMAIL,
        "count": len(numbers),
        "sum": sum(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "mean": sum(numbers) / len(numbers),
    })

from pydantic import BaseModel
import jwt

ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-7843x1mg.apps.exam.local"

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""


class VerifyRequest(BaseModel):
    token: str


@app.post("/verify")
def verify_token(body: VerifyRequest):
    try:
        claims = jwt.decode(
            body.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={"require": ["exp", "iss", "aud", "sub", "email"]},
        )
        return {
            "valid": True,
            "email": claims["email"],
            "sub": claims["sub"],
            "aud": claims["aud"],
        }
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        return JSONResponse(
            status_code=401,
            content={"valid": False},
        )

