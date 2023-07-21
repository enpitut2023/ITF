from flask import render_template, jsonify, Flask
from flask import request, redirect, session
import os
# from firebase_admin import credentials
import json
import firebase_admin
from google.cloud import firestore
from google.oauth2.service_account import Credentials

# 環境変数からFirebaseサービスアカウントキーを読み込みます
# service_account_key = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT_ITF_DATABASE_B9026'))

# Firebaseクライアントを初期化します
key_path='itf-database-credential.json'
credentials = Credentials.from_service_account_file(key_path)

app = Flask(__name__)
db = firestore.Client(credentials=credentials)

one_exhibit_data = {
    "教科書名": None,
    "出品者": None,
    "受け取り場所": None,
    "受け取り時間": None,
    "受取人": None,
}
# Firestoreからデータ
docs_ref = db.collection('exhibit')

@app.route("/")
def hello_world():
  # Firestoreからデータを取得します
  docs =docs_ref.get()
  # Firestoreから取得したデータをリストに格納します
  results = []
  for doc in docs:
      results.append(doc.to_dict())
  
  return render_template('home.html',results=results)

@app.route("/mypage")
def mypage():
  return render_template('mypage.html')


@app.route("/exhibit",methods=['GET','POST'])
def exhibit():
  if request.method=='GET':
    return render_template('exhibit.html')
  else:
    textname = request.form.get('textname')


    one_exhibit_data['教科書名']=textname

    docs_ref.add(one_exhibit_data)
    return redirect('/')
    

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
    one_exhibit_data['教科書名']=textname

    docs_ref.add(one_exhibit_data)
    return redirect('/exhibit')


@app.route("/purchase_confirmation")
def purchase_confirmation():
  return render_template('purchase_confirmation.html')



if __name__ == '__main__':
  app.run(debug=False)
