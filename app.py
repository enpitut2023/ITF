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
import copy
# 環境変数からFirebaseサービスアカウントキーを読み込みます
# service_account_key = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT_ITF_DATABASE_B9026'))


# Firebaseクライアントを初期化します
key_path = 'itf-database-credential.json'
credentials = Credentials.from_service_account_file(key_path)
cred = firebase_admin.credentials.Certificate(key_path)
firebase_admin.initialize_app(cred)

app = Flask(__name__)
# セッションを有効化するためのsecret_keyを設定
app.secret_key = "your-secret-key"
db = firestore.Client(credentials=credentials)
with open('firebaseConfig.json') as json_file:
    data = json.load(json_file)

# 出品データ
exhibit_data = {
    "bookname": None,
    "img": None,
    "seller": None,
    "place": [],
    "date": [],
    "time": [],
    "receiver": None,
    "price": None,
    "state": "available",
}

# Firestoreからデータ
docs_ref = db.collection('exhibit')

# ユーザーデータ
user_data = {
    "name": None,
    "auth": None,  # verified or None
    "faculty": None,
    "year": None,
    "mail": None,
}

    # キーが英語じゃないとだめ、この処理のほうが軽い
        # ユーザー名に対応するデータをFirestoreから取得
        # user_docs_refs = db.collection('user').where("name", "==", username).get()
        
        # # 該当するユーザーが存在するかチェック
        # for doc in user_docs_refs:
        #     user_data = doc.to_dict()
        

@app.route("/")
def first():
    global user_auth
    user_auth=False
    return redirect('/guest_home')

@app.route("/guest_home", methods=['GET', 'POST'])
def guest_home():
    docs = docs_ref.get()
    
    # 'user'コレクションの全てのドキュメントのIDを取得
    # user_docs_refs = db.collection('user').get()
    # doc_ids = [doc.id for doc in user_docs_refs]
    if request.method == 'GET':
        results = []
        # Firestoreから取得したデータをリストに格納します
        
        for doc in docs:
            exuser = doc.to_dict()["seller"]
            user_docs = db.collection('user').where("name", "==", exuser).get()
            for user_doc in user_docs:
                exuser_id = user_doc.id
                pair = (doc,exuser_id)
                results.append(pair)
                break
        return render_template('guest_home.html', results=results)        

    else:
        results = []
        search_text = request.form.get('keyword')
        for doc in docs:
            if search_text in doc.to_dict()['bookname']:
                exuser = doc.to_dict()["seller"]
                user_docs = db.collection('user').where("name", "==", exuser).get()
                for user_doc in user_docs:
                    exuser_id = user_doc.id
                    pair = (doc,exuser_id)
                    results.append(pair)
                    break        
        if results == []:
            results=None
        return render_template('guest_home.html', results=results)
        
@app.route("/<flag>/register", methods=['GET', 'POST'])
def register(flag):
    # ユーザーデータベース登録
    all_user = db.collection('user').get()
    users = []
    for user in all_user:
        users.append(user.to_dict()["name"])
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
        userdata = user_name + "-" + school + "-" + year

        # Firestoreからデータ
        user_docs_ref = db.collection('user').document()
        id = user_docs_ref.id
        return redirect(f'/{userdata}/{id}/signup')


@app.route("/<userdata>/<id>/signup")
def signup(id, userdata):
    # FIrebaseサインアップ入力、メール送信
    return render_template("signup.html", id=id, config_data=data, userdata=userdata)


@app.route("/<userdata>/<id>/auth")
def mail_auth(id, userdata):

    return render_template("auth.html", id=id, config_data=data, userdata=userdata)


@app.route("/<userdata>/<id>/flag")
def veri_flag(id, userdata):
    # auth用のid
    uid = request.args.get('uid')
    tsukuba_mails = ["tsukuba.ac.jp"]
    user = auth.get_user(uid)
    email = user.email
    # uidからメールアドレスを取得し、筑波のものかを確かめる
    # Check if email ends with @u.tsukuba.ac.jp
    for tsukuba_mail in tsukuba_mails:
        if tsukuba_mail in email:
            # Firestoreからデータ
            user_docs_ref = db.collection('user').document(id)
            copied_user_data = copy.deepcopy(user_data)
            copied_user_data["auth"] = "verified"
            result_list = userdata.split("-")
            # データベース登録
            copied_user_data['name'] = result_list[0]
            copied_user_data['faculty'] = result_list[1]
            copied_user_data['year'] = result_list[2]
            copied_user_data["mail"] = email
            user_docs_ref.set(copied_user_data)
            session['user_id']=id
            return redirect(f"/{id}/home")

    return redirect(f"/{id}/signup")

