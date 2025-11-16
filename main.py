import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import create_document, get_documents, db
from schemas import Registration

app = FastAPI(title="Health & Safety Summit API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Health & Safety Summit API is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Welcome to the Health & Safety Summit"}

# Public content endpoints
class Session(BaseModel):
    id: str
    title: str
    speaker: str
    time: str
    track: str
    description: str

SESSIONS: List[Session] = [
    Session(id="ergonomics-101", title="Ergonomics 101", speaker="Dr. Maya Chen", time="09:00 - 09:45", track="Workplace Safety", description="Foundations of ergonomic design to prevent strain and injury."),
    Session(id="fire-safety", title="Modern Fire Safety Protocols", speaker="Captain Luis Ortega", time="10:00 - 10:45", track="Emergency Response", description="Latest standards, drills and equipment for fire safety."),
    Session(id="mental-health", title="Mental Health at Work", speaker="Sara Patel, LCSW", time="11:00 - 11:45", track="Wellbeing", description="Reducing stigma and building supportive cultures."),
]

@app.get("/api/sessions", response_model=List[Session])
async def list_sessions():
    return SESSIONS

# Registration endpoints (persisted)
@app.post("/api/register")
async def register_attendee(payload: Registration):
    try:
        inserted_id = create_document("registration", payload)
        return {"ok": True, "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/registrations")
async def get_registrations(limit: Optional[int] = 50):
    try:
        docs = get_documents("registration", limit=limit)
        # Convert ObjectId and datetime to strings
        def _ser(d):
            d = dict(d)
            if d.get("_id"):
                d["_id"] = str(d["_id"])
            for k, v in list(d.items()):
                if hasattr(v, "isoformat"):
                    d[k] = v.isoformat()
            return d
        return {"ok": True, "items": [_ser(doc) for doc in docs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
