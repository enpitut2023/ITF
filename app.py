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
# 環境変数からFirebaseサービスアカウントキーを読み込みます
# service_account_key = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT_ITF_DATABASE_B9026'))

# Firebaseクライアントを初期化します
key_path='itf-database-credential.json'
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
    "受け取り時間": None,
    "受取人": None,
    "状態" : None,
}
# Firestoreからデータ
docs_ref = db.collection('exhibit')

# ユーザーデータ
user_data = {
    "ユーザー名": None,
    "認証": None, # verified or None
    "学類": None,
    "学年": None,
}


@app.route("/")
def first():
  return redirect('/register')
 
# ユーザーデータベース登録
@app.route("/register",methods=['GET','POST'])
def register():
  if request.method=='GET':
    return render_template("register.html") 
  else:
    user_name = request.form.get('user_name')
    school = request.form.get('school')
    year = request.form.get('year')


  # データベース登録
    user_data['ユーザー名']=user_name
    user_data['学類']=school
    user_data['学年']=year
    # Firestoreからデータ
    user_docs_ref = db.collection('user').document()
    user_docs_ref.set(user_data)
    id=user_docs_ref.id  
    print(id)

    return redirect(f'{id}/signup')
  
# FIrebaseサインアップ入力、メール送信
@app.route("/<id>/signup")
def signup(id):
  return render_template("signup.html",id=id)

# メール認証
@app.route("/<id>/auth")
def mail_auth(id):
  return render_template("auth.html",id=id) 

@app.route("/<id>/flag")
def veri_flag(id):
  # 認証用のid
  uid = request.args.get('uid')
  tsukuba_mails=["@u.tsukuba.ac.jp","@s.tsukuba.ac.jp"]
  print(uid)
  user=auth.get_user(uid)
  email = user.email
  print(email)
  # uidからメールアドレスを取得し、筑波のものかを確かめる
  # Check if email ends with @u.tsukuba.ac.jp
  for tsukuba_mail in tsukuba_mails:
    if tsukuba_mail in email:
    # Firestoreからデータ
      user_docs_ref = db.collection('user').document(id)
      fetched_user_data=user_docs_ref.get().to_dict()
      fetched_user_data["認証"]="verified"
      user_docs_ref.update(fetched_user_data)
      return redirect("/home")  
    
  return redirect(f"/{id}/signup")
      
    
    
  

@app.route("/login")
def login():
  return render_template("login.html") 



    
  

 
#仮
@app.route("/home")
def home():
  # Firestoreからデータを取得します
  docs =docs_ref.get()
  # Firestoreから取得したデータをリストに格納します
  results = []
  for doc in docs:
      results.append(doc.to_dict())
  
  return render_template('home.html',results=results)


@app.route("/<username>/home")
def userhome(username):
  # Firestoreからデータを取得します
  docs =docs_ref.get()
  # Firestoreから取得したデータをリストに格納します
  results = []
  for doc in docs:
      results.append(doc.to_dict())
  
  return render_template('home.html',results=results,username=username)


@app.route("/<username>/mypage")
def mypage(username):


    # Firestoreからデータを取得します
  docs =docs_ref.get()
  # Firestoreから取得したデータをリストに格納します
  results = []
  for doc in docs:
    doc = doc.to_dict()
    if doc["出品者"]==username:
      results.append(doc)
        # Firestoreから取得したデータをリストに格納します
        
  # Firestoreからデータを取得します
  docs =user_docs_ref.get()
  for doc in docs:
      data = doc.to_dict()
      if(data["ユーザー名"]==username):
        return render_template('mypage.html',data=data,results=results)
  
      
#仮
@app.route("/exhibit",methods=['GET','POST'])
def testexhibit():
  if request.method=='GET':
    return render_template('exhibit.html')
  else:
    textname = request.form.get('textname')

    exhibit_data['教科書名']=textname

    docs_ref.add(exhibit_data)
    return redirect('/exhibit')

@app.route("/<username>/exhibit",methods=['GET','POST'])
def exhibit(username):
  if request.method=='GET':
    return render_template('exhibit.html',username=username)
  else:
    textname = request.form.get('textname')

    exhibit_data['出品者']=username
    exhibit_data['教科書名']=textname

    docs_ref.add(exhibit_data)
    return redirect(f'/{username}/home')
    

@app.route('/get_data')
def get_data():
    # Firestoreからデータを取得します
    docs =docs_ref.get()
    # Firestoreから取得したデータをリストに格納します
    results = []
    for doc in docs:
        results.append(doc.to_dict())

    # JSON形式でデータを返します
    return results

@app.route('/set_data', methods=['POST'])
def set_data():
    textname = request.form.get('textname')
    exhibit_data['教科書名']=textname

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


# @app.route('/delete', methods=['GET'])
#delete処理
def delete_data(
      doc_id : str = "3v86oConj2OtW4mI0vxL"
):
    doc_ref = docs_ref.document(doc_id)
    doc_ref.delete()
    return {"message": "Data deleted successfully"}, 200

# @app.route("/update", methods=['GET', 'POST'])
def update_data(
      doc_id : str = "6pjrviOAMg2UvxyR0h9f"
):
    copied_data = one_exhibit_data.copy()
    copied_data['教科書名']="textname"
    doc_ref = docs_ref.document(doc_id)
    doc_ref.update(copied_data)
    return redirect('/update')



@app.route("/purchase_confirmation",methods=['GET','POST'])
def purchase_confirmation():
  if request.method=='GET':
      # URLのクエリパラメータを取得
    # book_name = request.args.get('book')
    # seller_name = request.args.get('seller')
    # それかurlにidを埋め込む
    return render_template('purchase_confirmation.html')
  # else:
  #   place = request.form.get('place')
  #   date = request.form.get('date')
  #   #データのラベル変更、場所、日時追加
  #   docs =docs_ref.get()
  #   for doc in docs:
  #     doc = doc.to_dict()
  #     if #idが等しければ:  
       #データのラベル変更、場所、日時追加

# チャット
# app.config['SECRET_KEY'] = 'secret_key'
# socketio = SocketIO(app)

# チャットのメッセージを保存するリスト
# messages = []


# @app.route("/chat")
# def chat():
#   messages = Message.query.all()
#     chat_history = [{'sender': message.sender, 'message': message.message} for message in messages]
#     return render_template('index.html', chat_history=chat_history)
  
  
# @socketio.on('message')
# def handle_message(data):  # 受け取るデータを辞書型として受け取る
#     sender = data['sender']
#     message_content = data['message'] #会話内容
    
#     # 新しいメッセージをデータベースに保存
#     new_message = Message(sender=sender, message=message_content)
#     db.session.add(new_message)
#     db.session.commit()

#     emit('message', {'sender': sender, 'message': message_content}, broadcast=True)
# if __name__ == '__main__':
#   app.run(debug=False)
