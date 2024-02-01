import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.database import DB
from src.frontend import router as router_front


app = FastAPI()
db = DB()

app.include_router(router_front, prefix="")
app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent / "static"))


def main():
    db.initialize()
    uvicorn.run(app, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
