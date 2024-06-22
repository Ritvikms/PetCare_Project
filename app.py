import datetime
from enum import Enum
import os
import random
import re
from datetime import date, datetime, timedelta

import pymongo
from bson import ObjectId
from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import db
from others import AppointmentStatus, ServiceProviderStatus

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = APP_ROOT + "/static"

app = Flask(__name__)
app.secret_key = "poiuytrewqasdfghjkl"


# admin Views
@app.route("/admin/")
@app.route("/admin/login/", methods=["GET", "POST"])
def admin_login():
    error_msg = ""
    if request.method == "POST":
        values = {
            "username": request.form.get("username"),
            "password": request.form.get("password"),
        }

        result = db.admin.find_one(values)
        if result:
            session["logged_in"] = True
            del result["password"]
            session["fullname"] = result["fullname"]
            session["role"] = "Admin"
            return redirect(url_for("admin_home"))
        else:
            error_msg = "Invalid Login Credentials"

    return render_template("/admin/login.html", error_msg=error_msg)


@app.route("/admin/home/")
def admin_home():
    hosts = db.hosts.count_documents({"status": True})
    verified_hosts = db.hosts.count_documents({"status": True, "is_verified": True})
    users = db.users.count_documents({"status": True})
    dashboard = {"hosts": hosts, "users": users, "verified_hosts": verified_hosts}
    return render_template("/admin/home.html", dashboard=dashboard)


# admin change password
@app.route("/admin/change-password/", methods=["GET", "POST"])
def admin_change_password():
    if request.method == "POST":
        values = {
            "password": request.form.get("password"),
        }
        result = db.admins.update_one({}, {"$set": values})
        flash("Password Updated successfully", "success")
        return redirect(url_for("admin_change_password"))

    return render_template("/admin/change-password.html")


@app.route("/admin/services/")
def admin_services():
    service = ""
    service_id = request.args.get("service_id")
    # Edit Services
    if service_id:
        service = db.services.find_one({"_id": ObjectId(service_id)})

    # get all services with status true
    services = db.services.find({"status": True})
    services = list(services)
    list.reverse(services)

    return render_template("/admin/services.html", service=service, services=services)


@app.route("/admin/services/", methods=["POST"])
def admin_services_post():
    service_name = request.form.get("service_name")
    service_id = request.form.get("service_id")
    if not service_id:
        # Add Service
        db.services.insert_one({"service_name": service_name, "status": True})
        flash("Service Added Successfully", "success")
    else:
        # Update Service
        db.services.update_one(
            {"_id": ObjectId(service_id)}, {"$set": {"service_name": service_name}}
        )
        flash("Service Updates Successfully", "success")

    return redirect(url_for("admin_services"))


# delete services
@app.route("/admin/service/delete/<service_id>/", methods=["GET"])
def admin_services_delete(service_id):
    service = db.services.find_one({"_id": ObjectId(service_id)})
    if not service:
        flash("Service Not Found", "danger")
    else:
        # Delete Service
        db.services.update_one(
            {"_id": ObjectId(service_id)}, {"$set": {"status": False}}
        )
        flash("Service Deleted Successfully", "success")

    return redirect(url_for("admin_services"))


# admin - view registered service providers
@app.route("/admin/view-service-providers/")
def admin_view_service_providers():
    providers = db.service_providers.find(
        {"status": {"$ne": ServiceProviderStatus.DELETED.name}}
    )

    providers = list(providers)
    list.reverse(providers)

    return render_template("/admin/service_providers.html", providers=providers)


# admin - view service provider details
@app.route("/admin/view-service-provider-details/<provider_id>/")
def admin_view_service_provider_details(provider_id):
    provider = db.service_providers.find_one(
        {"_id":ObjectId(provider_id),"status": {"$ne": ServiceProviderStatus.DELETED.name}}
    )
    if not provider:
        return abort(404, "Service Provider Not Found")
    return render_template("/admin/service_provider_details.html", provider=provider)


# admin approve service provider
@app.route("/admin/approve-service-provider/<provider_id>/", methods=["GET", "POST"])
def admin_approve_service_provider(provider_id):
    provider = db.service_providers.find_one({"_id": ObjectId(provider_id)})
    if not provider:
        return abort(404, "Service Provider Not Found")

    if request.method == "POST":
        values = {
            "status": ServiceProviderStatus.APPROVED.name,
            "commission": float(request.form.get("commission")),
            "remarks": "",
        }
        result = db.service_providers.update_one(
            {"_id": ObjectId(provider["_id"])}, {"$set": values}
        )
        if result.modified_count > 0:
            flash("Service Provider Verified Successfully", "success")
            return redirect(url_for("admin_view_service_providers"))

    return render_template("/admin/provider_update_commission.html", provider=provider)


# Admin reject service provider
@app.route("/admin/reject-service-provider/<provider_id>/", methods=["GET", "POST"])
def admin_reject_service_provider(provider_id):
    provider = db.service_providers.find_one({"_id": ObjectId(provider_id)})
    if not provider:
        return abort(404, "Host Not Found")

    if request.method == "POST":
        values = {
            "remarks": request.form.get("remarks"),
            "commission": float(0),
            "status": ServiceProviderStatus.REJECTED.name,
        }
        result = db.service_providers.update_one(
            {"_id": ObjectId(provider["_id"])}, {"$set": values}
        )

        if result.modified_count > 0:
            flash("Rejected Successfully", "success")
            return redirect(url_for("admin_view_service_providers"))
        else:
            flash("No changes made", "success")
            return redirect(url_for("admin_view_service_providers"))

    return render_template("/admin/reject_service_provider.html", provider=provider)


