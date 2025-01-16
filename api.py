from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from contextual_response import ContextualResponseGenerator
from bot_service import handle_query_response, HELP_CHANNEL_ID

# Initialize FastAPI app
app = FastAPI(
    title="RAG Chat API",
    description="API for retrieving context-aware responses using RAG",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the response generator
response_generator = ContextualResponseGenerator()

class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str = Field(..., description="The user's question")
    max_context: Optional[int] = Field(5, description="Maximum number of context messages to include")
    use_cache: Optional[bool] = Field(True, description="Whether to use response caching")
    send_to_chat: Optional[bool] = Field(False, description="Whether to send the response to chat")
    channel_id: Optional[str] = Field(HELP_CHANNEL_ID, description="The channel ID to send the response to")

@app.post("/query")
async def query(request: QueryRequest):
    """
    Get a contextual response for a query.
    
    Args:
        request (QueryRequest): The query request containing:
            - query: The user's question
            - max_context: Maximum number of context messages (optional)
            - use_cache: Whether to use caching (optional)
            - send_to_chat: Whether to send response to chat (optional)
            - channel_id: The channel ID to send the response to (optional)
    
    Returns:
        dict: The response containing the answer and context
    """
    try:
        print(f"Processing query: {request.query}")
        
        # If sending to chat, validate channel
        if request.send_to_chat and request.channel_id != HELP_CHANNEL_ID:
            raise HTTPException(
                status_code=400, 
                detail=f"Bot responses are only available in the help channel"
            )
            
        response = response_generator.generate_response(
            query=request.query,
            max_context=request.max_context,
            use_cache=request.use_cache
        )
        
        # If requested, send the response to chat
        if request.send_to_chat:
            try:
                print(f"Sending response to chat in channel: {request.channel_id}")
                handle_query_response(request.query, response['answer'], channel_id=request.channel_id)
            except Exception as e:
                print(f"Warning: Failed to send message to chat: {e}")
                # Continue with the API response even if chat message fails
        
        return response
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 










    # curl -X POST "http://localhost:8000/query" \
    #  -H "Content-Type: application/json" \
    #  -d '{"query": "What are some recommended VS Code extensions?"}'