import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse

from services import RecommenderService


class TextRequest(BaseModel):
    text: str


def get_frontend():
    with open("index.html", 'r') as f:
        lines = f.readlines()
    html_content = "\n".join(lines)
    return html_content


recommender_service = RecommenderService()
recommender_service.start()
app = FastAPI()


@app.get("/")
async def root():
    return HTMLResponse(get_frontend(), status_code=200)


@app.post("/text")
async def post_text(text_request: TextRequest):
    if not text_request.text:
        raise HTTPException(status_code=400, detail="Request missing text field")
    client_text = text_request.text
    result = recommender_service.get_result(client_text)
    return {"result": result}


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
    recommender_service.stop()
