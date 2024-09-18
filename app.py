from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
import os

app = Flask(__name__)

# 환경 변수에서 MongoDB URI 가져오기
# .env 파일 또는 Heroku 환경 변수 설정을 통해 관리 가능
app.config["MONGO_URI"] = os.getenv('MONGO_URI', 'mongodb+srv://hishp:<db_password>@within.uwscqyk.mongodb.net/mydatabase?retryWrites=true&w=majority')

mongo = PyMongo(app)

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

if __name__ == '__main__':
    app.run(debug=True)
