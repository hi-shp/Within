from flask import Flask, request, jsonify, render_template, redirect, url_for, Response
from flask_pymongo import PyMongo
import os
from cryptography.fernet import Fernet
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

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
    language = data.get('language', 'kor')  # 기본값은 한국어

    if not user_instagram_id or not target_instagram_id:
        error_message = "Instagram ID is required." if language == "eng" else "Instagram ID를 입력해주세요."
        return jsonify({"redirect": url_for('error', error_message=error_message, encrypted_id="")}), 400

    # 클라이언트 IP 가져오기
    client_ip = request.remote_addr
    ip_tracking = mongo.db.ip_tracking.find_one({'ip': client_ip})

    # 동일한 IP에서 이전 요청과 동일한 역방향 지목 방지
    reverse_match = mongo.db.instagram_ids.find_one({
        "user_instagram_id": target_instagram_id,
        "target_instagram_id": user_instagram_id
    })

    current_time = datetime.utcnow()

    if reverse_match:
        # IP 차단 상태 확인
        ip_block = mongo.db.ip_tracking.find_one({'ip': client_ip})

        if ip_block:
            block_time = ip_block.get('blocked_until')
            blocked_target = ip_block.get('blocked_user')

            # 현재 IP 차단 상태인지 확인
            if block_time and current_time < block_time:
                # 입력한 user_id가 이전에 타겟으로 기록된 경우 금지
                if user_instagram_id == blocked_target:
                    alert_message = "Impersonation is bad!" if language == "eng" else "사칭은 나빠!"
                    return jsonify({"alert": alert_message, "redirect": url_for('index')}), 429

        # IP 차단 설정
        block_until = current_time + timedelta(minutes=5)
        mongo.db.ip_tracking.update_one(
            {'ip': client_ip},
            {
                "$set": {
                    "blocked_user": user_instagram_id,
                    "blocked_until": block_until
                }
            },
            upsert=True
        )

        alert_message = "Impersonation is bad!" if language == "eng" else "사칭은 나빠!"
        return jsonify({"alert": alert_message, "redirect": url_for('index')}), 429

    # IP 및 요청 정보 갱신
    mongo.db.ip_tracking.update_one(
        {'ip': client_ip},
        {"$set": {"blocked_until": current_time + timedelta(minutes=5)}},  # blocked_until만 갱신
        upsert=True  # IP가 존재하지 않으면 새로 추가
    )

    # 스스로를 지목한 경우
    if user_instagram_id == target_instagram_id:
        alert_message = "You truly love yourself!" if language == "eng" else "스스로를 사랑하시는군요!"
        # 데이터 삭제
        mongo.db.instagram_ids.delete_one({'user_instagram_id': user_instagram_id})
        return jsonify({
            "alert": alert_message,
            "redirect": url_for('index')
        }), 200

    # 한 명만 지목 가능하도록 기존 지목 확인
    existing_user = mongo.db.instagram_ids.find_one({'user_instagram_id': user_instagram_id})

    if existing_user:
        encrypted_id = encrypt_data(user_instagram_id)
        error_message = "You can only target one person." if language == "eng" else "한 명만 지목할 수 있습니다."
        return jsonify({
            "redirect": url_for('error', error_message=error_message, encrypted_id=encrypted_id)
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
        # 매칭된 사용자 아이디들
        matched_user = reverse_match["user_instagram_id"]
        matched_target = reverse_match["target_instagram_id"]

        # 이메일 전송
        email_subject = "매칭 성공 알림"
        email_message = f"""
매칭 성공!
@{matched_user}와 @{matched_target}가 매칭되었습니다.


안녕하세요, Withinstar입니다! 🎉
두 분의 비밀스러운 마음이 서로 통했습니다.
@{matched_user}님과 @{matched_target}님, 그동안 전하지 못했던 감정을 안전하게 연결해 드릴 수 있어 저희도 정말 기쁩니다. 😊
지금부터 두 분만의 특별한 대화를 시작해 보세요. 서로의 이야기를 나누며 소중한 시간을 만들어가시길 바랍니다.
Withinstar가 항상 응원하겠습니다! 💌
"""
        send_email(subject=email_subject, message=email_message)

        success_message = "Match successful!" if language == "eng" else "매칭 성공!"
        return jsonify({"redirect": url_for('success', message=success_message)}), 200

    success_message = "Target selected successfully!" if language == "eng" else "상대방이 성공적으로 선택되었습니다."
    return jsonify({"redirect": url_for('success', message=success_message)}), 200


# 기존 데이터 삭제 API
@app.route('/delete_target', methods=['POST'])
def delete_target():
    data = request.json
    encrypted_id = data.get('encryptedID')
    user_language = data.get('language', 'kor')  # 기본값은 한국어

    if not encrypted_id:
        error_message = "요청이 잘못되었습니다." if user_language == 'kor' else "Invalid request."
        return jsonify({"error": error_message}), 400

    try:
        user_instagram_id = decrypt_data(encrypted_id)
    except Exception:
        error_message = "유효하지 않은 토큰입니다." if user_language == 'kor' else "Invalid token."
        return jsonify({"error": error_message}), 400

    # MongoDB에서 데이터 삭제
    result = mongo.db.instagram_ids.delete_one({'user_instagram_id': user_instagram_id})

    if result.deleted_count == 0:
        error_message = "일치하는 데이터를 찾을 수 없습니다." if user_language == 'kor' else "No matching data found."
        return jsonify({"error": error_message}), 404

    success_message = "기존 지목이 성공적으로 삭제되었습니다." if user_language == 'kor' else "Target successfully deleted."
    return jsonify({"message": success_message}), 200


@app.route('/ads.txt')
def ads_txt():
    content = "google.com, pub-4209969470096098, DIRECT, f08c47fec0942fa0"
    return Response(content, mimetype='text/plain')


if __name__ == '__main__':
    app.run(debug=True)
