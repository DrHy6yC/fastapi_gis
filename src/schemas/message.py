from pydantic import BaseModel


class Message(BaseModel):
    detail: str


class MessageID(BaseModel):
    id: int