# admin update service provider commission
@app.route("/admin/provider-update-commission/<provider_id>/", methods=["GET", "POST"])
def admin_provider_update_commission(provider_id):
    provider = db.service_providers.find_one({"_id": ObjectId(provider_id)})
    if not provider:
        return abort(404, "Host Not Found")

    if request.method == "POST":
        values = {"commission": float(request.form.get("commission"))}
        result = db.service_providers.update_one(
            {"_id": ObjectId(provider["_id"])}, {"$set": values}
        )
        if result.modified_count > 0:
            flash("Service Provider Commisssion Updated Successfully", "success")
            return redirect(url_for("admin_view_service_providers"))
        else:
            flash("No changes in commission value", "success")
            return redirect(url_for("admin_view_service_providers"))

    return render_template("/admin/provider_update_commission.html", provider=provider)


# delete host
@app.route("/admin/host/delete/<host_id>/", methods=["GET"])
def admin_delete_host(host_id):
    host = db.hosts.find_one({"_id": ObjectId(host_id)})
    result = db.hosts.update_one(
        {"_id": ObjectId(host["_id"])}, {"$set": {"status": False}}
    )
    if result.modified_count > 0:
        properties = db.properties.find({"host_id": ObjectId(host["_id"])})
        if properties:
            for property in properties:
                db.properties.update_one(
                    {"_id": ObjectId(property["_id"])}, {"$set": {"status": False}}
                )
        flash("Host deleted successfully", "success")
    else:
        flash("Error Deleting Host", "danger")

    return redirect(url_for("admin_hosts"))


@app.route("/admin/properties/<host_id>/")
def admin_view_host_properties(host_id):
    properties = db.properties.aggregate(
        [
            {"$match": {"host_id": ObjectId(host_id), "status": True}},
            {
                "$lookup": {
                    "from": db.categories.name,
                    "localField": "category_id",
                    "foreignField": "_id",
                    "as": "category",
                }
            },
            {
                "$lookup": {
                    "from": db.countries.name,
                    "localField": "country_id",
                    "foreignField": "_id",
                    "as": "country",
                }
            },
        ]
    )
    properties = list(properties)
    list.reverse(properties)
    return render_template("/admin/properties.html", properties=properties)


@app.route("/admin/view-property/<property_id>/")
def admin_view_property(property_id):
    property = db.properties.aggregate(
        [
            {"$match": {"_id": ObjectId(property_id)}},
            {
                "$lookup": {
                    "from": db.categories.name,
                    "localField": "category_id",
                    "foreignField": "_id",
                    "as": "category",
                }
            },
            {
                "$lookup": {
                    "from": db.countries.name,
                    "localField": "country_id",
                    "foreignField": "_id",
                    "as": "country",
                }
            },
        ]
    )
    if not property:
        return abort(404, "Property Not Found")
    property = list(property)

    reviews = db.ratings.aggregate(
        [
            {"$match": {"property_id": ObjectId(property[0]["_id"])}},
            {
                "$lookup": {
                    "from": db.users.name,
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user",
                }
            },
        ]
    )
    reviews = list(reviews)
    list.reverse(reviews)
    return render_template(
        "/admin/property-details.html", property=property[0], reviews=reviews
    )


@app.route("/admin/bookings/<property_id>/")
def admin_view_host_bookings(property_id):
    bookings = db.bookings.aggregate(
        [
            {"$match": {"property_id": ObjectId(property_id)}},
            {
                "$lookup": {
                    "from": db.properties.name,
                    "localField": "property_id",
                    "foreignField": "_id",
                    "as": "property",
                }
            },
        ]
    )
    bookings = list(bookings)
    list.reverse(bookings)
    return render_template("/admin/bookings.html", bookings=bookings)


@app.route("/admin/booking-details/<booking_id>/")
def admin_host_booking_details(booking_id):
    bookings = db.bookings.aggregate(
        [
            {"$match": {"_id": ObjectId(booking_id)}},
            {
                "$lookup": {
                    "from": db.properties.name,
                    "localField": "property_id",
                    "foreignField": "_id",
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": db.countries.name,
                                "localField": "country_id",
                                "foreignField": "_id",
                                "as": "country",
                            }
                        }
                    ],
                    "as": "property",
                }
            },
            {
                "$lookup": {
                    "from": db.payments.name,
                    "localField": "_id",
                    "foreignField": "booking_id",
                    "as": "payment",
                }
            },
        ]
    )
    bookings = list(bookings)
    return render_template("/admin/booking-details.html", bookings=bookings[0])


# view transaction history
@app.route("/admin/transactions/")
def admin_commission():
    payments = db.payments.find({})
    payments = list(payments)
    list.reverse(payments)
    return render_template("/admin/transactions.html", payments=payments)


