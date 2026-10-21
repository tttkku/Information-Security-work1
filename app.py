from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User
import html
import os


app = Flask(__name__)
# 配置跨域
CORS(app) 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'local-dev-secret-key')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON in request"}), 400
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()  # 参数化查询，防 SQLi
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"msg": "Bad username or password"}), 401
    token = create_access_token(identity=str(user.id))
    return jsonify(access_token=token), 200


@app.route('/api/data', methods=['GET'])
@jwt_required()          # ← 这就是“中间件拦截”，Flask-JWT-Extended 自动处理
def get_data():
    user_id = get_jwt_identity()
    # 模拟用户可控内容，演示 XSS 转义
    raw_content = request.args.get('content', '<script>alert("xss")</script>')
    safe_content = html.escape(raw_content)  # 核心：输出转义

    return jsonify({
        "user_id": user_id,
        "data": f"This is the protected data of User-{user_id}",
        "safe_content": safe_content
    }), 200


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "secure-api-demo"}), 200



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='testuser').first():
            hashed = bcrypt.generate_password_hash('password123').decode('utf-8')
            db.session.add(User(username='testuser', password_hash=hashed))
            db.session.commit()
    # 启动 Flask 服务
    app.run(host='127.0.0.1', port=5000, debug=True)