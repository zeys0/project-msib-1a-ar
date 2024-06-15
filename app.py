import os
import jwt
import hashlib
from pymongo import MongoClient, DESCENDING
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
TOKEN_KEY = os.environ.get("TOKEN_KEY")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
app.secret_key = SECRET_KEY


@app.route("/")
def hello():
    return render_template("main/home.html")


@app.route("/admin")
def adminHome():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"username": payload.get("id")})
        total_produk = db.products.count_documents({})
        return render_template(
            "dashboard/HomeDash.html", total_produk=total_produk, user_info=user_info
        )
    except jwt.ExpiredSignatureError:
        msg = "Your token has expired"
        return redirect(url_for("login"), msg=msg)
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login"))


@app.route("/admin/kelolaproduk")
def kelolaProduk():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"username": payload.get("id")})
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
            "dashboard/kelolaproduk.html",
            produk_coll=produk_on_page,
            pagination=pagination,
            user_info=user_info,
        )
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))
    # Pagination
    # page = request.args.get("page", 1, type=int)
    # per_page = request.args.get("per_page", 3, type=int)
    # offset = (page - 1) * per_page
    # produk_on_page = list(db.products.find().skip(offset).limit(per_page))
    # pagination = Pagination(
    #     page=page,
    #     per_page=per_page,
    #     total=db.products.count_documents({}),
    #     show_single_page=False,
    #     alignment="end",
    # )

    # return render_template(
    #     "dashboard/kelolaProduk.html",
    #     produk_coll=produk_on_page,
    #     pagination=pagination,
    # )


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
    # token_receive = request.cookies.get("mytoken")
    # try:
    #     payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
    #     username = payload["id"]
    username_receive = request.form["username_give"]
    nama_receive = request.form["nama_give"]
    noHp_receive = request.form["noHp_give"]
    email_receive = request.form["email_give"]
    new_doc = {
        "profile_username": username_receive,
        "profile_nama": nama_receive,
        "profile_noHp": noHp_receive,
        "profile_email": email_receive,
    }
    if "file_give" in request.files:
        file = request.files["file_give"]
        filename = secure_filename(file.filename)
        extension = filename.split(".")[-1]
        file_path = f"profile_pics/{username_receive}.{extension}"
        file.save("./static/" + file_path)
        new_doc["profile_pic"] = filename
        new_doc["profile_pic_real"] = file_path
    db.users.insert_one(new_doc)  # ganti update kalo login udah
    return jsonify({"result": "success", "msg": "Profile updated!"})


# except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#     return redirect(url_for("home"))


@app.route("/kelolapesanan")
def kelolaPesanan():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 5, type=int)
    offset = (page - 1) * per_page
    pesanan_on_page = list(db.orders.find().skip(offset).limit(per_page))

    pagination = Pagination(
        page=page,
        per_page=per_page,
        total=db.orders.count_documents({}),
        show_single_page=False,
        alignment="end",
    )

    return render_template(
        "dashboard/kelolaPesanan.html",
        pesanan_coll=pesanan_on_page,
        pagination=pagination,
    )


@app.route("/detailpesanan/<id>")
def detailPesanan(id):
    pesanan = db.orders.find_one({"_id": ObjectId(id)})
    if not pesanan:
        flash("Pesanan tidak ditemukan.")
        return redirect(url_for("kelolaPesanan"))

    return render_template("dashboard/detailPesanan.html", pesanan=pesanan)


@app.route("/order")
def order():
    return render_template("main/order.html")


@app.route("/pesanan")
def pesanan():
    pesanan_collet = list(db.pesanan.find().sort("_id", DESCENDING))
    return render_template("main/pesanan.html", pesanan_collet=pesanan_collet)


@app.route("/produk")
def produk():
    pesanan_collet = list(db.pesanan.find().sort("_id", DESCENDING))
    return render_template("main/produk.html", pesanan_collet=pesanan_collet)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login/login.html")

    else:
        username_receive = request.form["username_give"]
        password_receive = request.form["password_give"]
        # password_hash = hashlib.sha3_256(password_receive.encode("utf-8")).hexdigest()
        result = db.users.find_one(
            {
                "username": username_receive,
                "password": password_receive,
            }
        )

        if result:
            role = result.get("role", "user")
            payload = {
                "id": username_receive,
                "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

            return jsonify({"result": "success", "token": token, "role": role})

        else:
            return jsonify(
                {
                    "result": "fail",
                    "msg": "We could not find a user with that id/password combination",
                }
            )
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Here, add logic to handle the new user registration
        return redirect(url_for('home'))
    return render_template('signup.html')

@app.route('/')
def home():
    featured_products = db['products'].find()
    tips = db['tips'].find()
    return render_template('home.html', featured_products=featured_products, tips=tips)



def seed_database():
    client = MongoClient('mongodb+srv://test:sparta@cluster0.2m7qwhx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
    db = client['wedding_box_rental']

    # Hapus koleksi jika sudah ada sebelumnya
    db['products'].drop()
    db['tips'].drop()

    # Data produk sampel
    products = [
        {"name": "Floral Fantasy", "description": "Beautiful floral arrangement", "price": 99},
        {"name": "Modern Elegance", "description": "Chic table setting", "price": 79},
        {"name": "Love Story", "description": "Romantic decor set", "price": 129},
    ]

    # Data tips sampel
    tips = [
        {"title": "Choosing the Right Venue", "description": "Tips on selecting the perfect venue."},
        {"title": "Floral Arrangement Ideas", "description": "Explore trending floral arrangements."},
    ]

    # Masukkan data ke dalam koleksi
    db['products'].insert_many(products)
    db['tips'].insert_many(tips)
    print("Database has been seeded!")


if __name__ == "__main__":
    seed_database()
if __name__ == "__main__":
    app.run("0.0.0.0", port=8000, debug=True)
