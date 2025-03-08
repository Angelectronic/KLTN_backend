from typing import List, Union
import pymongo
from ..view.test_bank import TestRequest, TestResponse
from ..view.category import Category
from bson import ObjectId
from ..view.question_bank import QuestionResponse
import datetime

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mcq_grading_system"]
test_collection = db["tests"]
question_collection = db["questions"]
category_collection = db["categories"]

def insert_test(test: Union[TestRequest, List[TestRequest]]):
    result = None
    if isinstance(test, list):
        result = test_collection.insert_many([t.model_dump() for t in test])
    else:
        result = test_collection.insert_one(test.model_dump())
    return result
    

def auto_create_test(category_id: str, hardQuestionCount: int, easyQuestionCount: int, mediumQuestionCount: int):

    def get_questions(difficulty, count):
        return list(question_collection.aggregate([
            {"$match": {"category_id": category_id, "difficulty": difficulty, "status": True}},
            {"$sample": {"size": count}},
            {"$addFields": {"category_id": {"$toObjectId": "$category_id"}}},
            {"$lookup": {"from": "categories", "localField": "category_id", "foreignField": "_id", "as": "category"}},
            {"$unwind": "$category"},
            {"$unset": "category_id"}
        ]))

    hard_questions = get_questions("Hard", hardQuestionCount)
    if len(hard_questions) < hardQuestionCount:
        return {"message": f"Not enough hard questions in {category_id}"}

    easy_questions = get_questions("Easy", easyQuestionCount)
    if len(easy_questions) < easyQuestionCount:
        return {"message": f"Not enough easy questions in {category_id}"}

    medium_questions = get_questions("Medium", mediumQuestionCount)
    if len(medium_questions) < mediumQuestionCount:
        return {"message": f"Not enough medium questions in {category_id}"}
    
    questions = hard_questions + easy_questions + medium_questions
    custom_order = ["Easy", "Medium", "Hard"]
    questions = sorted(questions, key=lambda x: custom_order.index(x["difficulty"]))
    questions = [QuestionResponse(**q) for q in questions]

    category_item = category_collection.find_one({"_id": ObjectId(category_id), "status": True})
    category = Category(**category_item)
    
    test_response = TestResponse(title=f"Test on {category.name}", description=f"Test on {category.name} for SS1 students", category=category, lstQuestions=questions, status=True, created_at=datetime.datetime.now(), updated_at=datetime.datetime.now())
    test_request = TestRequest(title=f"Test on {category.name}", description=f"Test on {category.name} for SS1 students", category_id=category_id, lstQuestions_id=[str(q.id) for q in questions], status=True, created_at=datetime.datetime.now(), updated_at=datetime.datetime.now())

    result = insert_test(test_request)
    test_response.id = str(result.inserted_id)
    return test_response

def edit_test(test_id: str, test: TestRequest):
    dict_test = test.model_dump()
    dict_test.pop("created_at")    # delete created_at field
    test_collection.update_one({"_id": ObjectId(test_id), "status": True}, {"$set": dict_test})

def search_by_name(name: str):
    pipeline = [
        {"$match": {"title": {"$regex": name, "$options": "i"}, "status": True}},  # search by name
        {"$addFields": {"lstQuestions_id": {"$map": {"input": "$lstQuestions_id", "as": "id", "in": {"$toObjectId": "$$id"}}}, "category_id": {"$toObjectId": "$category_id"}}},  # convert lstQuestions_id to ObjectId, category_id to ObjectId

        {"$lookup": {"from": "categories", "localField": "category_id", "foreignField": "_id", "as": "category"}},  # join category
        {"$unwind": "$category"},
        {"$unset": "category_id"},
        
        {"$lookup": {"from": "questions", "localField": "lstQuestions_id", "foreignField": "_id", "as": "lstQuestions"}},  # join questions
        {"$unset": "lstQuestions_id"},
    ]
    items = list(test_collection.aggregate(pipeline))
    
    if items:
        for item in items:
            for question in item["lstQuestions"]:
                question["category_id"] = ObjectId(question["category_id"])
                question["category"] = category_collection.find_one({"_id": question["category_id"], "status": True})
                question["category"] = Category(**question["category"])
                question.pop("category_id")

    items = [TestResponse(**item) for item in items]

    return items