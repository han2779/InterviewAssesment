from flask import Flask
from flask_cors import CORS
from routes.report_route import report_bp
from routes.resume_route import resume_bp
from routes.answer_route import answer_bp
from routes.suggestion_route import suggestion_bp

app = Flask(__name__)
# 允许所有域名访问所有路由（默认行为）
CORS(app, resources={r"/*": {"origins": "*"}})

app.register_blueprint(report_bp, url_prefix='/interview')
app.register_blueprint(resume_bp, url_prefix='/select_of_resume')
app.register_blueprint(answer_bp, url_prefix='/select_of_answer')
app.register_blueprint(suggestion_bp, url_prefix='/me')

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=18081, debug=True)