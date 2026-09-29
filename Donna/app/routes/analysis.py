from fastapi import APIRouter, HTTPException
from config import GEMINI_API_KEY
from database import contracts_collection
from bson import ObjectId
from service.gemini_analyse import analyze_contract
from database import analysis_collection

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
)


@router.post("/analyse/{contract_id}")
async def analyse_contract(contract_id: str):
    """
    Analyze a contract using AI and return insights.
    """

    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="AI API key is not configured")
    
    contract = contracts_collection.find_one({"_id": ObjectId(contract_id)})
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not contract.get("text_content"):
        raise HTTPException(status_code=400, detail="Contract has no text content to analyze")
    
    contracts_collection.update_one({"_id": ObjectId(contract_id)}, {"$set": {"analysis_status": "in_progress"}})

    result = await analyze_contract(contract_id, contract["text_content"])

    doc = result.model_dump()
    insert_result = analysis_collection.insert_one(doc)
    result.id = str(insert_result.inserted_id)

    contracts_collection.update_one({"_id": ObjectId(contract_id)}, {"$set": {"analysis_status": "completed"}})

    return {
        "message": "Contract analyzed successfully",
        "analysis": result.model_dump(),
        "id": result.id
    }


@router.get("/{analysis_id}")
def get_analysis(analysis_id: str):
    """
    Retrieve the results of a specific analysis by ID.
    """
    analysis = analysis_collection.find_one({"_id": ObjectId(analysis_id)})

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return {
        "analysis": analysis
    }

@router.get('/')
def list_analyses():
    """
    List all analyses performed.
    """
    def _convert_obj(obj):
        # recursively convert ObjectId to str for JSON serialization
        if isinstance(obj, list):
            return [_convert_obj(v) for v in obj]
        if isinstance(obj, dict):
            new = {}
            for k, v in obj.items():
                if k == '_id':
                    new['id'] = str(v)
                else:
                    new[k] = _convert_obj(v)
            return new
        try:
            from bson import ObjectId
            if isinstance(obj, ObjectId):
                return str(obj)
        except Exception:
            pass
        return obj

    analyses = [_convert_obj(doc) for doc in analysis_collection.find({})]
    return {"analyses": analyses}

@router.get("/contract/{contract_id}")
async def get_analyses_for_contract(contract_id: str):
    """Get all analyses for a specific contract."""
    analyses = []
    cursor = analysis_collection.find({"contract_id": contract_id})

    for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        analyses.append(doc)

    return {"analyses": analyses, "total": len(analyses)}