# service provider registration
@app.route("/service-provider-registration/", methods=["GET", "POST"])
def service_provider_registration():
    if request.method == "POST":
        values = {
            "fullname": request.form.get("fullname"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
            "address": request.form.get("address"),
            "about": request.form.get("about"),
            "password": request.form.get("password"),
            "commission": float(0),
            "remarks": "",
            "status": ServiceProviderStatus.PENDING.name,
        }

        db.service_providers.insert_one(values)
        flash(
            "you have registered successfully, admin will verify your registration shortly",
            "success",
        )
        return redirect(url_for("service_provider_login"))

    return render_template("service_provider_registration.html")


@app.route("/service-provider/")
@app.route("/service-provider-login/", methods=["GET", "POST"])
def service_provider_login():
    error_msg = ""
    if request.method == "POST":
        values = {
            "email": request.form.get("email"),
            "password": request.form.get("password"),
        }
        service_provider = db.service_providers.find_one(values)
        if service_provider:
            if service_provider["status"] == ServiceProviderStatus.DELETED.name:
                error_msg = "Login Disabled by admin"
                return render_template("/provider/login.html", error_msg=error_msg)

            session["logged_in"] = True
            session["provider_id"] = str(service_provider["_id"])
            session["fullname"] = service_provider["fullname"]
            session["role"] = "Provider"
            session["status"] = service_provider["status"]
            return redirect(url_for("service_provider_home"))
        else:
            error_msg = "Invalid Login Credentials"

    return render_template("/provider/login.html", error_msg=error_msg)


@app.route("/service-provider/home/")
def service_provider_home():
    provider_id = session["provider_id"]
    provider = db.service_providers.find_one({"_id": ObjectId(provider_id)})

    # properties = db.properties.find(
    #     {"host_id": ObjectId(session["host_id"]), "status": True}
    # )
    # property_count = db.properties.count_documents(
    #     {"host_id": ObjectId(session["host_id"]), "status": True}
    # )
    # bookings = 0
    # for property in properties:
    #     booking = db.bookings.count_documents(
    #         {"property_id": ObjectId(property["_id"])}
    #     )
    #     bookings = bookings + booking

    users = db.users.count_documents({"status": True})
    dashboard = {"properties": 0, "users": users, "bookings": 0}
    return render_template(
        "/provider/home.html", dashboard=dashboard, provider=provider
    )


@app.route("/service-provider/my-profile/", methods=["GET", "POST"])
def service_provider_profile():
    if request.method == "POST":
        host_id = ObjectId(session["host_id"])
        update_values = {
            "name": request.form.get("name"),
            "phone": request.form.get("phone"),
            "languages": request.form.get("languages"),
            "about": request.form.get("about"),
        }
        result = db.hosts.update_one({"_id": host_id}, {"$set": update_values})
        if result.modified_count > 0:
            flash("Profile Updated Successfully", "success")
            return redirect(url_for("host_profile"))

    profile = db.hosts.find_one({"_id": ObjectId(session["host_id"])})
    return render_template("/provider/profile.html", profile=profile)


# host change password
@app.route("/service-provider/change-password/", methods=["GET", "POST"])
def service_provider_change_password():
    if request.method == "POST":
        values = {
            "password": request.form.get("password"),
        }
        result = db.hosts.update_one(
            {"_id": ObjectId(session["host_id"])}, {"$set": values}
        )
        flash("Password Updated successfully", "success")
        return redirect(url_for("host_change_password"))

    return render_template("/host/change-password.html")


@app.route("/service-provider/services/")
def service_provider_services():
    provider_id = session["provider_id"]
    provider_services = db.service_provider_services.aggregate(
        [
            {"$match": {"provider_id": ObjectId(provider_id), "status": True}},
            {
                "$lookup": {
                    "from": db.services.name,
                    "localField": "service_id",
                    "foreignField": "_id",
                    "as": "service",
                }
            },
            {"$unwind": "$service"},
        ]
    )
    return render_template(
        "/provider/services.html", provider_services=provider_services
    )


@app.route("/service-provider/add-service/", methods=["GET", "POST"])
def service_provider_add_service():
    if request.method == "POST":
        provider_id = session["provider_id"]
        values = {
            "provider_id": ObjectId(provider_id),
            "service_id": ObjectId(request.form.get("service_id")),
            "price": float(request.form.get("price")),
            "duration": request.form.get("duration"),
            "description": request.form.get("description"),
            "time_slots": [],
            "status": True,
        }
        result = db.service_provider_services.insert_one(values)
        flash("Services Added Successfully, add time slot for this service", "success")
        return redirect(
            url_for("service_provider_service_time_slots", psid=result.inserted_id)
        )

    service_provider = ""
    services = db.services.find({"status": True})

    return render_template(
        "/provider/service_form.html",
        service_provider=service_provider,
        services=services,
    )


@app.route(
    "/service-provider/edit-service/<provider_service_id>/", methods=["GET", "POST"]
)
def service_provider_edit_service(provider_service_id):
    provider_id = session["provider_id"]

    if request.method == "POST":
        provider_service_id = request.form.get("provider_service_id")

        values = {
            "service_id": ObjectId(request.form.get("service_id")),
            "price": float(request.form.get("price")),
            "duration": request.form.get("duration"),
            "description": request.form.get("description"),
        }
        db.service_provider_services.update_one(
            {"_id": ObjectId(provider_service_id)}, {"$set": values}
        )

        flash("Service Updated Successfully", "success")
        return redirect(url_for("service_provider_services"))

    service_provider = db.service_provider_services.find_one(
        {"_id": ObjectId(provider_service_id), "provider_id": ObjectId(provider_id)}
    )
    if not service_provider:
        return abort(404, "Service provider Not Found")
    services = db.services.find({"status": True})

    return render_template(
        "/provider/service_form.html",
        service_provider=service_provider,
        services=services,
    )


# Service provider time slots
@app.route("/service-provider/service-time-slots")
def service_provider_service_time_slots():
    provider_service_id = request.args.get("psid")
    time_slot_id = request.args.get("time_slot_id")
    time_slot = ""

    # Edit Time SLot
    if time_slot_id:
        # edit
        provider_service = db.service_provider_services.aggregate(
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
                                "cond": {
                                    "$eq": ["$$time_slot.id", ObjectId(time_slot_id)]
                                },
                            }
                        }
                    }
                },
            ]
        )
        provider_service = list(provider_service)
        time_slot = provider_service[0]["time_slots"][0]

    provider_service = db.service_provider_services.aggregate(
        [
            {"$match": {"_id": ObjectId(provider_service_id), "status": True}},
            {
                "$lookup": {
                    "from": db.services.name,
                    "localField": "service_id",
                    "foreignField": "_id",
                    "as": "service",
                }
            },
            {"$unwind": "$service"},
        ]
    )
    provider_service = list(provider_service)
    if not provider_service:
        return abort(404, "Service provider service Not Found")

    return render_template(
        "/provider/time_slots.html",
        time_slot=time_slot,
        provider_service=provider_service[0],
    )


