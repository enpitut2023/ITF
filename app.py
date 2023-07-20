from flask import render_template, jsonify, Flask
import os
from firebase_admin import credentials, firestore
import json
import firebase_admin
# from google.cloud import firestore
# from google.oauth2.service_account import Credentials

# 環境変数からFirebaseサービスアカウントキーを読み込みます
# service_account_key = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT_ITF_DATABASE_B9026'))

# # Firebaseクライアントを初期化します
# credentials = Credentials.from_service_account_info(service_account_key)
# db = firestore.Client(credentials=credentials)

# # Firebaseの認証情報を使用してFirebase Admin SDKを初期化します
cred = credentials.Certificate('itf-database-credential.json')
firebase_admin.initialize_app(cred)

app = Flask(__name__)
db = firestore.client()

@app.route("/")
def hello_world():
  return render_template('home.html')

@app.route("/mypage")
def mypage():
  return render_template('mypage.html')


@app.route("/exhibit")
def exhibit():
  return render_template('exhibit.html')

@app.route('/get_data')
def get_data():
    # Firestoreからデータを取得します
    docs = db.collection('test').get()

    # Firestoreから取得したデータをリストに格納します
    results = []
    for doc in docs:
        results.append(doc.to_dict())

    # JSON形式でデータを返します
    return jsonify(results)

@app.route("/purchase_confirmation")
def purchase_confirmation():
  return render_template('purchase_confirmation.html')



if __name__ == '__main__':
  app.run(debug=False)
