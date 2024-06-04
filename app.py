import os
import jwt
from pymongo import MongoClient
from os.path import join, dirname
from dotenv import load_dotenv
from flask_paginate import Pagination
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from bson import ObjectId
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")
SECRET_KEY = os.environ.get("SECRET_KEY")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
app.secret_key = SECRET_KEY


@app.route("/")
def hello():
    return render_template("main/home.html")


@app.route("/admin")
def adminHome():
    total_produk = db.products.count_documents({})
    return render_template("dashboard/HomeDash.html", total_produk=total_produk)


@app.route("/kelolaproduk")
def kelolaProduk():
    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 3, type=int)
    offset = (page - 1) * per_page
    produk_on_page = list(db.products.find().skip(offset).limit(per_page))
    pagination = Pagination(
        page=page,
        per_page=per_page,
        total=db.products.count_documents({}),
        show_single_page=False,
        alignment="end",
    )

    return render_template(
        "dashboard/kelolaProduk.html",
        produk_coll=produk_on_page,
        pagination=pagination,
    )


@app.route("/kelolaproduk/add", methods=["POST"])
def addDatasProduk():
    name = request.form.get("name")
    description = request.form.get("description")
    price = int(request.form.get("price"))
    image = request.files["images"]

    if image:
        save_to = "static/uploads"
        if not os.path.exists(save_to):
            os.makedirs(save_to)

        ext = image.filename.split(".")[-1]
        file_name = f"img-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.{ext}"
        image.save(f"{save_to}/{file_name}")

    db.products.insert_one(
        {
            "name": name,
            "price": price,
            "description": description,
            "image": file_name,
        }
    )
    flash("Data berhasil ditambah")
    return redirect(url_for("kelolaProduk"))


@app.route("/kelolaproduk/edit/<id>", methods=["POST"])
def editDatasProduk(id):

    name = request.form.get("name")
    price = int(request.form.get("price"))
    description = request.form.get("description")
    image = request.files["images"]

    if image:
        save_to = "static/uploads"
        produk = db.products.find_one({"_id": ObjectId(id)})
        target = f"static/uploads/{produk['image']}"

        if os.path.exists(target):
            os.remove(target)

        ext = image.filename.split(".")[-1]
        file_name = f"img-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.{ext}"
        image.save(f"{save_to}/{file_name}")

        db.products.update_one({"_id": ObjectId(id)}, {"$set": {"image": file_name}})

    db.products.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "name": name,
                "price": price,
                "description": description,
            }
        },
    )

    flash("Berhasil mengubah data buah")
    return redirect(url_for("kelolaProduk"))


@app.route("/kelolaproduk/delete/<id>", methods=["POST"])
def deleteDatasProduk(id):
    produk = db.products.find_one({"_id": ObjectId(id)})
    target = f"static/uploads/{produk['image']}"

    if os.path.exists(target):
        os.remove(target)

    db.products.delete_one({"_id": ObjectId(id)})
    flash("Data berhasil dihapus")
    return redirect(url_for("kelolaProduk"))

@app.route("/about")
def about():
    return render_template("main/about.html")

@app.route("/profile")
def profile():
    return render_template("main/profile.html")

@app.route("/update_profile", methods=["POST"])
def save_img():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        username = payload["id"]
        name_receive = request.form["name_give"]
        about_receive = request.form["about_give"]
        new_doc = {"profile_name": name_receive, "profile_info": about_receive}
        if "file_give" in request.files:
            file = request.files["file_give"]
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f"profile_pics/{username}.{extension}"
            file.save("./static/" + file_path)
            new_doc["profile_pic"] = filename
            new_doc["profile_pic_real"] = file_path
        db.users.update_one({"username": payload["id"]}, {"$set": new_doc})

        return jsonify({ "result": "success", "msg": "Profile updated!" })
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route("/order")
def order():
    return render_template("main/order.html")

@app.route("/kelolapesanan")
def kelolaPesanan():
    return render_template("dashboard/kelolaPesanan.html")

@app.route("/kelolapesanan/detail")
def detail_pesanan():
    return render_template("dashboard/detailPesanan.html")

if __name__ == "__main__":
    app.run("0.0.0.0", port=8000, debug=True)