@app.route("/service-provider/service-time-slots", methods=["POST"])
def service_provider_service_time_slots_post():
    provider_service_id = request.form.get("provider_service_id")
    provider_service = db.service_provider_services.find_one(
        {"_id": ObjectId(provider_service_id), "status": True}
    )

    time_slot_id = request.form.get("time_slot_id")

    values = {
        "time_slot": request.form.get("time_slot"),
    }

    if time_slot_id:
        # update time slot
        values["id"] = ObjectId(time_slot_id)
        db.service_provider_services.update_one(
            {
                "_id": ObjectId(provider_service["_id"]),
                "time_slots.id": ObjectId(time_slot_id),
            },
            {"$set": {"time_slots.$": values}},
        )
        flash("Updated Successfully", "success")
    else:
        # add time slot
        values["id"] = ObjectId()
        db.service_provider_services.update_one(
            {"_id": ObjectId(provider_service["_id"])},
            {"$push": {"time_slots": values}},
        )
        flash("Added Successfully", "success")

    return redirect(
        url_for("service_provider_service_time_slots", psid=provider_service_id)
    )


# service provider - delete time slot
@app.route("/service-provider/service-time-slots/delete")
def service_provider_delete_timeslot():
    provider_service_id = request.args.get("psid")
    time_slot_id = request.args.get("time_slot_id")

    db.service_provider_services.update_one(
        {"_id": ObjectId(provider_service_id)},
        {"$pull": {"time_slots": {"id": ObjectId(time_slot_id)}}},
    )
    flash("Deleted Successfully", "success")
    return redirect(
        url_for("service_provider_service_time_slots", psid=provider_service_id)
    )


# service provider view appointments
@app.route("/service-provider/view-appointments/")
def service_provider_view_appointments():
    provider_id = session["provider_id"]
    appointments = db.appointments.aggregate(
        [
            {
                "$match": {
                    "provider_id": ObjectId(provider_id),
                    "status": {"$ne": AppointmentStatus.REJECTED.name},
                }
            },
            {
                "$lookup": {
                    "from": db.services.name,
                    "localField": "service_id",
                    "foreignField": "_id",
                    "as": "service",
                }
            },
            {"$unwind": "$service"},
            {
                "$lookup": {
                    "from": db.users.name,
                    "localField": "owner_id",
                    "foreignField": "_id",
                    "as": "owner",
                }
            },
            {"$unwind": "$owner"},
            {
                "$lookup": {
                    "from": db.pets.name,
                    "localField": "pet_id",
                    "foreignField": "_id",
                    "as": "pet",
                }
            },
            {"$unwind": "$pet"},
        ]
    )
    appointments = list(appointments)
    list.reverse(appointments)
    return render_template(
        "/provider/user_appointments.html",
        appointments=appointments,
        getTimeSlot=db.getTimeSlot,
    )


# default views
@app.route("/")
@app.route("/home/")
def index():
    categories = list(db.categories.find({"status": True}))
    countries = list(db.countries.find({"status": True}))
    latest_properties = db.properties.find({"status": True}).sort("_id", -1).limit(6)
    return render_template(
        "index.html",
        countries=countries,
        categories=categories,
        latest_properties=latest_properties,
        getCountry=db.getCountryById,
        ratings=db.getRatingsByPropertyId,
    )


@app.route("/user-registration/", methods=["GET", "POST"])
def user_registration():
    if request.method == "POST":
        values = {
            "fullname": request.form.get("fullname"),
            "email": request.form.get("email"),
            "contact_no": request.form.get("contact_no"),
            "password": request.form.get("password"),
            "status": True,
        }
        result = db.users.insert_one(values)
        user = db.users.find_one({"_id": ObjectId(result.inserted_id)})
        if result.inserted_id:
            session["logged_in"] = True
            session["user_id"] = str(user["_id"])
            session["fullname"] = user["fullname"]
            session["role"] = "User"
            flash("Registered successfully", "success")
            return redirect(url_for("user_home"))

    return render_template("/register.html")


@app.route("/user-login/", methods=["GET", "POST"])
def user_login():
    error_msg = ""
    if request.method == "POST":
        values = {
            "email": request.form.get("email"),
            "password": request.form.get("password"),
        }
        user = db.users.find_one(values)
        if user:
            session["logged_in"] = True
            session["user_id"] = str(user["_id"])
            session["fullname"] = user["fullname"]
            session["role"] = "User"

            return redirect(url_for("index"))
        else:
            error_msg = "Invalid Login Credentials"

    return render_template("/login.html", error_msg=error_msg)


# user home
@app.route("/user/home/", methods=["GET", "POST"])
def user_home():
    return render_template("/home.html")


# user pets
@app.route("/user/view-pets/")
def user_view_pets():
    owner_id = session["user_id"]
    pets = db.pets.find({"owner_id": ObjectId(owner_id), "status": True}).sort(
        "_id", -1
    )

    return render_template("/pets.html", pets=pets)


# user add pets
@app.route("/user/add-pet/", methods=["GET", "POST"])
def user_add_pets():
    owner_id = session["user_id"]
    if request.method == "POST":
        image = request.files.get("pet_image")
        values = {
            "owner_id": ObjectId(owner_id),
            "name": request.form.get("name").title(),
            "species": request.form.get("species").title(),
            "breed": request.form.get("breed").title(),
            "age": request.form.get("age"),
            "sex": request.form.get("sex"),
            "image_file_name": image.filename,
            "status": True,
        }

        db.pets.insert_one(values)
        image.save(APP_ROOT + "/images/pets/" + image.filename)
        flash("Pet added successfully", "sucsess")
        return redirect(url_for("user_view_pets"))

    return render_template("/pet_form.html", pet="", str=str)


