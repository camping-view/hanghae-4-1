from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.campingview

## HTML을 주는 부분
@app.route('/')
def home():
   return render_template('index.html')

## 회원가입 페이지
@app.route('/register')
def register():
   return render_template('register.html')

# 회원가입 api
@app.route('/register/save', methods=['POST'])
def register_save():
   id_receive = request.form['id']
   password_receive = request.form['password']
   # pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
   nick_receive = request.form['nick']

   doc = {
        'user_id':id_receive,
        'password': password_receive,
        'nick': nick_receive
   }
   db.memeber.insert_one(doc)

   return jsonify({'result': 'success'})

# ## 아이디 중복 확인 api
# @app.route('/register/idcheck', methods=['POST'])
# def check_id():
#     id_receive = request.form['id']
#     exists = bool(db.memeber.find_one({'id':id_receive}))
#
#     return jsonify({'exists':exists})
#
# ## 닉네임 중복 확인 api
# @app.route('/register/nickcheck', methods=['POST'])
# def check_nick():
#     nick_receive = request.form['nick']
#     exists = bool(db.memeber.find_one({'nick':nick_receive}))
#     return jsonify({'exists':exists})

if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)