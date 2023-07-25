from flask import render_template, jsonify, Flask
from flask import request, redirect, session
import os
import json
import firebase_admin
from google.cloud import firestore
from google.oauth2.service_account import Credentials
from firebase_admin import auth, initialize_app
import re
from flask_socketio import SocketIO, emit, join_room, leave_room
import requests
# 環境変数からFirebaseサービスアカウントキーを読み込みます
# service_account_key = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT_ITF_DATABASE_B9026'))

# Firebaseクライアントを初期化します
key_path = 'itf-database-credential.json'
credentials = Credentials.from_service_account_file(key_path)
cred = firebase_admin.credentials.Certificate(key_path)
firebase_admin.initialize_app(cred)

app = Flask(__name__)
db = firestore.Client(credentials=credentials)
with open('firebaseConfig.json') as json_file:
    data = json.load(json_file)


# 出品データ
exhibit_data = {
    "教科書名": None,
    "画像": None,
    "出品者": None,
    "受け取り場所": [],
    "受け取り日時": None,
    "受け取り時間": None,
    "受取人": None,
    "値段": None,
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
    return render_template("signup.html", id=id, config_data=data)


@app.route("/<id>/auth")
def mail_auth(id):
    # メール認証
    return render_template("auth.html", id=id, config_data=data)


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
        return render_template("login.html", flag=flag, config_data=data)
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


@app.route("/<id>/home", methods=['GET', 'POST'])
def home(id):
    # Firestoreからデータを取得します
    docs = docs_ref.get()
    results = []
    if request.method == 'GET':
        # Firestoreから取得したデータをリストに格納します
        for doc in docs:
            results.append(doc)

        return render_template('home.html', results=results, id=id)
    else:
        search_text = request.form.get('keyword')
        for doc in docs:
            if search_text in doc.to_dict()['教科書名']:
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
        if doc.to_dict()["出品者"] == username:
            results.append(doc)
            # Firestoreから取得したデータをリストに格納します

    return render_template('mypage.html', data=fetched_user_data, results=results, id=id)


@app.route('/<id>/search', methods=['POST'])
def search_books(id):
    book_name = request.form.get('book_name')
    # Google Books APIへのリクエスト
    response = requests.get(
        'https://www.googleapis.com/books/v1/volumes', params={'q': book_name})
    books_data = response.json()
    return render_template('search_results.html', books=books_data.get('items', []), id=id)


@app.route("/<id>/search_book", methods=['GET', 'POST'])
def book_search(id):
    user_docs_ref = db.collection('user').document(id)
    fetched_user_data = user_docs_ref.get().to_dict()
    username = fetched_user_data["ユーザー名"]
    if request.method == 'GET':
        return render_template('book_search.html', username=username, id=id)
    else:
        textname = request.form.get('bookTitle')
        image = request.form.get('bookImage')
        exhibit_data['出品者'] = username
        exhibit_data['教科書名'] = textname
        exhibit_data['画像'] = image
        exhibit_data["状態"] = "available"
        # Firestoreからデータ
        docs_ref = db.collection('exhibit').document()
        docs_ref.set(exhibit_data)
        ex_id = docs_ref.id
        return redirect(f'/{id}/exhibit/{ex_id}')





@app.route("/<id>/exhibit/<ex_id>",methods=['GET','POST'])
def exhibit(id,ex_id):
  if request.method=='GET':
    return render_template('exhibit.html',id=id,ex_id=ex_id)
  else:
    docs_ref = db.collection('exhibit').document(ex_id)
    fetched_data=docs_ref.get().to_dict()
    money = request.form.get('money')

    location1 = request.form.getlist('location1')
    fetched_data['値段'] = money
    fetched_data['受け取り場所'] = location1
    
    docs_ref.update(fetched_data)
    return redirect(f'/{id}/home')
  
@app.route('/get_data')
def get_data():
    # Firestoreからデータを取得します
    docs = docs_ref.get()
    # Firestoreから取得したデータをリストに格納します
    results = []
    for doc in docs:
        results.append(doc)

    return render_template('home.html', results=results, id=id)


@app.route('/<id>/delete/<doc_id>', methods=['GET'])
# delete処理
def delete_data(doc_id, id):
    doc_ref = docs_ref.document(doc_id)
    doc_ref.delete()
    return redirect(f"/{id}/mypage")


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
        location = request.form.getlist('location')
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


@app.route('/<id>/chatapp/<doc_id>')
def chat(id,doc_id):
    user_docs_ref = db.collection('user').document(id)
    fetched_user_data = user_docs_ref.get().to_dict()
    
    exhibit_ref = db.collection('exhibit').document(doc_id)
    fetched_exhibit_data = exhibit_ref.get().to_dict()
    
    return render_template('chatapp.html',id=id, doc_id=doc_id,config_data=data,user_data=fetched_user_data,exhibit_data=fetched_exhibit_data)



# サーバーサイドのWebSocketを追加

# socketio = SocketIO(app)
# @app.route("/<id>/chat")
# def chat(id):
#     user_docs_ref = db.collection('user').document(id)
#     fetched_user_data=user_docs_ref.get().to_dict()
#     user=fetched_user_data["ユーザー名"]
#     return render_template("chat.html",user=user)

# @socketio.on('message')
# def handle_message(data):
#     sender = data['sender']
#     message = data['message']
#     emit('message', {'sender': sender, 'message': message}, broadcast=True)
# app.config['SECRET_KEY'] = 'your-secret-key'
# socketio = SocketIO(app)

# # チャットルームの辞書。ユーザー名をキー、チャットメッセージのリストを値として持つ。
# chat_rooms = {}


# @app.route('/<id>/chat')
# def index():
#     return render_template('chat.html',id=id)


# # ユーザーごとのチャットルームのディクショナリ（ユーザーIDをキーに持つ）
# user_chat_rooms = {}

# # ユーザーのマッチングを行う関数（仮の例として、ユーザーIDの後半2文字が同じ場合にマッチングとします）
# def matching_users(user1_id, user2_id):
#     return user1_id[-2:] == user2_id[-2:]

# @app.route('/')
# def index():
#     return render_template('index.html')

# @socketio.on('connect')
# def on_connect():
#     print('Client connected')

# @socketio.on('join')
# def on_join(data):
#     user_id = data['user_id']
#     room = user_chat_rooms.get(user_id)

#     # マッチングしたユーザー同士でチャットルームを作成
#     if room is None:
#         room = user_id  # 仮の例として、ユーザーIDをチャットルームのIDとします
#         user_chat_rooms[user_id] = room

#     # ユーザーをルームに参加させる
#     join_room(room)

#     # 参加したユーザーにメッセージを送信
#     message = f'{user_id}さんが入室しました'
#     emit('message', {'username': 'システム', 'message': message}, room=room)

# # 以下、略（leaveイベント、messageイベントの処理など）


# @socketio.on('leave')
# def on_leave(data):
#     username = data['username']
#     room = data['room']
#     leave_room(room)


# @socketio.on('send_message')
# def send_message(data):
#     username = data['username']
#     room = data['room']
#     message = data['message']
#     chat_rooms[username].append(message)
#     emit('new_message', {'username': username, 'message': message}, room=room)


# if __name__ == '__main__':
#     socketio.run(app, debug=True)

if __name__ == '__main__':
    app.run(debug=False)
