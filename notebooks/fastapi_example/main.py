from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    text: str = None
    is_done: bool = False

items = []  # In-memory storage for items

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/items")                             # curl -X POST -H "Content-Type: application/json" 'http://127.0.0.1:8000/items?item=orange' -- non pydantic
def create_item(item: Item):                    # curl -X POST -H "Content-Type: application/json" -d '{"text":"orange"}'  'http://127.0.0.1:8000/items'
    items.append(item)
    return items

@app.get("/items")                              # curl -X GET 'http://127.0.0.1:8000/items?limit=9'
def list_items(limit: int = 10, response_model=list[Item]):  
    return items[:limit]

@app.get("/items/{item_id:int}", response_model=Item)                # curl -X GET http://127.0.0.1:8000/items/0
def get_item(item_id: int) -> Item:
    if item_id < len(items):
        item = items[item_id]
        return item
    else:
        raise HTTPException(status_code=404, detail="Item not found")
    