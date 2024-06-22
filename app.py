import os
import jwt
import hashlib
from pymongo import MongoClient, DESCENDING
from os.path import join, dirname
from dotenv import load_dotenv
from flask_paginate import Pagination
from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
    flash,
)
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
TOKEN_USER = os.environ.get("TOKEN_USER")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
app.secret_key = SECRET_KEY


@app.route("/")
def hello():
    return render_template("main/home.html")


@app.route("/home")
def home():
    token_receive = request.cookies.get(TOKEN_USER)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        logged_in = payload["id"]
        user_info = db.users.find_one({"username": payload.get("id")})
        return render_template(
            "main/home.html", user_info=user_info, logged_in=logged_in
        )
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/admin")
def adminHome():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"username": payload.get("id")})
        user_count = db.users.count_documents({"role": "user"})
        total_produk = db.products.count_documents({})
        total_pesanan = db.pesanan.count_documents({})
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 5, type=int)
        offset = (page - 1) * per_page
        pesanan_on_page = list(
            db.pesanan.find().skip(offset).limit(per_page).sort("_id", DESCENDING)
        )
        pagination = Pagination(
            page=page,
            per_page=per_page,
            total=db.pesanan.count_documents({}),
            alignment="end",
            show_single_page=False,
        )
        return render_template(
            "dashboard/HomeDash.html",
            total_produk=total_produk,
            total_pesanan=total_pesanan,
            user_info=user_info,
            user_count=user_count,
            pesanan=pesanan_on_page,
            pagination=pagination,
        )
    except jwt.ExpiredSignatureError:
        msg = "Your token has expired"
        return redirect(url_for("login"), msg=msg)
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login"))


@app.route("/admin/datauser")
def datauser():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"username": payload.get("id")})
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 5, type=int)
        offset = (page - 1) * per_page
        user_on_page = list(
            db.users.find({"role": "user"})
            .skip(offset)
            .limit(per_page)
            .sort("_id", DESCENDING)
        )
        pagination = Pagination(
            page=page,
            per_page=per_page,
            total=db.users.count_documents({}),
            alignment="end",
            show_single_page=False,
        )

        return render_template(
            "dashboard/datauser.html",
            user_info=user_info,
            user=user_on_page,
            pagination=pagination,
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


@app.route("/home/about")
def aboutLogin():
    token_receive = request.cookies.get(TOKEN_USER)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        logged_in = payload["id"]
        user_info = db.users.find_one({"username": payload.get("id")})
        return render_template(
            "main/about.html", user_info=user_info, logged_in=logged_in
        )
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/home/profile/<username>")
def profile(username):
    token_receive = request.cookies.get(TOKEN_USER)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        logged_in = payload["id"]
        status = username == payload["id"]

        user_info = db.users.find_one({"username": username}, {"_id": False})
        return render_template(
            "main/profile.html", user_info=user_info, status=status, logged_in=logged_in
        )
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/home/update_profile", methods=["POST"])
def save_img():
    token_receive = request.cookies.get(TOKEN_USER)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        username = payload["id"]
        nama_receive = request.form["nama_give"]
        noHp_receive = request.form["noHp_give"]
        email_receive = request.form["email_give"]

        new_doc = {
            "profile_name": nama_receive,
            "no_telepon": noHp_receive,
            "email": email_receive,
        }

        if "file_give" in request.files:

            file = request.files["file_give"]
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f"profile_pics/{username}.{extension}"
            if not os.path.exists("static/profile_pics"):
                os.makedirs("static/profile_pics")
            file.save("./static/" + file_path)
            new_doc["profile_pic"] = filename
            new_doc["profile_pic_real"] = file_path

        db.users.update_one({"username": payload["id"]}, {"$set": new_doc})
        return jsonify({"result": "success", "msg": "Profile updated!"})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route("/admin/kelolapesanan")
def kelolaPesanan():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"username": payload.get("id")})
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 6, type=int)
        offset = (page - 1) * per_page
        pesanan_on_page = list(
            db.pesanan.find().skip(offset).limit(per_page).sort("_id", DESCENDING)
        )
        pagination = Pagination(
            page=page,
            per_page=per_page,
            total=db.pesanan.count_documents({}),
            show_single_page=True,
            alignment="end",
        )

        return render_template(
            "dashboard/kelolaPesanan.html",
            pesanan_coll=pesanan_on_page,
            pagination=pagination,
            user_info=user_info,
        )
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/admin/detailpesanan/<id>")
def detailPesanan(id):
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"username": payload.get("id")})
        pesanan_coll = db.pesanan.find_one({"_id": ObjectId(id)})
        return render_template(
            "dashboard/detailPesanan.html",
            pesanan=pesanan_coll,
            user_info=user_info,
        )
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/admin/kelolapesanan/resetpesanan", methods=["POST"])
def resetpesanan():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"username": payload.get("id")})
        db.pesanan.delete_many({})
        flash("Data pesanan berhasil direset")
        return redirect(url_for("kelolaPesanan", user_info=user_info))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/detailpesanan/delete/<id>", methods=["POST"])
