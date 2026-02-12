from typing import Literal
import uuid
from fastapi import FastAPI, HTTPException, Response, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pydantic_ai import Agent

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Naive summary storage in memory. Could also just use localstorage in the browser.
summaries: dict[str, dict] = {}


class SummarizeRequest(BaseModel):
    text: str
    language: Literal["en", "fi", "sv"] = "en"


class SummaryResponse(BaseModel):
    summary: str
    key_points: list[str]
    language: str


class SummaryFailure(BaseModel):
    reason: str


SYSTEM_PROMPT = f"""
You are a medical transcription assistant. Summarize the provided text into a single clear paragraph translated into the provided language.
<instructions>
1. Identify if the text is a medical transcript and you can identify the desired language.
2. If it is not, return a {SummaryFailure.__name__} with the reason.
3. If it is, return a {SummaryResponse.__name__} with the summary and key points.
    - The key points should be a list of 3-5 key points that are most important in the text.
</instructions>
<policy>
* The summary should be no longer than 100 words.
</policy>
"""

# A simple agent, could just call gemini directly but this is a bit more flexible as we can change the provider
# and add more tools later.
summarize_agent = Agent(
    model="google-gla:gemini-3-flash-preview",
    system_prompt=SYSTEM_PROMPT,
    output_type=[SummaryFailure, SummaryResponse],
)


@app.post("/summarize", response_model=SummaryResponse)
async def summarize(
    request: SummarizeRequest, response: Response, session_id: str | None = Cookie(None)
):
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie(key="session_id", value=session_id)

    prompt = f"<text>{request.text}</text><language>{request.language}</language>"

    result = await summarize_agent.run(prompt)

    if isinstance(result.output, SummaryFailure):
        # NB; Maybe not ideal to leak this verbatim to the user
        raise HTTPException(status_code=400, detail=result.output.reason)

    summaries[session_id] = {
        "summary": result.output.summary,
        "key_points": result.output.key_points,
        "language": request.language,
    }

    return result.output


@app.get("/summary", response_model=SummaryResponse)
async def get_summary(session_id: str | None = Cookie(None)):
    if session_id and session_id in summaries:
        data = summaries[session_id]
        return SummaryResponse(
            summary=data["summary"],
            key_points=data["key_points"],
            language=data["language"],
        )

    # NB; Could also just return 404 here.
    return SummaryResponse(summary="", key_points=[], language="en")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8888)
