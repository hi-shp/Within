from flask import Flask, request, jsonify, render_template, redirect, url_for, Response
from flask_pymongo import PyMongo
import os

app = Flask(__name__)

# 환경 변수에서 MongoDB URI 가져오기
app.config["MONGO_URI"] = os.getenv('MONGO_URI')
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

    return jsonify({"redirect": url_for('success', message="Target selected successfully!")}), 200

@app.route('/ads.txt')
def ads_txt():
    content = "google.com, pub-4209969470096098, DIRECT, f08c47fec0942fa0"
    return Response(content, mimetype='text/plain')

@app.route('/delete_target', methods=['DELETE'])
def delete_target():
    user_instagram_id = request.cookies.get('userInstagramID')  # 사용자 ID를 쿠키에서 가져오기

    print(f"Received request to delete target for user ID: {user_instagram_id}")  # 요청 로그

    if not user_instagram_id:
        print("No user ID found in cookies")
        return jsonify({'error': 'User not authenticated'}), 401

    # MongoDB에서 해당 사용자의 지목 데이터 삭제
    result = mongo.db.instagram_ids.delete_one({'user_instagram_id': user_instagram_id})

    print(f"Delete result: {result.deleted_count} document(s) deleted")  # 삭제 결과 로그

    if result.deleted_count == 0:
        return jsonify({'error': 'No target found to delete'}), 404

    return jsonify({'message': 'Target deleted successfully'}), 200


if __name__ == '__main__':
    app.run(debug=True)
