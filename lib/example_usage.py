from mongo_crud import MongoCRUD, MongoCRUDError, to_object_id

try:
    with MongoCRUD(database_name="my_database") as mongo:
        user_id = mongo.insert_one(
            "users",
            {
                "name": "Alice",
                "email": "alice@example.com",
                "age": 28,
            },
        )
        print("inserted:", user_id)

        user = mongo.find_one("users", {"_id": to_object_id(user_id)})
        print("found:", user)

        update_result = mongo.update_one("users", {"_id": user_id}, {"age": 29})
        print("updated:", update_result)

        users = mongo.find_many("users", {"age": {"$gte": 18}}, sort=[("age", -1)], limit=10)
        print("users:", users)

        deleted_count = mongo.delete_one("users", {"_id": user_id})
        print("deleted:", deleted_count)
except MongoCRUDError as exc:
    print("MongoDB operation failed:", exc)
