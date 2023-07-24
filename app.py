from flask import render_template, jsonify, Flask
from flask import request, redirect, session
import os
import json
import firebase_admin
from google.cloud import firestore
from google.oauth2.service_account import Credentials
from firebase_admin import auth

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
    "メール": None,
    "学類": None,
    "学年": None,
}
# Firestoreからデータ
user_docs_ref = db.collection('user')

@app.route("/")
def first():
  return redirect("/home")

@app.route("/login")
def login():
  return render_template("login.html") 

@app.route("/signup",methods=['GET','POST'])
def signup():
  if request.method=='GET':
    return render_template("signup.html") 
  else:
    mail_adress = request.form.get('mail_adress')
    user_name = request.form.get('user_name')
    school = request.form.get('school')
    year = request.form.get('year')

    user_data['ユーザー名']=user_name
    user_data['メール']=mail_adress
    user_data['学類']=school
    user_data['学年']=year

    user_docs_ref.add(user_data)    
    return redirect('/home')
 
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



@app.route("/purchase_confirmation")
def purchase_confirmation():
  return render_template('purchase_confirmation.html')



if __name__ == '__main__':
  app.run(debug=False)
