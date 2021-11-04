from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'CAMPING-VIEW'

# client = MongoClient('내AWS아이피', 27017, username="아이디", password="비밀번호")
client = MongoClient('localhost', 27017)
db = client.campingview


@app.route('/')
def home():
    reviews = list(db.reviews.find({}))
    for i in range(len(reviews)):
        reviews[i]['_id'] = str(reviews[i]['_id'])
    print(reviews)
    return render_template('index.html', reviews=reviews)

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


##리뷰 등록페이지 호출
@app.route('/review/insert', methods=['GET'])
def insert_page():
    return render_template('review.html', testmsg='/review/insert')

##리뷰 등록
@app.route('/review/insert.json', methods=['POST'])
def insert_review():
    #TODO 로그인 되어있으면 진행. 아니면 return.
    white_list = ['JPG', 'jpg', 'gif', 'png', 'PNG', 'webp']
    if 'image' in request.files:
        image = request.files['image']
    else:
        image = request.form['image']
    # if image is None:
    #     return jsonify({'result': 'false', 'msg': '이미지를 등록해주세요'})
    name = request.form['name']
    # if name is None:
    #     return jsonify({'result': 'false', 'msg': '상품명을 입력해주세요'})
    price= request.form['price']
    # if price is None:
    #     return jsonify({'result': 'false', 'msg': '가격을 입력해주세요.'})
    url= request.form['url']

    star= request.form['star']
    # if star is None:
    #     return jsonify({'result': 'false', 'msg': '별점을 등록해주세요'})
    content= request.form['content']
    # if content is None:
    #     return jsonify({'result': 'false', 'msg': '리뷰내용을 입력해주세요'})
    #TODO 로그인 되어있는 member_id 가져오기
    #member_id= request.form['member_id']

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
        doc['image']= f'{filename}.{extension}'
    else:
        doc['crawling_image'] = image


    if url is not None:
        doc['url'] = url
    insert_review= db.reviews.insert_one(doc)
    # print(insert_review)
    # print(insert_review.inserted_id)
    # insert_id = insert_review.inserted_id
    #,'review_id':insert_id
    return jsonify({'result': 'true', 'msg': '등록이 완료되었습니다.'})

#리뷰 등록시 image, 가격 크롤링
@app.route('/crawling/productInfo', methods=['POST'])
def crawling_product():
    url_receive = request.form['product_url']
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

    data = requests.get(url_receive, headers=headers)
    soup = BeautifulSoup(data.text, 'html.parser')

    product_info= {
        'title' : soup.select_one('meta[property="og:title"]')['content'],
        'image_src' : soup.select_one('meta[property="og:image"]')['content']
    }

    return jsonify({'product_info': product_info})

##리뷰상세페이지 호출 /review/<id>
# @app.route('/review/<id>', methods=['GET'])
# def show_review():
#     print("'/review', methods=['GET']")
#     print(request.args.get['review_id'])
#     review_id = request.args.get['review_id']
#     print(review_id)
#     review = db.reviews.find_one({'id' : review_id})
#     return render_template('review.html', jsonify({'testmsg': '/review','review':review}))


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
#
# @app.route('/review/delete', methods=['POST'])
# def delete_review():
#     # TODO 로그인 되어있으면 진행. 아니면 return.
#     review_id = request.form['review_id']
#     review = db.reviews.find_one({'id': review_id})
#     if review is None:
#         #TODO 수정
#         return "/"
#     db.reviews.delete_one({'id': review_id})
#     return jsonify({'msg': '리뷰가 삭제되었습니다.'})

#TODO 공감
# @app.rout('/review/like', methods=['POST'])
# def like_review():
#     return jsonify({'msg': '완료'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)