# パスワード間違ってても入れるのを直す
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        session.pop('user_id', None)
        return render_template("login.html", config_data=data)
    else:
        udata = request.get_json()
        username = udata.get("username")
        # ユーザー名に対応するデータをFirestoreから取得
        user_docs_refs = db.collection('user').where("name", "==", username).get()
        if len(user_docs_refs) != 0:
            # 該当するユーザーが存在するかチェック
            for doc in user_docs_refs:
                fetched_user_data = doc.to_dict()
                id=doc.id
                email = fetched_user_data["mail"]
                return jsonify({"email": email, "id": id}), 200        
        else:
             return jsonify({"email": False, "id": None}), 200
            

@app.route("/<id>/login_success")
def login_success(id):
    session['user_id'] = id 
    return redirect(f"/{id}/home")   

# セッションがどのくらいで消えるのか、ちゃんとログアウトせず閉じた場合はブラウザを閉じた瞬間閉じる、ブラウザごとにセッションを持つ
def is_certified():
    if 'user_id' in session:
        return True
    else:
        return False

# @app.route('/receive_username', methods=['POST'])
# def receive_username():
#     # usernameに合致するemailを返す
#     get_user_name = request.get_json()['username']
#     # ユーザー名に対応するデータをFirestoreから取得
#     fetched_user_data = db.collection('user').where("user_name", "==", get_user_name).get().to_dict()
#     # 該当するユーザーが存在するか
#     if len(fetched_user_data) != 0:
#         auth = fetched_user_data["auth"]
#         email = fetched_user_data["mail"]
#         if (auth == "verified"):
#             return jsonify({'email': email})
#         else:
#             flag = "not_verified"
#             return jsonify({'flag': flag})


@app.route("/<id>/home", methods=['GET', 'POST'])
def home(id):
    # Firestoreからデータを取得します
    
    docs = docs_ref.get()
    results = []
    # 'user'コレクションの全てのドキュメントのIDを取得

  
    if request.method == 'GET':
        if is_certified():
            results = []
            # Firestoreから取得したデータをリストに格納します          
            for doc in docs:
                exuser = doc.to_dict()["seller"]
                user_docs = db.collection('user').where("name", "==", exuser).get()
                for user_doc in user_docs:
                    exuser_id = user_doc.id
                    pair = (doc,exuser_id)
                    results.append(pair)
                    break
            return render_template('home.html', results=results, id=id)    
        return redirect("/login")
    else:
        results = []
        search_text = request.form.get('keyword')
        for doc in docs:
            if search_text in doc.to_dict()['bookname']:
                exuser = doc.to_dict()["seller"]
                user_docs = db.collection('user').where("name", "==", exuser).get()
                for user_doc in user_docs:
                    exuser_id = user_doc.id
                    pair = (doc,exuser_id)
                    results.append(pair)
                    break        
        if results == []:
            results=None
        return render_template('home.html', results=results,id=id)


@app.route("/<id>/mypage")
def mypage(id):
    if is_certified():
        user_docs_ref = db.collection('user').document(id)
        fetched_user_data = user_docs_ref.get().to_dict()
        username = fetched_user_data["name"]
        # Firestoreから取得したデータをリストに格納します
        results = []
        docs = db.collection('exhibit').where("seller", "==", username).get()    
        for doc in docs:
            results.append(doc)

        return render_template('mypage.html', data=fetched_user_data, results=results, id=id)
    return redirect("/login")

@app.route("/<id>/userpage", methods=['POST'])
def userpage(id):
    exuser_id = request.form.get('exuser_id')
    user_docs_ref = db.collection('user').document(exuser_id)
    fetched_user_data = user_docs_ref.get().to_dict()
    username = fetched_user_data["name"]

    # Firestoreから取得したデータをリストに格納します
    results = []
    docs = db.collection('exhibit').where("seller", "==", username).get()    
    for doc in docs:
        results.append(doc)
    return render_template('userpage.html', id=id, data=fetched_user_data, results=results)
    

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
    username = fetched_user_data["name"]
    if request.method == 'GET':
        if is_certified():
            return render_template('book_search.html', username=username, id=id)
        return redirect("/login")
    else:
        textname = request.form.get('bookTitle')
        image = request.form.get('bookImage')
        exhibit_data['seller'] = username
        exhibit_data['bookname'] = textname
        exhibit_data['img'] = image
        exhibit_data["state"] = "available"
        # Firestoreからデータ
        docs_ref = db.collection('exhibit').document()
        docs_ref.set(exhibit_data)
        ex_id = docs_ref.id
        return redirect(f'/{id}/exhibit/{ex_id}')
    

@app.route("/<id>/exhibit/<ex_id>", methods=['GET', 'POST'])
def exhibit(id, ex_id):
    if request.method == 'GET':
        if is_certified():
            return render_template('exhibit.html', id=id, ex_id=ex_id)
        return redirect("/login")
    else:
        docs_ref = db.collection('exhibit').document(ex_id)
        fetched_data = docs_ref.get().to_dict()
        money = request.form.get('money')

        location1 = request.form.getlist('location1')
        any_location = request.form.get('any_location')
        fetched_data['price'] = money
        fetched_data['place'] = location1
        fetched_data['place'].append(any_location)

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
    if is_certified():
        doc_ref = docs_ref.document(doc_id)
        doc_ref.delete()
        return redirect(f"/{id}/mypage")


