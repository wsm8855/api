import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.staticfiles import StaticFiles

from services import RecommenderService


class TextRequest(BaseModel):
    text: str


recommender_service = RecommenderService()
recommender_service.start()

app = FastAPI(title="app")
api_app = FastAPI(title="api-app")

app.mount("/api", api_app) # need to do this so that it doesn't try to interpret api calls as static file requests
app.mount("/", StaticFiles(directory="../datafest-webpage/build", html=True), name="build")


@api_app.post("/text")
async def post_text(text_request: TextRequest):
    if not text_request.text:
        raise HTTPException(status_code=400, detail="Request missing text field")
    client_text = text_request.text
    result = recommender_service.get_result(client_text)
    return {"result": result}


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
    recommender_service.stop()
