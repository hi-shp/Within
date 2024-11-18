from flask import Flask, request, jsonify, render_template, redirect, url_for, Response
from flask_pymongo import PyMongo
import os
from cryptography.fernet import Fernet

app = Flask(__name__)

# 환경 변수에서 MongoDB URI 및 암호화 키 가져오기
app.config["MONGO_URI"] = os.getenv('MONGO_URI')
mongo = PyMongo(app)
mongo.init_app(app)

# 암호화/복호화 키 설정
SECRET_KEY = os.getenv('SECRET_KEY', Fernet.generate_key().decode())
cipher_suite = Fernet(SECRET_KEY.encode())

def encrypt_data(data):
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(token):
    return cipher_suite.decrypt(token.encode()).decode()

# 기본 루트
@app.route('/')
def index():
    return render_template('index.html')

# 성공 메시지 페이지
@app.route('/success/<message>')
def success(message):
    return render_template('success.html', message=message)

# 오류 메시지 페이지
@app.route('/error/<error_message>/<encrypted_id>')
def error(error_message, encrypted_id):
    return render_template('error.html', error_message=error_message, encrypted_id=encrypted_id)

# 인스타그램 ID 저장 API
@app.route('/save_instagram_id', methods=['POST'])
def save_instagram_id():
    data = request.json
    user_instagram_id = data.get('userInstagramID')
    target_instagram_id = data.get('targetInstagramID')

    if not user_instagram_id or not target_instagram_id:
        return jsonify({"redirect": url_for('error', error_message="Instagram ID is required", encrypted_id="")}), 400

    # 한 명만 지목 가능하도록 기존 지목 확인
    existing_user = mongo.db.instagram_ids.find_one({'user_instagram_id': user_instagram_id})

    if existing_user:
        encrypted_id = encrypt_data(user_instagram_id)
        return jsonify({
            "redirect": url_for('error', error_message="You can only target one person.", encrypted_id=encrypted_id)
        }), 409

    # MongoDB에 데이터 저장 (새로운 지목)
    mongo.db.instagram_ids.insert_one({
        'user_instagram_id': user_instagram_id,
        'target_instagram_id': target_instagram_id
    })

    return jsonify({"redirect": url_for('success', message="Target selected successfully!")}), 200

# 기존 데이터 삭제 API
@app.route('/delete_target', methods=['POST'])
def delete_target():
    data = request.json
    encrypted_id = data.get('encryptedID')

    if not encrypted_id:
        return jsonify({"error": "요청이 잘못되었습니다."}), 400

    try:
        user_instagram_id = decrypt_data(encrypted_id)
    except Exception:
        return jsonify({"error": "유효하지 않은 토큰입니다."}), 400

    # MongoDB에서 데이터 삭제
    result = mongo.db.instagram_ids.delete_one({'user_instagram_id': user_instagram_id})

    if result.deleted_count == 0:
        return jsonify({"error": "일치하는 데이터를 찾을 수 없습니다."}), 404

    return jsonify({"message": "기존 지목이 성공적으로 삭제되었습니다."}), 200


@app.route('/ads.txt')
def ads_txt():
    content = "google.com, pub-4209969470096098, DIRECT, f08c47fec0942fa0"
    return Response(content, mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)
