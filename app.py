from flask import render_template, jsonify, Flask
from flask import request, redirect, session
import os
import json
import firebase_admin
from google.cloud import firestore
from google.oauth2.service_account import Credentials
from firebase_admin import auth, initialize_app
import re
from flask_socketio import SocketIO, emit
import copy

# Firebaseクライアントを初期化します
key_path = 'itf-database-credential.json'
credentials = Credentials.from_service_account_file(key_path)
cred = firebase_admin.credentials.Certificate(key_path)
firebase_admin.initialize_app(cred)

app = Flask(__name__)
db = firestore.Client(credentials=credentials)

# 出品データ
exhibit_data = {
    "教科書名": None,
    "出品者": None,
    "受け取り場所": None,
    "受け取り日時": None,
    "受け取り時間": None,
    "受取人": None,
    "状態": "available",
}
# Firestoreからデータ
docs_ref = db.collection('exhibit')

# ユーザーデータ
user_data = {
    "ユーザー名": None,
    "認証": None,  # verified or None
    "学類": None,
    "学年": None,
}


@app.route("/")
def first():
    flag = None
    return redirect(f'/{flag}/register')


@app.route("/<flag>/register", methods=['GET', 'POST'])
def register(flag):
    # ユーザーデータベース登録
    all_user = db.collection('user').get()
    users = []
    for user in all_user:
        users.append(user.to_dict()["ユーザー名"])
    if request.method == 'GET':
        return render_template("register.html", flag=flag)
    else:
        user_name = request.form.get('user_name')
        school = request.form.get('school')
        year = request.form.get('year')
        for user in users:
            if user == user_name:
                flag = "false"
                return redirect(f"/{flag}/register")

        # データベース登録
        user_data['ユーザー名'] = user_name
        user_data['学類'] = school
        user_data['学年'] = year
        # Firestoreからデータ
        user_docs_ref = db.collection('user').document()
        user_docs_ref.set(user_data)
        id = user_docs_ref.id
        print(id)

        return redirect(f'/{id}/signup')


@app.route("/<id>/signup")
def signup(id):
    # FIrebaseサインアップ入力、メール送信
    return render_template("signup.html", id=id)


@app.route("/<id>/auth")
def mail_auth(id):
    # メール認証
    return render_template("auth.html", id=id)


@app.route("/<id>/flag")
def veri_flag(id):
    # 認証用のid
    uid = request.args.get('uid')
    tsukuba_mails = ["@u.tsukuba.ac.jp", "@s.tsukuba.ac.jp"]
    user = auth.get_user(uid)
    email = user.email
    # uidからメールアドレスを取得し、筑波のものかを確かめる
    # Check if email ends with @u.tsukuba.ac.jp
    for tsukuba_mail in tsukuba_mails:
        if tsukuba_mail in email:
            # Firestoreからデータ
            user_docs_ref = db.collection('user').document(id)
            fetched_user_data = user_docs_ref.get().to_dict()
            fetched_user_data["認証"] = "verified"
            user_docs_ref.update(fetched_user_data)
            return redirect(f"/{id}/home")

    return redirect(f"/{id}/signup")


@app.route("/<flag>/login", methods=['GET', 'POST'])
def login(flag):
    # flagはユーザーがないのか、認証されていないのかを判別
    if request.method == 'GET':
        return render_template("login.html", flag=flag)
    else:
        get_user_name = request.form.get('user_name')
        # 'user'コレクションの全てのドキュメントのIDを取得
        user_docs_refs = db.collection('user').get()
        doc_ids = [doc.id for doc in user_docs_refs]
        for id in doc_ids:
            user_docs_ref = db.collection('user').document(id)
            fetched_user_data = user_docs_ref.get().to_dict()
            user_name = fetched_user_data["ユーザー名"]
            auth = fetched_user_data["認証"]
            if (user_name == get_user_name):
                if (auth == "verified"):
                    return redirect(f"/{id}/home")
                else:
                    flag = "not_verified"
                    return redirect(f"/{flag}/login")
        flag = "no_user"
        return redirect(f"/{flag}/login")


@app.route("/<id>/home")
def home(id):
    # Firestoreからデータを取得します
    docs = docs_ref.get()
    # Firestoreから取得したデータをリストに格納します
    results = []
    for doc in docs:
        results.append(doc)

    return render_template('home.html', results=results, id=id)


