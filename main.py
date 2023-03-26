import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.staticfiles import StaticFiles

from services import RecommenderService, CategoricalQueryService
from models import TextRequest, CategoricalRequest

CATEGORICAL_QUERY_FILE = "../../data/client_questionposts.csv"
FRONTEND_DIRECTORY = "../datafest-webpage/build"

recommender_service = RecommenderService()
recommender_service.start()
categorical_query_service = CategoricalQueryService(CATEGORICAL_QUERY_FILE)

app = FastAPI(title="app")
api_app = FastAPI(title="api-app")

app.mount("/api", api_app)  # need to do this so that it doesn't try to interpret api calls as static file requests
app.mount("/", StaticFiles(directory=FRONTEND_DIRECTORY, html=True), name="build")


@api_app.post("/text")
async def post_text(text_request: TextRequest):
    if not text_request.text:
        raise HTTPException(status_code=400, detail="Request missing text field")
    client_text = text_request.text
    result = recommender_service.get_result(client_text)
    return {"result": result}


@api_app.get("/categoricalQuery")
async def get_categorical_query(query_request: CategoricalRequest):
    result = categorical_query_service.query_question(
        age=query_request.age,
        ethnicities=query_request.ethnicities,
        genders=query_request.genders,
        states=query_request.states
    )
    return {"result": result}


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8889)
    recommender_service.stop()
