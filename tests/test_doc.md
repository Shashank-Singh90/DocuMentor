# FastAPI Quick Start

FastAPI is a modern, fast web framework for building APIs with Python 3.7+.

## Installation
```bash
pip install fastapi uvicorn
```

## Basic Example
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

## Running the App
```bash
uvicorn main:app --reload
```





