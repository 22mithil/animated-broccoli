from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, GetCoreSchemaHandler
from pydantic_core import core_schema
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom Pydantic type for MongoDB's ObjectId."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        def validate(v):
            if not ObjectId.is_valid(v):
                raise ValueError("Invalid ObjectId")
            return ObjectId(v)

        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(validate),
                ]),
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetCoreSchemaHandler
    ) -> Dict[str, Any]:
        """
        Update the JSON schema for OpenAPI documentation.
        """
        # Return a simple JSON schema directly instead of calling handler
        return {
            "type": "string",
            "format": "objectid",
            "example": "67f57a7b5a8c4dd89a74c781",
        }


class Message(BaseModel):
    # The 'id' field is now optional and will be assigned by MongoDB
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    query_metadata: Optional[dict] = Field(
        default=None,
        description="Additional metadata about the query and response",
    )

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


class ChatSession(BaseModel):
    # The 'id' field will be assigned by MongoDB
    id: PyObjectId = Field(alias="_id", default_factory=PyObjectId)
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }