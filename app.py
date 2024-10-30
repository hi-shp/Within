from flask import Flask, request, jsonify, render_template
from flask_pymongo import PyMongo
import os

app = Flask(__name__)

# 환경 변수에서 MongoDB URI 가져오기
app.config["MONGO_URI"] = os.getenv('MONGO_URI')
mongo = PyMongo(app)

# 기본 루트 추가 (앱 동작 확인용)
@app.route('/')
def index():
    return render_template('index.html')

# 인스타그램 ID를 저장하는 API (한 명만 지목 가능하게 수정)
@app.route('/save_instagram_id', methods=['POST'])
def save_instagram_id():
    data = request.json
    user_instagram_id = data.get('userInstagramID')
    target_instagram_id = data.get('targetInstagramID')

    if not user_instagram_id or not target_instagram_id:
        return jsonify({"error": "Instagram ID is required"}), 400

    # 한 명만 지목 가능하도록 기존 지목 확인
    existing_user = mongo.db.instagram_ids.find_one({
        'user_instagram_id': user_instagram_id
    })

    if existing_user:
        return jsonify({"error": "You can only target one person."}), 409

    # MongoDB에 데이터 저장 (새로운 지목)
    mongo.db.instagram_ids.insert_one({
        'user_instagram_id': user_instagram_id,
        'target_instagram_id': target_instagram_id
    })

    return jsonify({"message": "Target selected successfully!"}), 200

@app.route('/ads.txt')@app.route('/ads.txt')
def ads_txt():
    content = "google.com, pub-4209969470096098, DIRECT, f08c47fec0942fa0"
    return Response(content, mimetype='text/plain')git add .
git commit -m "."
git push heroku main

def ads_txt():
    content = "google.com, pub-4209969470096098, DIRECT, f08c47fec0942fa0"
    return Response(content, mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)