# user edit pets
@app.route("/user/edit-pet/", methods=["GET", "POST"])
def user_edit_pets():
    owner_id = session["user_id"]
    pet_id = request.args.get("pet_id")

    if request.method == "POST":
        pet_id = request.form.get("pet_id")
        image = request.files.get("pet_image")
        image_file_name = request.form.get("image_file_name")
        if image.filename != "":
            image_file_name = image.filename

        values = {
            "name": request.form.get("name").title(),
            "species": request.form.get("species").title(),
            "breed": request.form.get("breed").title(),
            "age": request.form.get("age"),
            "sex": request.form.get("sex"),
            "image_file_name": image_file_name,
        }

        result = db.pets.update_one({"_id": ObjectId(pet_id)}, {"$set": values})
        if image.filename != "":
            image.save(APP_ROOT + "/images/pets/" + image.filename)

        flash("Pet updated successfully", "success")
        return redirect(url_for("user_view_pets"))

    pet = db.pets.find_one({"_id": ObjectId(pet_id), "owner_id": ObjectId(owner_id)})
    if not pet:
        return abort(404, "Sorry, Pet not found")

    return render_template("/pet_form.html", pet=pet, str=str)


# user delete pet
@app.route("/user/delete-pet/", methods=["GET", "POST"])
def user_delete_pets():
    owner_id = session["user_id"]
    pet_id = request.args.get("pet_id")

    pet = db.pets.find_one({"_id": ObjectId(pet_id), "owner_id": ObjectId(owner_id)})
    if not pet:
        return abort(404, "Sorry, Pet not found")

    db.pets.update_one({"_id": ObjectId(pet_id)}, {"$set": {"status": False}})


# user view all services
@app.route("/user/view-services/", methods=["GET", "POST"])
def user_view_services():
    services = db.services.find({"status": True})
    return render_template(
        "/services.html",
        services=services,
        getProviderCountByServiceId=db.getProviderCountByServiceId,
    )


# user view service provider services list
@app.route("/user/view-provider-service/")
def user_view_provider_services():
    service_id = request.args.get("service_id")
    service = db.services.find_one({"_id": ObjectId(service_id)})
    if not service:
        return abort(404, "Service not found")

    provider_services = db.service_provider_services.find(
        {"service_id": ObjectId(service_id), "status": True}
    )

    provider_services = db.service_provider_services.aggregate(
        [
            {"$match": {"service_id": ObjectId(service_id), "status": True}},
            {
                "$lookup": {
                    "from": db.service_providers.name,
                    "localField": "provider_id",
                    "foreignField": "_id",
                    "as": "service_provider",
                }
            },
            {"$unwind": "$service_provider"},
        ]
    )
    provider_services = list(provider_services)
    return render_template(
        "/provider_services.html",
        provider_services=provider_services,
        service=service,
    )


# user view service provider service details
@app.route("/user/view-provider-service-details/")
def user_view_provider_service_details():
    provider_service_id = request.args.get("id")

    provider_service = db.service_provider_services.aggregate(
        [
            {"$match": {"_id": ObjectId(provider_service_id), "status": True}},
            {
                "$lookup": {
                    "from": db.service_providers.name,
                    "localField": "provider_id",
                    "foreignField": "_id",
                    "as": "service_provider",
                }
            },
            {"$unwind": "$service_provider"},
            {
                "$lookup": {
                    "from": db.services.name,
                    "localField": "service_id",
                    "foreignField": "_id",
                    "as": "service",
                }
            },
            {"$unwind": "$service"},
        ]
    )

    if not provider_service:
        return abort(404, "Provider service not found")

    provider_service = list(provider_service)

    return render_template(
        "/provider_services_details.html",
        provider_service=provider_service[0],
    )


# user schedule appointment
@app.route("/user/schedule-now/")
def user_schedule_appointment():
    provider_service_id = request.args.get("psid")
    provider_service = db.service_provider_services.aggregate(
        [
            {"$match": {"_id": ObjectId(provider_service_id), "status": True}},
            {
                "$lookup": {
                    "from": db.service_providers.name,
                    "localField": "provider_id",
                    "foreignField": "_id",
                    "as": "service_provider",
                }
            },
            {"$unwind": "$service_provider"},
            {
                "$lookup": {
                    "from": db.services.name,
                    "localField": "service_id",
                    "foreignField": "_id",
                    "as": "service",
                }
            },
            {"$unwind": "$service"},
        ]
    )
    provider_service = list(provider_service)
    owner_id = session["user_id"]
    pets = db.pets.find({"owner_id": ObjectId(owner_id), "status": True})
    return render_template(
        "schedule_appointment_form.html",
        provider_service=provider_service[0],
        pets=pets,
    )


# user schedule appointment post
@app.route("/user/schedule-now/", methods=["POST"])
def user_schedule_appointment_post():
    provider_service_id = request.form.get("provider_service_id")
    appointment_date = request.form.get("appointment_date")
    time_slot_id = request.form.get("time_slot_id")

    if not time_slot_id:
        time_slot_id = ""
    else:
        time_slot_id = ObjectId(time_slot_id)

    isScheduled = db.appointments.find_one(
        {
            "provider_service_id": ObjectId(provider_service_id),
            "appointment_date": appointment_date,
            "time_slot_id": time_slot_id,
            "status": {
                "$nin": [
                    AppointmentStatus.REJECTED.name,
                    AppointmentStatus.CANCELLED.name,
                ]
            },
        }
    )

    if isScheduled:
        flash(
            "Sorry, already appointment scheduled in this time slot, please select another slot",
            "success",
        )
        return redirect(url_for("user_schedule_appointment", psid=provider_service_id))

    values = {
        "provider_service_id": ObjectId(provider_service_id),
        "service_id": ObjectId(request.form.get("service_id")),
        "provider_id": ObjectId(request.form.get("provider_id")),
        "owner_id": ObjectId(session["user_id"]),
        "pet_id": ObjectId(request.form.get("pet_id")),
        "appointment_date": appointment_date,
        "time_slot_id": time_slot_id,
        "notes": "",
        "status": AppointmentStatus.PENDING.name,
    }
    db.appointments.insert_one(values)
    flash("Appointment requested, on approval make payment and schedule service")
    return redirect(url_for("user_view_appointments"))


