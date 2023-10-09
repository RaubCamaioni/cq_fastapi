from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from pathlib import Path
import uuid
import io

import cadquery as cq
from model import create_stand
from collections import deque

models = deque(maxlen=10)
template = Jinja2Templates(directory="templates")


class Stand(BaseModel):
    mounts: list[tuple[float, float]]
    angle: float
    screw_size: float
    edge_padding: float
    padding: float
    thickness: float


app = FastAPI(docs_url=None, redoc_url=None)


@app.get("/stand")
def stand(request: Request):
    return template.TemplateResponse("stand.html", {"request": request})


@app.post("/backend/stand")
async def stand(stand: Stand):
    mount = create_stand(
        stand.mounts,
        stand.angle,
        stand.screw_size,
        stand.edge_padding,
        stand.padding,
        stand.thickness,
    )

    model_id = uuid.uuid4()
    stl_file = Path(f"/tmp/{model_id}.stl")

    try:
        cq.exporters.export(mount, str(stl_file))
        with open(stl_file, "rb") as f:
            model_bytes = io.BytesIO(f.read())
    finally:
        stl_file.unlink()

    models.append((str(model_id), model_bytes))

    def file_generator():
        while chunk := model_bytes.read(65536):
            yield chunk

    response = StreamingResponse(
        file_generator(), media_type="application/octet-stream"
    )
    response.headers["Content-Disposition"] = f'filename="{stl_file.name}"'

    return response


@app.get("/models/{model_id}")
async def download_file(model_id: str):
    # Replace this with the actual path to your files

    model_bytes = None
    for _id, _bytes in models:
        if _id == model_id:
            model_bytes = _bytes
            break

    if model_bytes is None:
        raise HTTPException(status_code=404, detail="File not found")

    def file_generator():
        while chunk := model_bytes.read(65536):
            yield chunk

    response = StreamingResponse(
        file_generator(), media_type="application/octet-stream"
    )
    response.headers["Content-Disposition"] = f'filename="{uuid}.stl"'

    return response
