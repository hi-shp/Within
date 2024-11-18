from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_pymongo import PyMongo
import os

app = Flask(__name__)

# MongoDB 연결 설정
app.config["MONGO_URI"] = os.getenv('MONGO_URI')
mongo = PyMongo(app)

# 임시 저장소 (서버 내 메모리)
temp_storage = {}

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
    if user_instagram_id in temp_storage:
        return jsonify({"redirect": url_for('error', error_message="You can only target one person.")}), 409

    # 임시 저장소에 데이터 저장
    temp_storage[user_instagram_id] = target_instagram_id

    return jsonify({"redirect": url_for('success', message="Target selected successfully!")}), 200

# 인스타그램 ID 삭제 API
@app.route('/delete_target', methods=['DELETE'])
def delete_target():
    # 클라이언트에서 전달된 데이터 가져오기
    data = request.json
    user_instagram_id = data.get('userInstagramID')

    # 사용자 ID가 없는 경우 처리
    if not user_instagram_id:
        return jsonify({'error': 'User ID is required'}), 400

    # 임시 저장소에서 데이터 삭제
    if user_instagram_id in temp_storage:
        del temp_storage[user_instagram_id]
        return jsonify({'message': 'Target deleted successfully'}), 200
    else:
        return jsonify({'error': f'No target found to delete for {user_instagram_id}'}), 404

if __name__ == '__main__':
    app.run(debug=True)