# user view appointments
@app.route("/user/view-appointments/")
def user_view_appointments():
    user_id = session["user_id"]

    appointments = db.appointments.aggregate(
        [
            {
                "$match": {
                    "owner_id": ObjectId(user_id),
                    "status": {"$ne": AppointmentStatus.REJECTED.name},
                }
            },
            {
                "$lookup": {
                    "from": db.services.name,
                    "localField": "service_id",
                    "foreignField": "_id",
                    "as": "service",
                }
            },
            {"$unwind": "$service"},
            {
                "$lookup": {
                    "from": db.service_providers.name,
                    "localField": "provider_id",
                    "foreignField": "_id",
                    "as": "provider",
                }
            },
            {"$unwind": "$provider"},
            {
                "$lookup": {
                    "from": db.pets.name,
                    "localField": "pet_id",
                    "foreignField": "_id",
                    "as": "pet",
                }
            },
            {"$unwind": "$pet"},
        ]
    )
    appointments = list(appointments)
    list.reverse(appointments)
    return render_template(
        "user_appointments.html", appointments=appointments, getTimeSlot=db.getTimeSlot
    )


@app.route("/my-profile/", methods=["GET", "POST"])
def user_profile():
    if request.method == "POST":
        values = {
            "fullname": request.form.get("fullname"),
            "contact_no": request.form.get("contact_no"),
        }
        result = db.users.update_one(
            {"_id": ObjectId(session["user_id"])}, {"$set": values}
        )
        flash("Profile Updated successfully", "success")
        return redirect(url_for("user_profile"))

    user = db.users.find_one({"_id": ObjectId(session["user_id"])})
    return render_template("/profile.html", user=user)


@app.route("/change-password/", methods=["GET", "POST"])
def user_change_password():
    if request.method == "POST":
        values = {
            "password": request.form.get("password"),
        }
        result = db.users.update_one(
            {"_id": ObjectId(session["user_id"])}, {"$set": values}
        )
        flash("Password Updated successfully", "success")
        return redirect(url_for("user_change_password"))

    return render_template("/change-password.html")


@app.route("/property-details/<property_id>/")
def property_details(property_id):
    property = db.properties.aggregate(
        [
            {"$match": {"_id": ObjectId(property_id)}},
            {
                "$lookup": {
                    "from": db.categories.name,
                    "localField": "category_id",
                    "foreignField": "_id",
                    "as": "category",
                }
            },
            {
                "$lookup": {
                    "from": db.countries.name,
                    "localField": "country_id",
                    "foreignField": "_id",
                    "as": "country",
                }
            },
            {
                "$lookup": {
                    "from": db.hosts.name,
                    "localField": "host_id",
                    "foreignField": "_id",
                    "as": "host",
                }
            },
        ]
    )
    if not property:
        return abort(404, "Property Not Found")
    property = list(property)
    tomorrow = datetime.now() + timedelta(1)
    tomorrow = tomorrow.strftime("%Y-%m-%d")
    ratings = db.getRatingsByPropertyId(property[0]["_id"])
    # reviews = db.ratings.find({"property_id":ObjectId(property[0]["_id"])})

    reviews = db.ratings.aggregate(
        [
            {"$match": {"property_id": ObjectId(property[0]["_id"])}},
            {
                "$lookup": {
                    "from": db.users.name,
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user",
                }
            },
        ]
    )
    reviews = list(reviews)
    list.reverse(reviews)
    return render_template(
        "/property_details.html",
        property=property[0],
        tomorrow=tomorrow,
        ratings=ratings,
        reviews=reviews,
    )


# search or filter properties based on conditions
@app.route("/search/")
def search_properties():
    category_id = request.args.get("category")
    country_id = request.args.get("country")

    if country_id == "" and category_id == "":
        query = {}
    if country_id != "" and category_id == "":
        query = {"country_id": ObjectId(country_id)}
    if country_id == "" and category_id != "":
        query = {"category_id": ObjectId(category_id)}
    if country_id != "" and category_id != "":
        query = {
            "country_id": ObjectId(country_id),
            "category_id": ObjectId(category_id),
        }
    query["status"] = True

    properties = db.properties.find(query)
    properties = list(properties)

    categories = list(db.categories.find({"status": True}))
    countries = list(db.countries.find({"status": True}))

    return render_template(
        "/search_properties.html",
        str=str,
        categories=categories,
        countries=countries,
        properties=properties,
        getCountry=db.getCountryById,
        ratings=db.getRatingsByPropertyId,
    )


def isPropertyReserved(check_in, check_out, propertyId):
    check_in = datetime.strptime(check_in, "%Y-%m-%d")
    check_out = datetime.strptime(check_out, "%Y-%m-%d")
    query = {"property_id": ObjectId(propertyId), "is_cancelled": False}
    print(type(check_in))
    print(query)
    Bookings = db.bookings.find(query)
    for Booking in Bookings:
        print("inside")
        booked_check_in = Booking["check_in"]
        booked_check_out = Booking["check_out"]
        if check_in >= booked_check_in and check_in <= booked_check_out:
            return True
        elif check_out >= booked_check_in and check_out <= booked_check_out:
            return True
        elif check_in < booked_check_in and check_out > booked_check_out:
            return True
        print(check_in >= booked_check_in)
    return False


