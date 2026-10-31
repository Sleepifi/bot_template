import os
from pathlib import Path

import yaml
from pydantic import BaseModel

class Product(BaseModel):
    name:str
    price:int
    description:str=""

class Category(BaseModel):
    id: str
    title: str
    products: list[Product]


class Modules(BaseModel):
    start: bool =  True
    catalog: bool = True
    cart: bool = False
    delivery: bool = False


class ClientConfig(BaseModel):
    business_name: str
    welcome_text: str 
    contacts: str = ""
    modules: Modules = Modules()
    categories: list[Category] = []
    admins_ids: list[int] = []

def load_config() -> ClientConfig:
    path = Path("clients") / f"{os.environ["CLIENT"]}.yaml"
    with open(path,encoding="utf-8") as f:
        return ClientConfig(**yaml.safe_load(f))
