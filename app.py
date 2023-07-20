from flask import Flask
from flask import render_template
import os
from flask import Flask, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

# Firebaseの認証情報を使用してFirebase Admin SDKを初期化します
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


if __name__ == '__main__':
  app.run(debug=False)