@app.route("/check-availability/", methods=["POST"])
def user_check_property_availability():
    prop_id = request.form.get("property_id")
    check_in = request.form.get("check_in")
    check_out = request.form.get("check_out")

    if isPropertyReserved(check_in, check_out, prop_id):
        return render_template(
            "/confirm-booking.html", isReserved=True, booking_values=""
        )
    else:
        property = db.properties.find_one({"_id": ObjectId(prop_id)})
        rate_per_night = float(property["rate_per_night"])
        total_nights = int(request.form.get("nights_count"))
        property_amount = rate_per_night * total_nights
        service_amount = round(
            property_amount * (float(property["service_charge"]) / 100), 2
        )
        total_amount = property_amount + service_amount

        booking_values = {
            "property": property,
            "guest_count": request.form.get("guests"),
            "check_in": check_in,
            "check_out": check_out,
            "total_nights": total_nights,
            "property_amount": property_amount,
            "service_amount": service_amount,
            "total_amount": total_amount,
        }
        return render_template(
            "/confirm-booking.html", isReserved=False, booking_values=booking_values
        )


@app.route("/book/", methods=["POST"])
def user_property_booking():
    property_id = request.form.get("property_id")
    property = db.properties.find_one({"_id": ObjectId(property_id)})

    values = {
        "user_id": ObjectId(session["user_id"]),
        "property_id": ObjectId(property_id),
        "booked_on": datetime.now(),
        "check_in": datetime.strptime(request.form.get("check_in"), "%Y-%m-%d"),
        "check_out": datetime.strptime(request.form.get("check_out"), "%Y-%m-%d"),
        "total_guest": int(request.form.get("total_guest")),
        "rate_per_night": float(request.form.get("rate_per_night")),
        "total_nights": int(request.form.get("total_nights")),
        "bill_amount": round(float(request.form.get("total_amount")), 2),
        "is_checked_in": False,
        "is_checked_out": False,
        "is_cancelled": False,
    }
    result = db.bookings.insert_one(values)
    booking_id = result.inserted_id

    bookings = db.bookings.find_one({"_id": ObjectId(booking_id)})
    host = db.hosts.find_one({"_id": ObjectId(property["host_id"])})
    commission_amount = float(bookings["bill_amount"]) * (
        float(host["commission_percentage"]) / 100
    )
    host_amount = float(bookings["bill_amount"]) - commission_amount

    card_values = {
        "card_holder": request.form.get("card_holder"),
        "card_number": request.form.get("card_number"),
        "expiry_month": int(request.form.get("expiry_month")),
        "expiry_year": int(request.form.get("expiry_year")),
        "cvv": int(request.form.get("cvv")),
    }
    payment_values = {
        "booking_id": ObjectId(booking_id),
        "host_id": ObjectId(host["_id"]),
        "payment_date": datetime.now(),
        "base_amount": round(float(request.form.get("property_amount")), 2),
        "service_charge": round(float(request.form.get("service_charge")), 2),
        "service_amount": round(float(request.form.get("service_amount")), 2),
        "bill_amount": round(float(bookings["bill_amount"]), 2),
        "commission_percentage": round(float(host["commission_percentage"]), 2),
        "commission_amount": round(float(commission_amount), 2),
        "host_amount": round(host_amount, 2),
        "card_details": card_values,
        "is_cancelled": False,
        "remarks": "Property Booking",
    }

    result = db.payments.insert_one(payment_values)
    return redirect(url_for("user_bookings"))


@app.route("/bookings/")
def user_bookings():
    bookings = db.bookings.aggregate(
        [
            {"$match": {"user_id": ObjectId(session["user_id"])}},
            {
                "$lookup": {
                    "from": db.properties.name,
                    "localField": "property_id",
                    "foreignField": "_id",
                    "as": "property",
                }
            },
        ]
    )
    bookings = list(bookings)
    list.reverse(bookings)
    return render_template("/bookings.html", bookings=bookings)


@app.route("/booking-details/<booking_id>/")
def user_booking_details(booking_id):
    bookings = db.bookings.aggregate(
        [
            {"$match": {"_id": ObjectId(booking_id)}},
            {
                "$lookup": {
                    "from": db.properties.name,
                    "localField": "property_id",
                    "foreignField": "_id",
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": db.countries.name,
                                "localField": "country_id",
                                "foreignField": "_id",
                                "as": "country",
                            }
                        }
                    ],
                    "as": "property",
                }
            },
            {
                "$lookup": {
                    "from": db.payments.name,
                    "localField": "_id",
                    "foreignField": "booking_id",
                    "as": "payment",
                }
            },
        ]
    )
    bookings = list(bookings)
    property_id = bookings[0]["property"][0]["_id"]

    rating = db.ratings.find_one(
        {"user_id": ObjectId(session["user_id"]), "property_id": ObjectId(property_id)}
    )
    return render_template("/booking-details.html", bookings=bookings[0], rating=rating)


@app.route("/cancel-booking/<bid>/")
def user_cancel_booking(bid):
    bookings = db.bookings.find_one({"_id": ObjectId(bid)})
    property = db.properties.find_one({"_id": ObjectId(bookings["property_id"])})

    result = db.bookings.update_one(
        {"_id": ObjectId(bookings["_id"])}, {"$set": {"is_cancelled": True}}
    )

    if result.modified_count > 0:
        cancellation_charge = round(float(property["cancellation_charge"]), 2)
        cancellation_amount = round(
            float(bookings["bill_amount"]) * (cancellation_charge / 100), 2
        )
        refund_amount = round(float(bookings["bill_amount"]) - cancellation_amount, 2)
        values = {
            "commission_percentage": 0,
            "commission_amount": 0,
            "cancellation_charge": cancellation_charge,
            "cancellation_amount": cancellation_amount,
            "refund_amount": refund_amount,
            "host_amount": cancellation_amount,
            "is_cancelled": True,
            "remarks": "Booking Cancelled",
        }
        db.payments.update_one(
            {"booking_id": ObjectId(bookings["_id"])}, {"$set": values}
        )
        flash("Booking cancelled successfully", "success")
    else:
        flash("Unable to cancel your booking now", "danger")
    return redirect(url_for("user_bookings"))


