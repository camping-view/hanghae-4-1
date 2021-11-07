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

#client = MongoClient('13.125.154.61', 27017, username="test", password="test")
client = MongoClient('localhost', 27017)
db = client.campingview

###메인페이지
@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        ###내 프로필이면 True, 다른 사람 프로필 페이지면 False
        status = payload["id"]

        ###최근 일자(내림차순)로 등록된 리뷰 리스트를 클라이언트로 전달
        reviews = list(db.reviews.find({}).sort("regist_date", -1))
        for i in range(len(reviews)):
            reviews[i]['_id'] = str(reviews[i]['_id'])
        return render_template('index.html', reviews=reviews, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        ###로그인 시간 만료 또는 토큰이 없어도 리뷰 리스트를 클라이언트로 전달
        reviews = list(db.reviews.find({}).sort("regist_date", -1))
        for i in range(len(reviews)):
            reviews[i]['_id'] = str(reviews[i]['_id'])
        return render_template('index.html', reviews=reviews)

###회원가입 페이지
@app.route('/register')
def register():
    token_receive = request.cookies.get('mytoken')
    try:
        ###하나의 브라우저(네이버) 창에서 로그인 된 후, 다른 브라우저(네이버) 창에서 로그인 하는 경우 안해도 됨
        jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        flash("이미 로그인되어 있습니다.")
        return redirect(url_for('home'))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return render_template('register.html')

###서버 ID 중복체크 API
@app.route('/register/check_dup', methods=['POST'])
def check_dup():
    ###클라이언트에서 받은 아이디가 DB에 존재하는지 확인
    id_receive = request.form['id']
    exists = bool(db.member.find_one({"user_id": id_receive}))
    return jsonify({'result': 'success', 'exists': exists})

###서버 닉네임 중복체크 API
@app.route('/register/check_dup_nick', methods=['POST'])
def check_dup_nick():
    ###클라이언트에서 받은 닉네임이 DB에 존재하는지 확인
    nick_receive = request.form['nick']
    exists = bool(db.member.find_one({"nick": nick_receive}))
    return jsonify({'result': 'success', 'exists': exists})

###서버 아이디 생성 API
@app.route('/register/save', methods=['POST'])
def sign_up():
    id_receive = request.form['id']
    nick_receive = request.form['nick']
    password_receive = request.form['password']
    # 비밀번호 해시함수로 암호화
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    # 클라이언트에서 전달받은 정보로 아이디 생성
    doc = {
        "user_id": id_receive,
        "nick":nick_receive,
        "password": password_hash
    }
    db.member.insert_one(doc)
    return jsonify({'result': 'success'})

###로그인 페이지
@app.route('/login')
def login():
    ###cookies에서 토큰 받기
    token_receive = request.cookies.get('mytoken')
    try:
        ###로그인 상태면 경고창 뛰우기,그리고 홈으로 돌아가기
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        flash("이미 로그인되어 있습니다.")
        return redirect(url_for('home'))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        ###로그인 상태 아니면 로그인 페이지로 가기
        return render_template('login.html')

###로그인 API
@app.route('/login_in', methods=['POST'])
def login_in():
    ###로그인 페이지에서 id pw 받기
    id_receive = request.form['id']
    password_receive = request.form['password']
    ###pw를 키로 전환하기
    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    ###member table에서 id, pw 찾기
    result = db.member.find_one({'user_id': id_receive, 'password': pw_hash})

    if result is not None:
        ###토큰 생성
        payload = {
         'id': id_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    ###찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

###리뷰 등록페이지 호출
@app.route('/review/insert', methods=['GET'])
def review():
    ###cookies에서 토큰 받기
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        ###로그인 상태면 리뷰등록페이지 호출
        status = payload["id"]
        jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        return render_template('review.html', status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        ###로그인 상태아니면 경고창띄우고 메인페이지 호출
        flash("리뷰쓰기는 회원에게만 제공되는 서비스입니다.")
        return redirect(url_for('home'))



###리뷰 등록
@app.route('/review/insert.json', methods=['POST'])
def insert_review():
    ###cookies에서 토큰 받기
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        ###로그인 상태면 리뷰등록페이지 호출
        write_id = str(db.member.find_one(({'user_id': payload['id']}))['_id'])
        image = request.form['image']

        ###첨부파일 이미지업로드도 가능했다면 필요한 코드들
        # white_list = ['JPG', 'jpg', 'gif', 'png', 'PNG', 'webp']
        # if 'image' in request.files:
        #     image = request.files['image']
        # else:
        #     image = request.form['image']

        name = request.form['name']
        price = request.form['price']
        url = request.form['url']
        print(request.form['star'])

        star = int(request.form['star'])

        content = request.form['content']

        ###오늘 날짜,시간을 형식(에 맞게 가져온다.ex)2021-11-06-09-47-57
        today = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        doc = {
            'name': name,
            'price': price,
            'star': star,
            'content': content,
            'member_id': write_id,
            'regist_date': today
        }
        doc['crawling_image'] = image

        ###첨부파일 이미지업로드도 가능했다면 필요한 코드들
        # if 'image' in request.files:
        #     extension = image.filename.split('.')[-1]
        #     if extension not in white_list:
        #         return jsonify({'result': 'false', 'msg': '올바른 파일 형식이 아닙니다!'})
        #     filename = f'file-{today}'
        #     save_to = f'static/img/{filename}.{extension}'
        #     image.save(save_to)
        #     doc['image'] = f'{filename}.{extension}'
        # else:
        #     doc['crawling_image'] = image

        if url is not None:
            doc['url'] = url

        ###리뷰 DB에 저장
        db.reviews.insert_one(doc)

        # insert_id=db.reviews.insert_one(doc).inserted_id
        #return jsonify({'result': 'true'},{'review_id':str(inserted_id)})
        # 이렇게하면 insert_id와 review table의 _id에 저장된 값이 다름.

        ###리뷰작성이 성공적으로 끝났을경우 result에 true를 담아서 데이터전송
        return jsonify({'result': True})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        ###로그인 되어야 리뷰쓰기 가능
        return jsonify({'result': False,'status':'login_fail', 'msg': '리뷰쓰기는 회원에게만 제공되는 서비스입니다.'})


###리뷰 상세페이지
@app.route('/review', methods=['GET'])
def review_detail():
    ###cookies에서 토큰 받기
    token_receive = request.cookies.get('mytoken')
    review_id = request.args.get("review_id")
    if review_id == '':
        flash("해당 리뷰가 없습니다. 다시 시도해주세요.")
        return redirect(url_for('home'))
        ###넘어온 reivew의 id값을 object형으로 변환
    review = db.reviews.find_one({'_id': ObjectId(review_id)})
    my_review = False
    status = False
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        ###내 프로필이면 True, 다른 사람 프로필 페이지면 False
        access_info = db.member.find_one({"user_id": payload['id']})
        status = True
        ###리뷰가 접속한유저가 적은 리뷰인지 체크
        if str(access_info['_id']) == str(review['member_id']):
            my_review = True
        ###리뷰데이터, 접속한유저가 적은리뷰인치 체크한 데이터, 로그인한 userid데이터
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        ###로그인되어있지않거나, 접속유저의 글이 아닐경우
        my_review = False
        ###리뷰데이터, 접속한유저가 적은리뷰인치 체크한 데이터, 로그인한 userid데이터
    return render_template('review_detail.html', review=review, my_review=my_review, status=status)


###리뷰 등록시 image, 가격 크롤링
@app.route('/crawling/productInfo', methods=['POST'])
def crawling_product():
    ###TODO og:image가 없거나 og:title자체가 없을때 처리
    ###TODO 크롤링 메소드 실행시간따져서 일정시간이 지나면 크롤링 실패처리

    url_receive = request.form['product_url']
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

    data = requests.get(url_receive, headers=headers)
    soup = BeautifulSoup(data.text, 'html.parser')
    ###og:image태그내용 가져오기
    image_src = soup.select_one('meta[property="og:image"]')['content']

    ###og:title태그내용 가져오기
    title = soup.select_one('meta[property="og:title"]')['content']
    return jsonify({'title': title, 'image_src': image_src})

##리뷰 삭제
@app.route('/review/delete', methods=['POST'])
def delete_review():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        review_id = ObjectId(request.form["delete_id"])
        review = db.reviews.find_one({'_id': review_id})
        access_info = db.member.find_one({'user_id': payload['id']})
        if str(access_info['_id']) == str(review['member_id']):
            db.reviews.delete_one({'_id': review_id})
            return jsonify({'result': True, 'msg': '리뷰가 삭제되었습니다.'})
        else:
            return jsonify({'result': False, 'msg': '본인의 리뷰만 삭제할 수 있습니다.'})
    except:
        return jsonify({'result': False,'msg': '로그인 한뒤에 이용해주세요.'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)