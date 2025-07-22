from flask import Flask
from flask_cors import CORS
import logging
from routes import report_route
from routes.report_route import report_bp
from routes.resume_route import resume_bp
from routes.suggestion_route import suggestion_bp
from routes.next_route import next_bp
from routes.first_route import first_bp
from routes.frame_route import frame_bp

# 设置日志级别为DEBUG，以便查看所有级别的日志信息
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
# 允许所有域名访问所有路由（默认行为）
CORS(app, supports_credentials=True)

app.register_blueprint(report_bp, url_prefix='/interview')
app.register_blueprint(resume_bp, url_prefix='/select_of_resume')
app.register_blueprint(suggestion_bp, url_prefix='/me')
app.register_blueprint(next_bp, url_prefix='/interview')
app.register_blueprint(first_bp, url_prefix='/interview')
app.register_blueprint(frame_bp, url_prefix='/interview')

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=18081, debug=True)