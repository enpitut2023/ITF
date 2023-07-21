from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/")
def hello_world():
  return render_template('home.html')

@app.route("/mypage")
def mypage():
  return render_template('mypage.html')


@app.route("/exhibit")
def exhibit():
  return render_template('exhibit.html')

@app.route("/signup")
def signup():
  return render_template('signup.html')

if __name__ == '__main__':
  app.run(debug=False)
