from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
import os

app = Flask(__name__)

# MongoDB URI 설정
app.config["MONGO_URI"] = os.getenv('MONGO_URI', 'mongodb+srv://hishp:hishp@within.uwscqyk.mongodb.net/mydatabase?retryWrites=true&w=majority')
mongo = PyMongo(app)

# 기본 루트 (/) 추가
@app.route('/')
def index():
    return "Hello, this is the root endpoint. The app is running!"

# 인스타그램 ID를 저장하는 API
@app.route('/save_instagram_id', methods=['POST'])
def save_instagram_id():
    data = request.json
    user_instagram_id = data.get('userInstagramID')
    target_instagram_id = data.get('targetInstagramID')

    if not user_instagram_id or not target_instagram_id:
        return jsonify({"error": "Instagram ID is required"}), 400

    # MongoDB에 데이터 저장
    mongo.db.instagram_ids.insert_one({
        'user_instagram_id': user_instagram_id,
        'target_instagram_id': target_instagram_id
    })

    return jsonify({"message": "IDs saved successfully!"}), 200

# MongoDB 연결 테스트용 경로 추가
@app.route('/check_connection', methods=['GET'])
def check_connection():
    try:
        # MongoDB에 테스트 데이터 삽입
        mongo.db.test_connection.insert_one({'status': 'connected'})
        # 데이터베이스에서 데이터를 조회하여 연결 상태 확인
        connection_status = mongo.db.test_connection.find_one({'status': 'connected'})

        if connection_status:
            return jsonify({"message": "MongoDB is connected and working!"}), 200
        else:
            return jsonify({"error": "MongoDB connection failed."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
