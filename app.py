from bson import ObjectId
from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

import os

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

app.secret_key = 'CAMPING-VIEW'

# JWT 사용하기 위해한 SECRET_KEY
SECRET_KEY = 'CAMPING-VIEW'

client = MongoClient('13.125.154.61', 27017, username="test", password="test")
# client = MongoClient('localhost', 27017)
db = client.campingview


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = payload["id"]  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False
        user_info = db.users.find_one({"user_id": status}, {"_id": False})
        reviews = list(db.reviews.find({}))
        for i in range(len(reviews)):
            reviews[i]['_id'] = str(reviews[i]['_id'])
        return render_template('index.html', reviews=reviews, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        reviews = list(db.reviews.find({}))
        for i in range(len(reviews)):
            reviews[i]['_id'] = str(reviews[i]['_id'])
        return render_template('index.html', reviews=reviews)


## 회원가입 페이지
@app.route('/register')
def register():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        flash("이미 로그인되어 있습니다.")
        return redirect(url_for('home'))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return render_template('register.html', msg='회원가입 페이지')

# 서버 ID 중복체크 API
@app.route('/register/check_dup', methods=['POST'])
def check_dup():
    id_receive = request.form['id']
    exists = bool(db.member.find_one({"user_id": id_receive}))
    return jsonify({'result': 'success', 'exists': exists})

# 서버 닉네임 중복체크 API
@app.route('/register/check_dup_nick', methods=['POST'])
def check_dup_nick():
    nick_receive = request.form['nick']
    exists = bool(db.member.find_one({"nick": nick_receive}))
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
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        flash("이미 로그인되어 있습니다.")
        return redirect(url_for('home'))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return render_template('login.html')

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


##리뷰 등록페이지 호출
@app.route('/review/insert', methods=['GET'])
def review():
    return render_template('review.html', testmsg='/review/insert')


##리뷰 등록
@app.route('/review/insert.json', methods=['POST'])
def insert_review():
    token_receive = request.cookies.get('mytoken')
    print(token_receive)
    try:
        print(33333333333333333333)
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        print(payload)
        white_list = ['JPG', 'jpg', 'gif', 'png', 'PNG', 'webp']
        if 'image' in request.files:
            image = request.files['image']
        else:
            image = request.form['image']

        name = request.form['name']
        price = request.form['price']
        url = request.form['url']

        star = int(request.form['star'])

        content = request.form['content']

        # TODO 로그인 되어있는 member테이블의 '_id' 가져오기
        # member_id= request.form['member_id']

        today = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        doc = {
            'name': name,
            'price': price,
            'star': star,
            'content': content,
            'member_id': 1,
            'regist_date': today
        }

        if 'image' in request.files:
            extension = image.filename.split('.')[-1]
            if extension not in white_list:
                return jsonify({'result': 'false', 'msg': '올바른 파일 형식이 아닙니다!'})
            filename = f'file-{today}'
            save_to = f'static/img/{filename}.{extension}'
            image.save(save_to)
            doc['image'] = f'{filename}.{extension}'
        else:
            doc['crawling_image'] = image

        if url is not None:
            doc['url'] = url

        insert_id = db.reviews.insert_one(doc).inserted_id
        # TODO insert_id값 확인
        return jsonify({'result': 'true', 'review_id': str(insert_id)})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        print(1111111111111111111111111111111)
        flash("리뷰쓰기는 회원에게만 제공되는 서비스입니다.")
        return redirect(url_for('home'))


## 리뷰 상세페이지
@app.route('/review', methods=['GET'])
def review_detail():
    # 리뷰 아이디값 있으면 리뷰상세내용 출력

    review_id = ObjectId(request.args.get("review_id"))
    review = db.reviews.find_one({'_id': review_id})

    #TODO 내글인지확인
    # if review.member_id == login한 member_id :
    my_review = 'true'
    return render_template('review_detail.html', review=review, my_review=my_review)

#리뷰 등록시 image, 가격 크롤링
@app.route('/crawling/productInfo', methods=['POST'])
def crawling_product():

    #TODO og:image가 없거나 og:title자체가 없을때 처리
    #TODO 쿠팡은 크롤링이 안됨. why??????
    url_receive = request.form['product_url']
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

    data = requests.get(url_receive, headers=headers)
    soup = BeautifulSoup(data.text, 'html.parser')
    image_src = soup.select_one('meta[property="og:image"]')['content']
    title = soup.select_one('meta[property="og:title"]')['content']
    return jsonify({'title': title, 'image_src': image_src})

##리뷰 삭제
@app.route('/review/delete.json', methods=['POST'])
def delete_review():
    # TODO 로그인 되어있으면 진행. 아니면 return.
    review_id = ObjectId(request.args.get("delete_id"))
    print(type(review_id)) #object로 타입변환 됐는데 delete가 안됨

    # find_review = db.reviews.find_one({'_id': review_id})
    # if find_review is None:
    #     return redirect(url_for('home'), jsonify({'msg': '해당 리뷰가 없습니다.'}))

    # TODO 내 글이 아니면 return redirect('/review?'+give_id, jsonify({'msg': '본인의 리뷰만 삭제할 수 있습니다.'}))
    db.reviews.delete_one({'_id': review_id})
    print('test')
    return jsonify({'result':'true', 'msg': '리뷰가 삭제되었습니다.'})

# @app.route('/review/update', methods=['POST'])
# def update_review():
#     #TODO 로그인 되어있으면 진행. 아니면 return.
#     review_id = request.form['review_id']
#     review = db.reviews.find_one({'id':review_id})
#     if review is None:
#         #TODO 수정
#         return "/"
#
#     member_id = request.form['member_id']
#     # TODO 로그인 되어있는 member_id와  review.member_id가 같은지 확인
#     # 같으면 내글이니까 수정가능, 아니면 return.
#     image= request.form['image']
#     name = request.form['name']
#     price= request.form['price']
#     url= request.form['url']
#     star= request.form['star']
#     content= request.form['content']
#
#
#     doc = {
#         'image': image,
#         'name': name,
#         'price': price,
#         'star': star,
#         'content': content,
#         'url' : url,
#         'regist_date': datetime.today()
#     }
#     print(doc)
#     db.reviews.update_one({'id': review_id}, {'$set': doc})
#     return jsonify({'msg':"수정완료"})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)