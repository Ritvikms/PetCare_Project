from bson import ObjectId
import pymongo

dbClient = pymongo.MongoClient("mongodb://localhost:27017/")
db = dbClient["pet_care"]

admin = db["admin"]
services = db["services"]
service_providers = db["service_providers"]
service_provider_services = db["service_provider_services"]
users = db["users"]
pets = db["pets"]
appointments = db["appointments"]
bookings = db["bookings"]
payments = db["payments"]

hosts = db["Hosts"]
admins = db["Admins"]
categories = db["Categories"]
countries = db["Countries"]
properties = db["Properties"]
ratings = db["Ratings"]


def getCountryById(id):
    return countries.find_one({"_id": ObjectId(id)})


def getUserById(id):
    return users.find_one({"_id": ObjectId(id)})


def getRatingsByPropertyId(property_id):
    prp_ratings = ratings.aggregate(
        [
            {"$match": {"property_id": ObjectId(property_id)}},
            {
                "$group": {
                    "_id": "null",
                    "totalRatings": {"$sum": "$rating"},
                    "count": {"$sum": 1},
                }
            },
        ]
    )
    prp_ratings = list(prp_ratings)
    if prp_ratings:
        propertyRating = round(
            int(prp_ratings[0]["totalRatings"]) / int(prp_ratings[0]["count"]), 1
        )
        return {"propertyRating": propertyRating, "count": prp_ratings[0]["count"]}
    else:
        return {"propertyRating": 0, "count": 0}


def getProviderCountByServiceId(service_id):
    return service_provider_services.count_documents(
        {"service_id": ObjectId(service_id)}
    )


def getTimeSlot(provider_service_id, time_slot_id):
    provider_services = service_provider_services.aggregate(
        [
            {
                "$match": {
                    "_id": ObjectId(provider_service_id),
                    "time_slots.id": ObjectId(time_slot_id),
                }
            },
            {
                "$project": {
                    "time_slots": {
                        "$filter": {
                            "input": "$time_slots",
                            "as": "time_slot",
                            "cond": {"$eq": ["$$time_slot.id", ObjectId(time_slot_id)]},
                        }
                    }
                }
            },
        ]
    )
    provider_services = list(provider_services)
    time_slot = provider_services[0]["time_slots"][0]["time_slot"]
    return time_slot