def deleteDatasPesanan(id):
    db.pesanan.delete_one({"_id": ObjectId(id)})
    flash("Data berhasil dihapus")
    return redirect(url_for("kelolaPesanan"))


@app.route("/order")
def order():
    return render_template("main/order.html")


@app.route("/home/pesanan")
def pesanan():
    token_receive = request.cookies.get(TOKEN_USER)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"username": payload.get("id")})
        logged_in = payload.get("id")
        pesanan_cursor = db.pesanan.find({"username": logged_in}).sort(
            "_id", DESCENDING
        )
        pesanan_coll = list(pesanan_cursor)
        return render_template(
            "main/pesanan.html",
            user_info=user_info,
            pesanan_collet=pesanan_coll,
            logged_in=logged_in,
        )
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/produk")
def produk():
    produk_coll = list(db.products.find().sort("_id", DESCENDING))
    return render_template("main/produk.html", produk_coll=produk_coll)


@app.route("/home/produk")
def produkLogin():
    token_receive = request.cookies.get(TOKEN_USER)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        logged_in = payload["id"]
        user_info = db.users.find_one({"username": payload.get("id")})
        produk_coll = list(db.products.find().sort("_id", DESCENDING))
        return render_template(
            "main/produk.html",
            user_info=user_info,
            logged_in=logged_in,
            produk_coll=produk_coll,
        )
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/home/produk/pesan", methods=["POST"])
def orderProduk():
    token_receive = request.cookies.get(TOKEN_USER)
    try:
        name_customer = request.form.get("name_give")
        alamat = request.form.get("alamat_give")
        tanggal = request.form.get("tanggal_give")
        produk = request.form.get("produk_give")
        images = request.form.get("img_give")
        description = request.form.get("desc_give")
        produk = request.form.get("produk_give")
        price_count = int(request.form.get("price_give"))
        pesanan_count = int(request.form.get("pesanan_give"))
        total_price = price_count * pesanan_count
        current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        logged_in = payload["id"]
        doc = {
            "username": logged_in,
            "customer": name_customer,
            "alamat": alamat,
            "tanggalpesanan": tanggal,
            "produk": produk,
            "image": images,
            "description": description,
            "price": price_count,
            "jumlahpesanan": pesanan_count,
            "totalprice": total_price,
            "created_at": current_time,
        }

        db.pesanan.insert_one(doc)
        flash("Pesanan anda berhasil")
        return redirect(url_for("pesanan"))

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login/login.html")
    else:
        username_receive = request.form["username_give"]
        password_receive = request.form["password_give"]
        password_hash = hashlib.sha3_256(password_receive.encode("utf-8")).hexdigest()
        result = db.users.find_one(
            {
                "username": username_receive,
                "password": password_hash,
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


@app.route("/signup", methods=["GET", "POST"])
def sign_up():
    if request.method == "GET":
        return render_template("login/signup.html")
    else:
        try:
            username_receive = request.form.get("username_give")
            password_receive = request.form.get("password_give")
            existing_user = db.users.find_one({"username": username_receive})
            current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            if existing_user:
                return (
                    jsonify({"result": "error", "message": "Username sudah ada"}),
                    409,
                )
            password_hash = hashlib.sha3_256(
                password_receive.encode("utf-8")
            ).hexdigest()

            doc = {
                "username": username_receive,
                "password": password_hash,
                "profile_name": username_receive,
                "profile_pic": "",
                "profile_pic_real": "img/profile.jpg",
                "profile_info": "",
                "no_telepon": "",
                "email": "",
                "role": "user",
                "created_at": current_time,
            }

            db.users.insert_one(doc)

            return jsonify({"result": "success"})
        except Exception as e:
            app.logger.error(f"Error during signup: {e}")
            return jsonify({"result": "error", "message": "Internal Server Error"}), 500


@app.route("/signup/check_dup", methods=["POST"])
def check_dup():
    username_receive = request.form.get("username_give")
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({"result": "success", "exists": exists})


if __name__ == "__main__":
    app.run("0.0.0.0", port=8000, debug=True)
