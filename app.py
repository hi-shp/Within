from flask import Flask, request, jsonify, render_template, redirect, url_for, Response
from flask_pymongo import PyMongo
import os
from cryptography.fernet import Fernet
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# 환경 변수에서 MongoDB URI 및 암호화 키 가져오기
app.config["MONGO_URI"] = os.getenv('MONGO_URI')
mongo = PyMongo(app)

# 암호화/복호화 키 설정
SECRET_KEY = os.getenv('SECRET_KEY', Fernet.generate_key().decode())
cipher_suite = Fernet(SECRET_KEY.encode())

def encrypt_data(data):
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(token):
    return cipher_suite.decrypt(token.encode()).decode()

@app.after_request
def add_header(response):
    # 정적 파일 캐싱 방지
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# 이메일 전송 함수
def send_email(subject, message):
    sender_email = "hishphi0917@gmail.com"  # 발신 이메일
    sender_password = os.getenv("EMAIL_PASSWORD")  # 환경변수에서 비밀번호 가져오기
    receiver_email = "hishp@pusan.ac.kr"   # 수신 이메일

    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

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

    # 역방향 매칭 확인
    reverse_match = mongo.db.instagram_ids.find_one({
        "user_instagram_id": target_instagram_id,
        "target_instagram_id": user_instagram_id
    })

    if reverse_match:
        # 이메일 전송
        send_email(
            subject="매칭 성공 알림",
            message=f"매칭 성공!\n{user_instagram_id}와 {target_instagram_id}가 매칭되었습니다."
        )
        return jsonify({"redirect": url_for('success', message="매칭 성공!")}), 200

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