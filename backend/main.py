from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import whisper
import json
import re
from datetime import datetime
import uvicorn
import os

app = FastAPI(title="Voice CRM API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Whisper model (using base model for speed)
print("Loading Whisper model...")
whisper_model = whisper.load_model("base")
print("Whisper model loaded successfully!")

class TranscriptionRequest(BaseModel):
    text: str

class ExtractedData(BaseModel):
    customer: Dict[str, Any]
    interaction: Dict[str, Any]
    raw_text: str
    confidence: str

def extract_phone_number(text: str) -> Optional[str]:
    """Extract phone number from text"""
    # Handle spoken numbers
    text = text.lower()
    
    # Remove all spaces first, then look for patterns
    # This handles "9988 776 655" -> "9988776655"
    text_no_spaces = re.sub(r'\s+', '', text)
    
    # Try to find 10 consecutive digits
    patterns = [
        r'(\d{10})',  # 10 consecutive digits
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_no_spaces)
        if match:
            return match.group(1)
    
    # If no match yet, try with spaces/dashes in original text
    patterns_with_separators = [
        r'(\d{4}[-.\s]?\d{3}[-.\s]?\d{3})',  # Indian format: 9988-776-655
        r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',  # US format: 999-877-6655
        r'(\d{5}[-.\s]?\d{5})',  # 99887-76655
    ]
    
    for pattern in patterns_with_separators:
        match = re.search(pattern, text)
        if match:
            return re.sub(r'[-.\s]', '', match.group(1))
    
    # Handle spelled out numbers
    number_words = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
        'oh': '0'  # People often say "oh" instead of "zero"
    }
    
    # Look for sequences like "nine nine eight eight"
    words = text.split()
    consecutive_digits = []
    current_sequence = []
    
    for word in words:
        if word in number_words:
            current_sequence.append(number_words[word])
        else:
            if len(current_sequence) >= 10:
                consecutive_digits.append(''.join(current_sequence))
            current_sequence = []
    
    # Check last sequence
    if len(current_sequence) >= 10:
        consecutive_digits.append(''.join(current_sequence))
    
    # Return the first 10-digit sequence found
    for seq in consecutive_digits:
        if len(seq) >= 10:
            return seq[:10]  # Take first 10 digits
    
    return None

def extract_customer_data(text: str) -> Dict[str, Any]:
    """Extract structured customer data from text using NLP patterns"""
    
    customer = {
        "full_name": None,
        "phone": None,
        "address": None,
        "city": None,
        "locality": None
    }
    
    interaction = {
        "summary": None,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    # Extract phone number
    phone = extract_phone_number(text)
    if phone:
        customer["phone"] = phone
    
    # Extract name - look for patterns
    name_patterns = [
        r'(?:customer|client|person|spoke with|met with|contacted)\s+(?:named\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'(?:name is|called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'^([A-Z][a-z]+\s+[A-Z][a-z]+)',  # Name at start
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            customer["full_name"] = match.group(1).strip()
            break
    
    # Extract address - look for street patterns
    address_patterns = [
        r'(?:at|address|stays at|lives at|located at)\s+([0-9]+\s+[A-Za-z\s]+(?:Street|Road|Avenue|Lane|Drive|St|Rd|Ave))',
        r'([0-9]+\s+[A-Za-z\s]+(?:Street|Road|Avenue|Lane|Drive|St|Rd|Ave))',
    ]
    
    for pattern in address_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            customer["address"] = match.group(1).strip()
            break
    
    # Extract city - common Indian cities or look for patterns
    cities = ['Mumbai', 'Delhi', 'Bangalore', 'Kolkata', 'Chennai', 'Hyderabad', 
              'Pune', 'Ahmedabad', 'Surat', 'Jaipur', 'Lucknow', 'Kanpur']
    
    for city in cities:
        if city.lower() in text.lower():
            customer["city"] = city
            break
    
    # If no city found, try pattern matching
    if not customer["city"]:
        city_pattern = r'(?:in|at|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*(?:city)?'
        match = re.search(city_pattern, text)
        if match:
            potential_city = match.group(1).strip()
            if len(potential_city.split()) <= 2:
                customer["city"] = potential_city
    
    # Extract locality/area
    locality_patterns = [
        r'(?:in|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*,\s*[A-Z]',
        r',\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*,',
    ]
    
    for pattern in locality_patterns:
        match = re.search(pattern, text)
        if match:
            customer["locality"] = match.group(1).strip()
            break
    
    # Extract interaction summary
    summary_keywords = ['discussed', 'talked about', 'next steps', 'demo', 'meeting', 
                        'presentation', 'proposal', 'follow-up', 'requirement']
    
    sentences = re.split(r'[.!?]', text)
    summary_sentences = []
    
    for sentence in sentences:
        if any(keyword in sentence.lower() for keyword in summary_keywords):
            summary_sentences.append(sentence.strip())
    
    if summary_sentences:
        interaction["summary"] = '. '.join(summary_sentences)
    else:
        # Take the last meaningful sentence as summary
        meaningful = [s.strip() for s in sentences if len(s.strip()) > 20]
        if meaningful:
            interaction["summary"] = meaningful[-1]
    
    return {
        "customer": customer,
        "interaction": interaction
    }

@app.post("/api/transcribe", response_model=ExtractedData)
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio file and extract structured data"""
    try:
        # Save uploaded file temporarily
        temp_file = f"temp_audio_{datetime.now().timestamp()}.wav"
        with open(temp_file, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # Transcribe using Whisper
        result = whisper_model.transcribe(temp_file, language="en")
        transcribed_text = result["text"]
        
        # Clean up temp file
        os.remove(temp_file)
        
        # Extract structured data
        extracted = extract_customer_data(transcribed_text)
        
        # Calculate confidence based on extracted fields
        filled_fields = sum(1 for v in extracted["customer"].values() if v)
        confidence = "high" if filled_fields >= 3 else "medium" if filled_fields >= 2 else "low"
        
        return ExtractedData(
            customer=extracted["customer"],
            interaction=extracted["interaction"],
            raw_text=transcribed_text,
            confidence=confidence
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/extract", response_model=ExtractedData)
async def extract_from_text(request: TranscriptionRequest):
    """Extract structured data from pre-transcribed text"""
    try:
        extracted = extract_customer_data(request.text)
        
        # Calculate confidence
        filled_fields = sum(1 for v in extracted["customer"].values() if v)
        confidence = "high" if filled_fields >= 3 else "medium" if filled_fields >= 2 else "low"
        
        return ExtractedData(
            customer=extracted["customer"],
            interaction=extracted["interaction"],
            raw_text=request.text,
            confidence=confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "whisper_model": "base"
    }

@app.get("/")
async def root():
    return {
        "message": "Voice CRM API",
        "endpoints": {
            "transcribe": "/api/transcribe (POST - audio file)",
            "extract": "/api/extract (POST - text)",
            "health": "/api/health (GET)"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)