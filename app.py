from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'CAMPING-VIEW'

# client = MongoClient('내AWS아이피', 27017, username="아이디", password="비밀번호")
client = MongoClient('localhost', 27017)
db = client.campingview


@app.route('/')
def home():
    return render_template('index.html')

## 회원가입 페이지
@app.route('/register')
def register():
    return render_template('register.html', msg='회원가입 페이지')

# 서버 ID 중복체크 API
@app.route('/register/check_dup', methods=['POST'])
def check_dup():
    id_receive = request.form['id']
    exists = bool(db.member.find_one({"user_id": id_receive}))
    # print(value_receive, type_receive, exists)
    return jsonify({'result': 'success', 'exists': exists})

# 서버 닉네임 중복체크 API
@app.route('/register/check_dup_nick', methods=['POST'])
def check_dup_nick():
    nick_receive = request.form['nick']
    exists = bool(db.member.find_one({"nick": nick_receive}))
    # print(value_receive, type_receive, exists)
    return jsonify({'result': 'success', 'exists': exists})

# 서버 아이디 생성 API
@app.route('/register/save', methods=['POST'])
def sign_up():
    id_receive = request.form['id']
    nick_receive = request.form['nick']
    password_receive = request.form['password']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "user_id": id_receive,
        "nick":nick_receive,
        "password": password_hash
    }
    db.member.insert_one(doc)
    return jsonify({'result': 'success'})


# 로그인 페이지
@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg='회원가입 페이지')

# 로그인 API
@app.route('/login_in', methods=['POST'])
def login_in():
    # 로그인
    id_receive = request.form['id']
    password_receive = request.form['password']
    #JWT 키로 전환
    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.member.find_one({'user_id': id_receive, 'password': pw_hash})

    if result is not None:
        payload = {
         'id': id_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)