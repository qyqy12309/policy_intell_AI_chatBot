"""
Main API Server
===============
FastAPI server for Conversational Insurance Assistant
Handles all stages: Entry, Conversation, Document Intelligence, Commerce, and Predictive Intelligence
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Form, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict
import os
from dotenv import load_dotenv
import shutil
import tempfile
from pathlib import Path

# Import backend modules
from conversation_engine import ConversationEngine
from document_intelligence import DocumentIntelligence
from commerce import QuoteService
from predictive_intelligence import PredictiveIntelligence

# Import core engine modules (if available)
try:
    from core.vector_store import VectorStore
    from core.rag_qa import PolicyQASystem
except ImportError:
    VectorStore = None
    PolicyQASystem = None

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Conversational Insurance Assistant API",
    description="AI-driven chat experience for insurance policies",
    version="2.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
vector_store = None
qa_system = None
conversation_engine = None
doc_intelligence = None
quote_service = None
predictive_intel = None
llm_model = "llama3"


@app.on_event("startup")
async def startup_event():
    """
    Initialize all components when server starts.
    """
    global vector_store, qa_system, conversation_engine, doc_intelligence
    global quote_service, predictive_intel, llm_model
    
    # Get LLM model from environment
    llm_model = os.getenv("OLLAMA_MODEL", "llama3")
    
    # Initialize vector store and Q&A if available
    try:
        if VectorStore:
            db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
            vector_store = VectorStore(db_path=db_path)
            
            if PolicyQASystem:
                qa_system = PolicyQASystem(vector_store, llm_model=llm_model)
    except Exception as e:
        print(f"Warning: Could not initialize vector store: {e}")
    
    # Initialize conversation engine
    conversation_engine = ConversationEngine(
        vector_store=vector_store,
        qa_system=qa_system,
        llm_model=llm_model
    )
    
    # Initialize document intelligence
    doc_intelligence = DocumentIntelligence(llm_model=llm_model)
    
    # Initialize quote service
    quote_service = QuoteService(vector_store=vector_store, qa_system=qa_system)
    
    # Initialize predictive intelligence
    predictive_intel = PredictiveIntelligence(llm_model=llm_model)
    
    print(f"✓ Conversational Insurance Assistant initialized with Ollama model: {llm_model}")


# ==================== Stage 0-2: Conversation Endpoints ====================

@app.post("/api/conversation/start")
async def start_conversation(
    user_id: str = Query(..., description="Unique user identifier"),
    persona: str = Query("travel_guru", description="Persona: travel_guru, advisor, or companion")
):
    """
    Stage 0: Start a new conversation session.
    
    Creates greeting and initializes user session.
    """
    try:
        result = conversation_engine.start_conversation(user_id, persona)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting conversation: {str(e)}")


@app.post("/api/conversation/message")
async def handle_message(
    user_id: str = Query(..., description="User identifier"),
    message: str = Query(..., description="User message"),
    use_qa: bool = Query(True, description="Use Q&A system for policy questions")
):
    """
    Stage 2: Handle user message and generate response.
    
    Detects intent, extracts entities, and generates conversational response.
    """
    try:
        response = conversation_engine.generate_response(
            message, 
            user_id, 
            use_qa_system=use_qa
        )
        return JSONResponse(content=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@app.get("/api/conversation/session/{user_id}")
async def get_session(user_id: str):
    """
    Get user conversation session.
    
    Returns conversation history and context.
    """
    try:
        session = conversation_engine.get_session(user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return JSONResponse(content=session)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session: {str(e)}")


@app.post("/api/conversation/persona")
async def update_persona(
    user_id: str = Query(..., description="User identifier"),
    persona: str = Query(..., description="New persona: travel_guru, advisor, or companion")
):
    """
    Switch conversation persona.
    """
    try:
        success = conversation_engine.update_persona(user_id, persona)
        if not success:
            raise HTTPException(status_code=400, detail="Invalid persona")
        return JSONResponse(content={"success": True, "persona": persona})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating persona: {str(e)}")


# ==================== Stage 3: Document Intelligence Endpoints ====================

@app.post("/api/document/extract")
async def extract_travel_info(
    file: UploadFile = File(..., description="Travel document (itinerary, confirmation, etc.)")
):
    """
    Stage 3: Extract travel information from uploaded document.
    
    Extracts destination, dates, travelers, flights, etc.
    """
    try:
        # Save uploaded file temporarily
        file_ext = os.path.splitext(file.filename)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        # Extract information
        result = doc_intelligence.extract_travel_info(tmp_path)
        
        # Clean up
        os.unlink(tmp_path)
        
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting info: {str(e)}")


@app.post("/api/document/suggest-coverage")
async def suggest_coverage(trip_info: Dict = Body(...)):
    """
    Suggest insurance coverage based on trip information.
    """
    try:
        suggestions = doc_intelligence.suggest_coverage_from_trip(trip_info)
        return JSONResponse(content=suggestions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating suggestions: {str(e)}")


@app.post("/api/document/auto-fill")
async def auto_fill_form(trip_info: Dict = Body(...)):
    """
    Auto-fill quote form from trip information.
    """
    try:
        form_data = doc_intelligence.auto_fill_quote_form(trip_info)
        return JSONResponse(content=form_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error auto-filling form: {str(e)}")


# ==================== Stage 4: Commerce Endpoints ====================

@app.post("/api/commerce/quotes")
async def get_quotes(trip_info: Dict = Body(...)):
    """
    Stage 4: Generate insurance quotes for a trip.
    
    Returns quote cards with prices and coverage details.
    """
    try:
        quotes_data = quote_service.get_quotes(trip_info)
        return JSONResponse(content=quotes_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quotes: {str(e)}")


@app.post("/api/commerce/purchase/initiate")
async def initiate_purchase(
    quote_id: str = Query(..., description="Quote identifier"),
    trip_info: Dict = Form(...),
    user_info: Dict = Form(...)
):
    """
    Initiate purchase flow - creates payment link.
    """
    try:
        result = quote_service.initiate_purchase(quote_id, trip_info, user_info)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initiating purchase: {str(e)}")


@app.post("/api/commerce/purchase/complete")
async def complete_purchase(
    transaction_id: str = Query(..., description="Transaction identifier"),
    quote_id: str = Query(..., description="Quote identifier"),
    payment_data: Dict = Form(...),
    trip_info: Dict = Form(...),
    user_info: Dict = Form(...)
):
    """
    Complete purchase after payment - issues policy.
    """
    try:
        result = quote_service.complete_purchase(
            transaction_id, payment_data, quote_id, trip_info, user_info
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing purchase: {str(e)}")


# ==================== Stage 5: Predictive Intelligence Endpoints ====================

@app.post("/api/predictive/risk-assessment")
async def assess_risk(
    trip_info: Dict = Body(...),
    user_info: Optional[Dict] = Body(None)
):
    """
    Stage 5: Assess risk profile for a trip.
    
    Returns risk score, level, and recommendations.
    """
    try:
        risk_profile = predictive_intel.assess_risk_profile(trip_info, user_info)
        return JSONResponse(content=risk_profile)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assessing risk: {str(e)}")


@app.post("/api/predictive/claim-prediction")
async def predict_claims(
    trip_info: Dict = Body(...),
    policy_info: Dict = Body(...),
    user_info: Optional[Dict] = Body(None)
):
    """
    Predict claim likelihood for a trip/policy combination.
    """
    try:
        prediction = predictive_intel.predict_claim_likelihood(trip_info, policy_info, user_info)
        return JSONResponse(content=prediction)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting claims: {str(e)}")


@app.post("/api/predictive/nudges")
async def get_smart_nudges(
    user_id: str = Query(..., description="User identifier"),
    trip_info: Dict = Body(...),
    policy: Optional[Dict] = Body(None)
):
    """
    Generate smart nudges for user.
    
    Examples: trip reminders, coverage suggestions, flight delay alerts.
    """
    try:
        nudges = predictive_intel.generate_smart_nudges(user_id, trip_info, policy)
        return JSONResponse(content={"nudges": nudges, "count": len(nudges)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating nudges: {str(e)}")


@app.post("/api/predictive/flight-delay")
async def check_flight_delay(
    flight_info: Dict = Body(...),
    policy: Dict = Body(...)
):
    """
    Check for flight delays and notify about coverage.
    """
    try:
        nudge = predictive_intel.detect_flight_delay(flight_info, policy)
        if nudge:
            return JSONResponse(content=nudge)
        else:
            return JSONResponse(content={"delay_detected": False})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking flight delay: {str(e)}")


# ==================== Health and Info Endpoints ====================

@app.get("/")
async def root():
    """
    API information and available endpoints.
    """
    return {
        "message": "Conversational Insurance Assistant API",
        "version": "2.0.0",
        "stages": {
            "Stage 0-2": "Conversation Engine (Entry, Intent, Chat)",
            "Stage 3": "Document Intelligence (Extract trip info)",
            "Stage 4": "Commerce (Quotes, Payment, Policy)",
            "Stage 5": "Predictive Intelligence (Risk, Claims, Nudges)"
        },
        "endpoints": {
            "conversation": "/api/conversation/*",
            "document": "/api/document/*",
            "commerce": "/api/commerce/*",
            "predictive": "/api/predictive/*"
        }
    }


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "components": {
            "conversation_engine": conversation_engine is not None,
            "document_intelligence": doc_intelligence is not None,
            "quote_service": quote_service is not None,
            "predictive_intelligence": predictive_intel is not None,
            "vector_store": vector_store is not None,
            "qa_system": qa_system is not None
        },
        "llm_model": llm_model
    }


# Run the server
if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(app, host=host, port=port)