# @app.route("/update/<doc_id>", methods=['GET', 'POST'])
# def update_data(doc_id):
#     copied_data = one_exhibit_data.copy()
#     copied_data['bookname'] = "textname"
#     doc_ref = docs_ref.document(doc_id)
#     doc_ref.update(copied_data)
#     return redirect('/update')


@app.route("/<id>/info")
def info(id):
    if is_certified():
        # firebaseからユーザー情報を取得
        user_docs_ref = db.collection('user').document(id)
        fetched_user_data = user_docs_ref.get().to_dict()
        username = fetched_user_data["name"]
        # Firestoreからデータを取得します
        docs = docs_ref.get()
        # Firestoreから取得したデータをリストに格納します
        results = []
        docs = db.collection('exhibit').where("seller", "==", username).get()    
        for doc in docs:
            if doc.to_dict()["seller"] == username or doc.to_dict()["receiver"] == username:
                if doc.to_dict()["seller"] != None and doc.to_dict()["receiver"] != None:
                    results.append(doc)
        return render_template('info.html', id=id, results=results, username=username)
    return redirect("/login")
# 購入確定


@app.route("/<id>/buy/<doc_id>", methods={'GET'})
def buy(doc_id, id):
    datetime_value = request.args.get('datetime')
    # datetime_valueを解析してdateとtimeに分割する処理を行う
    # 例えば、datetime_valueをアンダースコアで分割してdateとtimeを取得できる
    date, time = datetime_value.split('_')
    # firebaseからユーザー情報を取得
    exhibit_ref = db.collection('exhibit').document(doc_id)
    fetched_exhibit_data = exhibit_ref.get().to_dict()
    fetched_exhibit_data['state'] = 'sold'
    fetched_exhibit_data['date'] = [date]
    fetched_exhibit_data['time'] = [time]
    exhibit_ref.update(fetched_exhibit_data)
    return redirect(f"/{id}/info")

@app.route("/<id>/not_buy/<doc_id>", methods={'GET'})
def not_buy(doc_id, id):
    exhibit_ref = db.collection('exhibit').document(doc_id)
    fetched_exhibit_data = exhibit_ref.get().to_dict()    
    fetched_exhibit_data['state'] = 'available'
    fetched_exhibit_data['receiver'] = None
    exhibit_ref.update(fetched_exhibit_data)
    return redirect(f"/{id}/info")

@app.route("/<id>/purchase_confirmation/<doc_id>", methods=['GET', 'POST'])
def purchase_confirmation(doc_id, id):

    # firebaseからユーザー情報を取得
    exhibit_ref = db.collection('exhibit').document(doc_id)
    fetched_exhibit_data = exhibit_ref.get().to_dict()

    if request.method == 'GET':
        if is_certified():
            return render_template('purchase_confirmation.html', id=id, data=fetched_exhibit_data, doc_id=doc_id)
        return redirect("/login")
    else:
        location = request.form.getlist('location')
        date = request.form.getlist('date')
        time = request.form.getlist('time')
        user_docs_ref = db.collection('user').document(id)
        fetched_user_data = user_docs_ref.get().to_dict()
        username = fetched_user_data["name"]

        fetched_exhibit_data['state'] = 'dealing'
        fetched_exhibit_data['receiver'] = username
        fetched_exhibit_data['place'] = location
        fetched_exhibit_data['date'] = date
        fetched_exhibit_data['time'] = time

        exhibit_ref.update(fetched_exhibit_data)
        return redirect(f"/{id}/home")


# @app.route('/<id>/chatapp/<doc_id>')
# def chat(id, doc_id):
#     user_docs_ref = db.collection('user').document(id)
#     fetched_user_data = user_docs_ref.get().to_dict()

#     exhibit_ref = db.collection('exhibit').document(doc_id)
#     fetched_exhibit_data = exhibit_ref.get().to_dict()

#     return render_template('chatapp.html', id=id, doc_id=doc_id, config_data=data, user_data=fetched_user_data, exhibit_data=fetched_exhibit_data)


# サーバーサイドのWebSocketを追加

# socketio = SocketIO(app)
# @app.route("/<id>/chat")
# def chat(id):
#     user_docs_ref = db.collection('user').document(id)
#     fetched_user_data=user_docs_ref.get().to_dict()
#     user=fetched_user_data["name"]
#     return render_template("chat.html",user=user)

# @socketio.on('message')
# def handle_message(data):
#     sender = data['sender']
#     message = data['message']
#     emit('message', {'sender': sender, 'message': message}, broadcast=True)
# app.config['SECRET_KEY'] = 'your-secret-key'
# socketio = SocketIO(app)

# # チャットルームの辞書。nameをキー、チャットメッセージのリストを値として持つ。
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