@app.route("/check-out/<booking_id>/")
def user_checkout(booking_id):
    bookings = db.bookings.find_one({"_id": ObjectId(booking_id)})
    db.bookings.update_one(
        {"_id": ObjectId(bookings["_id"])}, {"$set": {"is_checked_out": True}}
    )
    flash("User checked-out successfully", "success")
    return redirect(url_for("user_bookings"))


@app.route("/extend-booking/<booking_id>/", methods=["GET", "POST"])
def user_extend_booking(booking_id):
    booking = db.bookings.find_one({"_id": ObjectId(booking_id)})
    if request.method == "POST":
        next_day_to_old_check_out = request.form.get("next_day_to_old_check_out")
        new_check_out = request.form.get("new_check_out")
        old_check_out = request.form.get("old_check_out")
        # exten_check_out = datetime.strptime(request.form.get("ex_date"), '%Y-%m-%d')
        if isPropertyReserved(
            next_day_to_old_check_out, new_check_out, booking["property_id"]
        ):
            return render_template(
                "/confirm-extend-booking.html", isReserved=True, booking_values=""
            )
        else:
            property = db.properties.find_one({"_id": ObjectId(booking["property_id"])})
            start_date = datetime.strptime(
                request.form.get("old_check_out"), "%Y-%m-%d"
            )
            end_date = datetime.strptime(request.form.get("new_check_out"), "%Y-%m-%d")
            total_nights = end_date - start_date
            total_nights = total_nights.days
            rate_per_night = float(property["rate_per_night"])
            base_amount = rate_per_night * total_nights
            service_amount = round(
                base_amount * (float(property["service_charge"]) / 100), 2
            )
            total_amount = base_amount + service_amount

            booking_values = {
                "booking": booking,
                "property": property,
                "old_check_out": old_check_out,
                "new_check_out": new_check_out,
                "total_nights": total_nights,
                "base_amount": base_amount,
                "service_amount": service_amount,
                "total_amount": total_amount,
            }
            return render_template(
                "/confirm-extend-booking.html",
                isReserved=False,
                booking_values=booking_values,
            )

    actual_checkout_date = booking["check_out"].strftime("%Y-%m-%d")
    extend_start_date = booking["check_out"] + timedelta(1)
    extend_start_date = extend_start_date.strftime("%Y-%m-%d")
    return render_template(
        "/extend-booking.html",
        actual_checkout_date=actual_checkout_date,
        extend_start_date=extend_start_date,
        booking_id=booking["_id"],
    )


@app.route("/extended-book/", methods=["POST"])
def user_property_exten_booking():
    booking_id = request.form.get("booking_id")
    booking = db.bookings.find_one({"_id": ObjectId(booking_id)})

    total_nights = int(booking["total_nights"]) + int(
        request.form.get("extended_nights")
    )
    bill_amount = float(booking["bill_amount"]) + float(
        request.form.get("total_amount")
    )

    values = {
        "extended_on": datetime.now(),
        "check_out": datetime.strptime(request.form.get("new_check_out"), "%Y-%m-%d"),
        "rate_per_night": float(request.form.get("rate_per_night")),
        "total_nights": total_nights,
        "bill_amount": round(bill_amount, 2),
    }

    result = db.bookings.update_one({"_id": ObjectId(booking["_id"])}, {"$set": values})

    payment = db.payments.find_one({"booking_id": ObjectId(booking_id)})

    base_amount = float(payment["base_amount"]) + float(request.form.get("base_amount"))
    service_amount = float(payment["service_amount"]) + float(
        request.form.get("service_amount")
    )
    commission_amount = float(bill_amount) * (
        float(payment["commission_percentage"]) / 100
    )
    host_amount = float(bill_amount) - commission_amount

    payment_values = {
        "base_amount": round(base_amount, 2),
        "service_amount": round(service_amount, 2),
        "bill_amount": round(bill_amount, 2),
        "commission_amount": round(commission_amount, 2),
        "host_amount": round(host_amount, 2),
        "remarks": "Booking Extended",
    }

    result = db.payments.update_one(
        {"_id": ObjectId(payment["_id"])}, {"$set": payment_values}
    )
    flash("Booking extension confirmed", "success")
    return redirect(url_for("user_bookings"))


@app.route("/rating/", methods=["POST"])
def user_post_rating():
    property_id = request.form.get("property_id")
    booking_id = request.form.get("booking_id")
    values = {
        "property_id": ObjectId(property_id),
        "user_id": ObjectId(session["user_id"]),
        "rating": int(request.form.get("rating")),
        "review": request.form.get("review"),
    }
    db.ratings.insert_one(values)
    flash("Ratings posted successfully", "success")
    return redirect(url_for("user_booking_details", booking_id=booking_id))


@app.route("/is-user-email-exist")
def check_user_email_registerd():
    email = request.args.get("email")
    user = db.users.find_one({"email": email})
    if user:
        return jsonify(False)
    else:
        return jsonify(True)


@app.route("/is-provider-email-exist")
def check_provider_email_registerd():
    email = request.args.get("email")
    provider = db.service_providers.find_one({"email": email})
    if provider:
        return jsonify(False)
    else:
        return jsonify(True)


@app.route("/is-user-phone-exist")
def check_user_phone_registerd():
    contact_no = request.args.get("contact_no")
    user = db.users.find_one({"contact_no": contact_no})
    if user:
        return jsonify(False)
    else:
        return jsonify(True)


@app.route("/is-host-phone-exist")
def check_host_phone_registerd():
    phone = request.args.get("phone")
    host = db.hosts.find_one({"phone": phone})
    if host:
        return jsonify(False)
    else:
        return jsonify(True)


@app.route("/logout/")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
