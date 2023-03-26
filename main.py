import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.staticfiles import StaticFiles

from services import RecommenderService, CategoricalQueryService
from models import TextRequest, CategoricalRequest

INDEX_VECTORS_FILE = "../../data/index_vectors.pkl"
INDEX_KEYS_FILE = "../../data/index_vectors.pkl"
QUESTIONPOSTS_COMBINED_FILE = "../../data/questionposts_combined.csv"
CATEGORICAL_QUERY_FILE = "../../data/client_questionposts.csv"
FRONTEND_DIRECTORY = "../datafest-webpage/build"

print("Starting recommender service...", end=" ", flush=True)
recommender_service = RecommenderService(INDEX_VECTORS_FILE, INDEX_KEYS_FILE, QUESTIONPOSTS_COMBINED_FILE)
recommender_service.start()
print("started.")

print("Starting categorical query service service...", end=" ", flush=True)
categorical_query_service = CategoricalQueryService(CATEGORICAL_QUERY_FILE)
print("started.")

app = FastAPI(title="app")
api_app = FastAPI(title="api-app")

app.mount("/api", api_app)  # need to do this so that it doesn't try to interpret api calls as static file requests
app.mount("/", StaticFiles(directory=FRONTEND_DIRECTORY, html=True), name="build")


@api_app.post("/text")
async def post_text(text_request: TextRequest):
    if text_request.questionUno is not None:
        # using text we provided via categorical query
        recommended_dialogs = recommender_service.query_by_existing_embedding(text_request.questionUno)
    else:
        if text_request.text is None:
            # malformed request
            raise HTTPException(status_code=400, detail="Text cannot be null")
        client_text = text_request.text
        recommended_dialogs = recommender_service.query_by_text(client_text)

    return {"recommendations": recommended_dialogs}


@api_app.post("/categoricalQuery")
async def post_categorical_query(query_request: CategoricalRequest):
    print("categoricalQuery")
    print(query_request)

    def none_if_empty(thing):
        if len(thing) == 0:
            return None
        return thing

    categories = none_if_empty(query_request.categories)
    age = none_if_empty(query_request.age)
    ethnicities = none_if_empty(query_request.ethnicities)
    genders = none_if_empty(query_request.genders)
    states = none_if_empty(query_request.states)
    print(f'{age=} {ethnicities=} {genders=} {states=}')
    result = categorical_query_service.query_question(
        categories=categories,
        age=age,
        ethnicities=ethnicities,
        genders=genders,
        states=states
    )
    if result is None:
        result = {"success": False}  # sad path
    else:
        question_uno, text = result  # happy path
        result = {
            "success": True,
            "questionUno": question_uno,
            "text": text
        }
    print(f"{result=}")
    return result


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8889)
    recommender_service.stop()
