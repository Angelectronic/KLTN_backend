from fastapi import APIRouter, HTTPException
from ..view.test_bank import TestRequest
from ..model import test_bank

router = APIRouter(prefix="/test_bank", tags=["test_bank"])

@router.post("/create")
async def create_test(test: TestRequest):
    test_bank.insert_test(test)
    return {"message": "Test created successfully"}

@router.post("/create-auto")
async def create_test_auto(category_id: str, hardQuestionCount: int, easyQuestionCount: int, mediumQuestionCount: int):
    results = test_bank.auto_create_test(category_id, hardQuestionCount, easyQuestionCount, mediumQuestionCount)
    if isinstance(results, dict):
        raise HTTPException(status_code=400, detail=results["message"])
    return results

@router.put("/edit/{test_id}")
async def edit_test(test: TestRequest, test_id: str):
    test_bank.edit_test(test_id, test)

    return {"message": "Edit test"}

@router.get("/search")
async def search_by_name(name: str):
    items = test_bank.search_by_name(name)
    if not items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items