from flask import Flask, request, jsonify, render_template, redirect, url_for, Response
from flask_pymongo import PyMongo
import jwt
import datetime
import os

app = Flask(__name__)

# 환경 변수에서 MongoDB URI 및 JWT 비밀 키 가져오기
app.config["MONGO_URI"] = os.getenv('MONGO_URI')
SECRET_KEY = os.getenv('SECRET_KEY', 'your_default_secret_key')  # 환경 변수에서 비밀 키 가져오기
mongo = PyMongo(app)

# 기본 루트
@app.route('/')
def index():
    return render_template('index.html')

# 성공 메시지 페이지
@app.route('/success/<message>')
def success(message):
    return render_template('success.html', message=message)

# 오류 메시지 페이지
@app.route('/error/<error_message>')
def error(error_message):
    return render_template('error.html', error_message=error_message)

# 인스타그램 ID 저장 API
@app.route('/save_instagram_id', methods=['POST'])
def save_instagram_id():
    data = request.json
    user_instagram_id = data.get('userInstagramID')
    target_instagram_id = data.get('targetInstagramID')

    if not user_instagram_id or not target_instagram_id:
        return jsonify({"redirect": url_for('error', error_message="Instagram ID is required")}), 400

    # 한 명만 지목 가능하도록 기존 지목 확인
    existing_user = mongo.db.instagram_ids.find_one({'user_instagram_id': user_instagram_id})

    if existing_user:
        return jsonify({"redirect": url_for('error', error_message="You can only target one person.")}), 409

    # MongoDB에 데이터 저장 (새로운 지목)
    mongo.db.instagram_ids.insert_one({
        'user_instagram_id': user_instagram_id,
        'target_instagram_id': target_instagram_id
    })

    # JWT 생성
    payload = {
        'userInstagramID': user_instagram_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # 만료 시간: 1시간
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    return jsonify({"token": token, "redirect": url_for('success', message="Target selected successfully!")}), 200

# ads.txt 파일 제공
@app.route('/ads.txt')
def ads_txt():
    content = "google.com, pub-4209969470096098, DIRECT, f08c47fec0942fa0"
    return Response(content, mimetype='text/plain')

# 인스타그램 ID 삭제 API
@app.route('/delete_target', methods=['DELETE'])
def delete_target():
    token = request.headers.get('Authorization')  # 요청 헤더에서 JWT 가져오기

    if not token:
        return jsonify({'error': 'Token is missing'}), 401

    try:
        # JWT 디코딩 및 검증
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_instagram_id = decoded_token.get('userInstagramID')
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

    print(f"Received request to delete target for user ID: {user_instagram_id}")  # 요청 로그

    # MongoDB에서 해당 사용자의 지목 데이터 삭제
    result = mongo.db.instagram_ids.delete_one({'user_instagram_id': user_instagram_id})

    print(f"Delete result: {result.deleted_count} document(s) deleted")  # 삭제 결과 로그

    if result.deleted_count == 0:
        return jsonify({'error': 'No target found to delete'}), 404

    return jsonify({'message': 'Target deleted successfully'}), 200


if __name__ == '__main__':
    app.run(debug=True)
