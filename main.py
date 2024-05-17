from sqlite3 import IntegrityError
from flask import Flask, jsonify, render_template, redirect, request, url_for
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from flask_ckeditor import CKEditor
from wtforms.validators import DataRequired, URL
from forms.post_form import PostForm
from datetime import date
from dotenv import load_dotenv
from icecream import ic
from bleach import clean
from os import environ
'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''
# ----------- Load Environment Variables/Secrets -----------
load_dotenv()

api_key = environ.get('SECRET_KEY')
if api_key:
    print(f"Your API key is: {api_key}")
else:
    print("API key not found in .env file")

# ----------- Start of Flask Project -----------
app = Flask(__name__)
app.config['SECRET_KEY'] = api_key
ckeditor = CKEditor(app)
Bootstrap5(app)

# ----------- CREATE DATABASE -----------
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# ----------- CONFIGURE TABLE -----------
class BlogPost(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()


# ----------- ROUTES -----------
@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)

@app.route('/post/<int:post_id>')
def show_post(post_id):
    requested_post = BlogPost.query.get_or_404(post_id, description='ID Not Found in Database.')
    return render_template("post.html", post=requested_post)


@app.route('/new-post', methods=['GET', 'POST'])
def add_post():
    form = PostForm()
    if form.validate_on_submit():
        timestamp = date.today()
        # Sanitazion is Needed Here (Project Only)
        new_post = BlogPost(
            title= form.title.data,  
            subtitle= form.subtitle.data,  
            author= form.author.data,
            img_url= form.img_url.data,
            date=timestamp.strftime("%m %d, %Y"),
            body= form.body.data
        )

        try:
            db.session.add(new_post)
            db.session.commit()
            db.session.refresh()
            print("Post Added to DB Successfully.")
            
        except(IntegrityError, Exception) as e:
            # Handle specific integrity errors (e.g., duplicate key)
            if "duplicate key value violates unique constraint" in str(e):
                return jsonify(error="Cafe with that name already exists."), 409  # 
            else:
                # Handle other integrity errors more generally
                return jsonify(error="An error occurred while adding the cafe."), 500  # Internal Server Error
            
        finally:
            # Optional: Close DB connection or perform cleanup actions
            db.session.close()
            return redirect(url_for("get_all_posts"))
            
    return render_template("make-post.html", form=form)


# TODO: edit_post() to change an existing blog post
@app.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id, description='ID Not Found in Database.')
    edit_form = PostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.author = edit_form.author.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        
        try:
            db.session.commit()
            print("Post Updated Successfully.")
            return redirect(url_for("show_post", post_id=post.id))

        except IntegrityError as e:
            db.session.rollback()
            if "duplicate key value violates unique constraint" in str(e):
                return jsonify(error="Blog post with that title already exists."), 409
            else:
                return jsonify(error="An error occurred while updating the blog post."), 500

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

        finally:
            print("Closing DB session.")
            db.session.close()

    return render_template("make-post.html", form=edit_form, is_edit=True, post=post)

@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

# Below is the code from previous lessons. No changes needed.
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True, port=5003)
