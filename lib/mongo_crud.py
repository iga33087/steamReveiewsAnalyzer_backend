from __future__ import annotations

import os
from typing import Any, Iterable

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError
from pymongo.results import DeleteResult, InsertManyResult, InsertOneResult, UpdateResult


class MongoCRUDError(Exception):
    """Raised when a MongoDB operation fails."""


class MongoCRUD:
    """Reusable helper for common MongoDB CRUD operations."""

    def __init__(
        self,
        database_name: str,
        uri: str | None = None,
        *,
        server_selection_timeout_ms: int = 5000,
    ) -> None:
        self.uri = uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.client: MongoClient = MongoClient(
            self.uri,
            serverSelectionTimeoutMS=server_selection_timeout_ms,
        )
        self.db: Database = self.client[database_name]

    def __enter__(self) -> MongoCRUD:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def collection(self, collection_name: str) -> Collection:
        return self.db[collection_name]

    def close(self) -> None:
        try:
            self.client.close()
        except PyMongoError as exc:
            raise MongoCRUDError("Failed to close MongoDB connection.") from exc

    def ping(self) -> bool:
        try:
            self.client.admin.command("ping")
            return True
        except PyMongoError as exc:
            raise MongoCRUDError("Failed to connect to MongoDB.") from exc

    def insert_one(self, collection_name: str, document: dict[str, Any]) -> ObjectId:
        try:
            result: InsertOneResult = self.collection(collection_name).insert_one(document)
            return result.inserted_id
        except PyMongoError as exc:
            raise MongoCRUDError(f"Failed to insert document into '{collection_name}'.") from exc

    def insert_many(
        self,
        collection_name: str,
        documents: Iterable[dict[str, Any]],
    ) -> list[ObjectId]:
        try:
            result: InsertManyResult = self.collection(collection_name).insert_many(list(documents))
            return result.inserted_ids
        except PyMongoError as exc:
            raise MongoCRUDError(f"Failed to insert documents into '{collection_name}'.") from exc

    def find_one(
        self,
        collection_name: str,
        query: dict[str, Any] | None = None,
        projection: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        try:
            return self.collection(collection_name).find_one(query or {}, projection)
        except PyMongoError as exc:
            raise MongoCRUDError(f"Failed to query one document from '{collection_name}'.") from exc

    def find_many(
        self,
        collection_name: str,
        query: dict[str, Any] | None = None,
        projection: dict[str, Any] | None = None,
        *,
        sort: list[tuple[str, int]] | None = None,
        limit: int = 0,
        skip: int = 0,
    ) -> list[dict[str, Any]]:
        try:
            cursor = self.collection(collection_name).find(query or {}, projection)

            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)

            return list(cursor)
        except PyMongoError as exc:
            raise MongoCRUDError(f"Failed to query documents from '{collection_name}'.") from exc

    def update_one(
        self,
        collection_name: str,
        query: dict[str, Any],
        update_data: dict[str, Any],
        *,
        upsert: bool = False,
    ) -> dict[str, int | ObjectId | None]:
        try:
            result: UpdateResult = self.collection(collection_name).update_one(
                query,
                {"$set": update_data},
                upsert=upsert,
            )
            return {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": result.upserted_id,
            }
        except PyMongoError as exc:
            raise MongoCRUDError(f"Failed to update one document in '{collection_name}'.") from exc

    def update_many(
        self,
        collection_name: str,
        query: dict[str, Any],
        update_data: dict[str, Any],
        *,
        upsert: bool = False,
    ) -> dict[str, int | ObjectId | None]:
        try:
            result: UpdateResult = self.collection(collection_name).update_many(
                query,
                {"$set": update_data},
                upsert=upsert,
            )
            return {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": result.upserted_id,
            }
        except PyMongoError as exc:
            raise MongoCRUDError(f"Failed to update documents in '{collection_name}'.") from exc

    def replace_one(
        self,
        collection_name: str,
        query: dict[str, Any],
        replacement: dict[str, Any],
        *,
        upsert: bool = False,
    ) -> dict[str, int | ObjectId | None]:
        try:
            result: UpdateResult = self.collection(collection_name).replace_one(
                query,
                replacement,
                upsert=upsert,
            )
            return {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": result.upserted_id,
            }
        except PyMongoError as exc:
            raise MongoCRUDError(f"Failed to replace document in '{collection_name}'.") from exc

    def delete_one(self, collection_name: str, query: dict[str, Any]) -> int:
        try:
            result: DeleteResult = self.collection(collection_name).delete_one(query)
            return result.deleted_count
        except PyMongoError as exc:
            raise MongoCRUDError(f"Failed to delete one document from '{collection_name}'.") from exc

    def delete_many(self, collection_name: str, query: dict[str, Any]) -> int:
        try:
            result: DeleteResult = self.collection(collection_name).delete_many(query)
            return result.deleted_count
        except PyMongoError as exc:
            raise MongoCRUDError(f"Failed to delete documents from '{collection_name}'.") from exc


def to_object_id(value: str | ObjectId) -> ObjectId:
    """Convert a string id to ObjectId for querying by MongoDB _id."""
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(value)
    except InvalidId as exc:
        raise MongoCRUDError(f"Invalid ObjectId: {value}") from exc
