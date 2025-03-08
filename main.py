from fastapi import FastAPI
from .mvc.controller import question_bank, test_bank, category

app = FastAPI()

app.include_router(question_bank.router)
app.include_router(test_bank.router)
app.include_router(category.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}