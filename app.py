from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'  # 使用 SQLite 資料庫
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 關閉追蹤資料庫修改警告
db = SQLAlchemy(app)
api = Api(app)

# 資料庫模型
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Post {self.title}>'

# API 資源
class PostAPI(Resource):
    def get(self, post_id=None):
        if post_id:
            post = Post.query.get(post_id)
            if post:
                return jsonify({'id': post.id, 'title': post.title, 'author': post.author, 'content': post.content})
            return {'message': 'Post not found'}, 404
        posts = Post.query.all()
        return jsonify([{'id': post.id, 'title': post.title, 'author': post.author, 'content': post.content} for post in posts])

    def post(self):
        data = request.get_json()
        new_post = Post(title=data['title'], author=data['author'], content=data['content'])
        try:
            db.session.add(new_post)
            db.session.commit()
            return jsonify({'message': 'Post created', 'id': new_post.id}), 201
        except SQLAlchemyError as e:
            db.session.rollback()
            return {'message': str(e)}, 400

    def put(self, post_id):
        post = Post.query.get(post_id)
        if not post:
            return {'message': 'Post not found'}, 404

        data = request.get_json()
        post.title = data.get('title', post.title)
        post.author = data.get('author', post.author)
        post.content = data.get('content', post.content)

        try:
            db.session.commit()
            return jsonify({'message': 'Post updated'})
        except SQLAlchemyError as e:
            db.session.rollback()
            return {'message': str(e)}, 400

    def delete(self, post_id):
        post = Post.query.get(post_id)
        if not post:
            return {'message': 'Post not found'}, 404

        try:
            db.session.delete(post)
            db.session.commit()
            return {'message': 'Post deleted'}
        except SQLAlchemyError as e:
            db.session.rollback()
            return {'message': str(e)}, 400

# API 路由設定
api.add_resource(PostAPI, '/api/posts', '/api/posts/<int:post_id>')

@app.before_first_request
def create_tables():
    db.create_all()

# 前端路由
@app.route('/')
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)

@app.route('/post/<int:post_id>')
def show_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('show_post.html', post=post)

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        content = request.form['content']
        new_post = Post(title=title, author=author, content=content)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create_post.html')

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        post.title = request.form['title']
        post.author = request.form['author']
        post.content = request.form['content']
        db.session.commit()
        return redirect(url_for('show_post', post_id=post.id))
    return render_template('edit_post.html', post=post)

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)