@app.route("/<id>/mypage")
def mypage(id):
    user_docs_ref = db.collection('user').document(id)
    fetched_user_data = user_docs_ref.get().to_dict()
    username = fetched_user_data["ユーザー名"]
    # Firestoreからデータを取得します
    docs = docs_ref.get()
    # Firestoreから取得したデータをリストに格納します
    results = []
    for doc in docs:
        doc = doc.to_dict()
        if doc["出品者"] == username:
            results.append(doc)
            # Firestoreから取得したデータをリストに格納します

        return render_template('mypage.html', data=fetched_user_data, results=results, id=id)


@app.route("/<id>/exhibit", methods=['GET', 'POST'])
def exhibit(id):
    user_docs_ref = db.collection('user').document(id)
    fetched_user_data = user_docs_ref.get().to_dict()
    username = fetched_user_data["ユーザー名"]
    if request.method == 'GET':
        return render_template('exhibit.html', username=username, id=id)
    else:
        textname = request.form.get('textname')

        exhibit_data['出品者'] = username
        exhibit_data['教科書名'] = textname
        exhibit_data["状態"] = "available"

        docs_ref.add(exhibit_data)
        return redirect(f'/{id}/home')


@app.route('/get_data')
def get_data():
    # Firestoreからデータを取得します
    docs = docs_ref.get()
    # Firestoreから取得したデータをリストに格納します
    results = []
    for doc in docs:
        results.append(doc.to_dict())

    # JSON形式でデータを返します
    return results


@app.route('/set_data', methods=['POST'])
def set_data():
    textname = request.form.get('textname')
    exhibit_data['教科書名'] = textname

    docs_ref.add(exhibit_data)
    return redirect('/exhibit')


@app.route('/test_signup', methods=['GET', 'POST'])
def signup_test():
    try:
        user = auth.create_user(
            email="namiki.takeyama@gmail.com",
            password="password"
        )
        return jsonify({'uid': user.uid}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/delete/<doc_id>', methods=['GET'])
# delete処理
def delete_data(doc_id):
    doc_ref = docs_ref.document(doc_id)
    doc_ref.delete()
    return {"message": "Data deleted successfully"}, 200


# @app.route('/delete/<doc_id>', methods=['GET'])
# #delete処理
# def delete_data(
#       doc_id : str = "3v86oConj2OtW4mI0vxL"
# ):
#     doc_ref = docs_ref.document(doc_id)
#     doc_ref.delete()
#     return {"message": "Data deleted successfully"}, 200

@app.route("/update/<doc_id>", methods=['GET', 'POST'])
def update_data(doc_id):
    copied_data = one_exhibit_data.copy()
    copied_data['教科書名'] = "textname"
    doc_ref = docs_ref.document(doc_id)
    doc_ref.update(copied_data)
    return redirect('/update')


@app.route("/<id>/info")
def info(id):
    user_docs_ref = db.collection('user').document(id)
    fetched_user_data = user_docs_ref.get().to_dict()
    username = fetched_user_data["ユーザー名"]
    # Firestoreからデータを取得します
    docs = docs_ref.get()
    # Firestoreから取得したデータをリストに格納します
    results = []
    for doc in docs:
        doc = doc.to_dict()
        if doc["出品者"] == username or doc["受取人"] == username:
            if doc["出品者"] != None and doc["受取人"] != None:
                results.append(doc)
    return render_template('info.html', id=id, results=results)


@app.route("/<id>/purchase_confirmation/<doc_id>", methods=['GET', 'POST'])
def purchase_confirmation(doc_id, id):
    # firebaseからユーザー情報を取得
    exhibit_ref = db.collection('exhibit').document(doc_id)
    fetched_exhibit_data = exhibit_ref.get().to_dict()

    if request.method == 'GET':
        return render_template('purchase_confirmation.html', id=id, data=fetched_exhibit_data, doc_id=doc_id)
    else:
        location = request.form.get('location')
        date = request.form.get('date')
        time = request.form.get('time')
        user_docs_ref = db.collection('user').document(id)
        fetched_user_data = user_docs_ref.get().to_dict()
        username = fetched_user_data["ユーザー名"]

        fetched_exhibit_data['状態'] = 'sold'
        fetched_exhibit_data['受取人'] = username
        fetched_exhibit_data['受け取り場所'] = location
        fetched_exhibit_data['受け取り日時'] = date
        fetched_exhibit_data['受け取り時間'] = time

        exhibit_ref.update(fetched_exhibit_data)
        return redirect(f"/{id}/home")


# @app.route("/thanks")
# def thanks():
#   return render_template('thanks.html')

if __name__ == '__main__':
    app.run(debug=False)
