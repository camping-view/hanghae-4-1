from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

## HTML을 주는 부분
@app.route('/')
def home():
   return render_template('index.html')

## 회원가입 페이지
@app.route('/regist')
def member_join():
   return render_template('join.html')

if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)