
from flask import Flask, render_template, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, TextAreaField, SelectMultipleField, StringField
from wtforms import PasswordField, EmailField, URLField
from wtforms.validators import InputRequired, Email, Length, EqualTo
import os
from medium import Client
import requests
import json
from substack import Api
from substack.post import Post

# https://github.com/hidevscommunity/blog_post/tree/dev
# dckr_pat__KXzY_5Hp2UHGxkgr1KcAdmnnCg

mutation = """
mutation PublishPost($input: PublishPostInput!) {
  publishPost(input: $input) {
    post{
     id
     slug
    }
  }
}
"""
# output mein jo chahiye wo milega
# post{slug}  slug apan ko title dega jiski help se url banayenge


app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'  # GET and POST ko use ke liye lagana jaruri hai


class UploadForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    title = TextAreaField("Title", validators=[InputRequired()])
    platforms = SelectMultipleField("Choose Platforms  [ctrl+click to select multiple platforms]",
                                    choices=[('med', 'Medium'), ('dev', 'DevCommunity'), ('hn', 'HashNode'),
                                             ('ss', 'SubStack')],
                                    validators=[InputRequired()])
    # Medium frontend pe dikhayi dega  med backend mein use aayega
    image_url = URLField(label="Upload image url")
    submit = SubmitField("Submit")


class RegisterForm(FlaskForm):
    username = StringField(label='User Name:', validators=[Length(min=2, max=30), InputRequired()])
    email_address = EmailField(label='Email Address', validators=[Email(), InputRequired()])
    password1 = PasswordField(label='password:', validators=[Length(min=6), InputRequired()])
    password2 = PasswordField(label='confirm password:', validators=[EqualTo('password1'), InputRequired()])
    submit = SubmitField(label='Create account')


class DetailsForm(FlaskForm):
    dev_api = StringField(label="Dev.to API Key", validators=[InputRequired()])
    medium_access_key = StringField(label="Medium Integration Token", validators=[InputRequired()])
    hashnode_api = StringField(label="HashNode Access Key", validators=[InputRequired()])
    hashnode_publication_id = StringField(label="Hashnode Publication ID", validators=[InputRequired()])
    substack_email = EmailField(label='SubStack Email Address', validators=[InputRequired()])
    substack_password = PasswordField(label="Substack password", validators=[InputRequired()])
    substack_publication_url = StringField(label='Substack Publication URL', validators=[InputRequired()])
    substack_user_id = StringField(label="User ID of SubStack", validators=[InputRequired()])
    submit = SubmitField(label='Create Account')


class LoginForm(FlaskForm):
    username = StringField(label="Enter username", validators=[InputRequired()])
    password = PasswordField(label="Enter Password", validators=[InputRequired()])
    submit = SubmitField(label='Log-in')


# dev.to
def create_post(title, content, dev_token, image_url):
    # dev.to
    api_key = dev_token  # api ko access karne ki key
    url_site = "https://dev.to/api/articles"  # api ka endpoint post karne ke liye

    headers = {
        "content-type": "application/json",  # header of HTTP batayega ki data json format mein hai
        "api-key": api_key  # client server connection ko complete karne ke liye
    }  # server ko access karne k password ek tareeke ka

    if image_url:
        data = {
            "article": {
                "title": title,
                "body_markdown": content,
                "published": False,  # publish immediately ->True
                "main_image": image_url
            }
        }
    else:
        data = {
            "article": {
                "title": title,
                "body_markdown": content,
                "published": False,  # publish immediately ->True
            }
        }
    response = requests.post(url=url_site, json=data, headers=headers)
    response.raise_for_status()  # exception raise karega
    # return response.json()["url"]  # dictionary ka element chahiye url


# medium
def publish_post_md(title, x, token):
    # medium
    # TOKEN = '257c07e5d5fcda561f1188087769b63275c597a3836b8141efcb9e9b16d5f1fd8'
    client = Client(access_token=token)
    user = client.get_current_user()  # dictionary return hogi
    # print(user)
    client.create_post(user_id=user["id"], title=title, content=x, content_format="markdown", publish_status='draft')


def upload_on_hashnode(title_article, data, hashnode_token, hashnode_publication_id, image_url):
    # hashnode
    access_token = hashnode_token
    hashnode_url = "https://gql.hashnode.com/"

    hashnode_header = {
        "Content-Type": "application/json",  # header of HTTP batayega ki data json format mein hai
        "Authorization": access_token  # client server connection ko complete karne ke liye
    }  # server ko access karne k password ek tareeke ka

    if image_url:
        variables = {
            "input": {
                "title": title_article,
                "contentMarkdown": data,
                "publicationId": hashnode_publication_id,
                "tags": [],
                "coverImageURL": image_url
            }
        }
    else:
        variables = {
            "input": {
                "title": title_article,
                "contentMarkdown": data,
                "publicationId": hashnode_publication_id,
                "tags": []
            }
        }

    hashnode_data = {
        "query": mutation,
        "variables": variables
    }  # json.dumps() ->python data ko convert karta hai
    response = requests.post(hashnode_url, headers=hashnode_header, data=json.dumps(hashnode_data))  # json mein
    response.raise_for_status()


def upload_substack(title, data, substack_email, substack_password, substack_publication_url, substack_user_id):
    api = Api(
        email=substack_email,
        password=substack_password,
        publication_url=substack_publication_url
    )
    post = Post(
        title=title,
        subtitle="",
        user_id=substack_user_id
    )
    post.add({'type': 'paragraph', 'content': data})
    api.post_draft(post.get_draft())


@app.route('/', methods=['GET', 'POST'])
def base():
    return render_template('index.html')


@app.route('/details', methods=['GET', 'POST'])
def details():
    form = DetailsForm()
    if form.validate_on_submit():
        dev_token = form.dev_api.data
        med_token = form.medium_access_key.data
        hashnode_key = form.hashnode_api.data
        substack_email = form.substack_email.data
        substack_password = form.substack_password.data
        substack_publication_url = form.substack_publication_url.data
        substack_user_id = form.substack_user_id.data
        hashnode_publication_id = form.hashnode_publication_id.data

        with open("database.json", "r") as file:
            data = json.load(file)

        demo = {
            "dev_token": dev_token,
            "med_token": med_token,
            "hashnode_key": hashnode_key,
            "substack_email": substack_email,
            "substack_password": substack_password,
            "substack_publication_url": substack_publication_url,
            "substack_user_id": substack_user_id,
            "hashnode_publication_id": hashnode_publication_id
        }
        data[session['username']].update(demo)
        with open("database.json", "w") as file:
            json.dump(data, file, indent=4)
        return redirect('home')
    return render_template('details.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email_address = form.email_address.data
        password = form.password1.data
        with open("database.json", "r") as file:
            data = json.load(file)

        if username in data:
            return "Username already exists. Please choose a different one."

        data[username] = {
            "email_address": email_address,
            "password": password
        }
        session['username'] = username
        with open("database.json", "w") as file:
            json.dump(data, file, indent=4)
        return redirect(url_for('details'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        with open("database.json", "r") as file:
            data = json.load(file)
        if username in data and data[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return "Login credentials wrong"
    return render_template('login.html', form=form)


@app.route('/home', methods=['GET', 'POST'])
def home():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = file.filename
        title = form.title.data
        blog_site = form.platforms.data
        image_url = form.image_url.data
        if filename and title:
            file_ext = os.path.splitext(filename)[1]
            if file_ext.lower() in ['.md']:
                content = file.read().decode('utf-8')  # medium-no need    dev.to- needed
                # print(blog_site)x
                with open("database.json", "r") as file:
                    data = json.load(file)
                if 'dev' in blog_site:
                    dev_token = data[session['username']]['dev_token']
                    create_post(title, content, dev_token, image_url)
                if 'med' in blog_site:
                    med_token = data[session['username']]['med_token']
                    publish_post_md(title, content, med_token)
                if 'hn' in blog_site:
                    hashnode_token = data[session['username']]['hashnode_key']
                    hashnode_publication_id = data[session['username']]['hashnode_publication_id']
                    upload_on_hashnode(title, content, hashnode_token, hashnode_publication_id, image_url)
                if 'ss' in blog_site:
                    substack_email = data[session['username']]['substack_email']
                    substack_password = data[session['username']]['substack_password']
                    substack_publication_url = data[session['username']]['substack_publication_url']
                    substack_user_id = data[session['username']]['substack_user_id']
                    upload_substack(title, content, substack_email, substack_password, substack_publication_url
                                         , substack_user_id)
                return "Post Added to Draft successful"
            else:
                return "Invalid file extension. Only .md files are allowed."
    return render_template('base.html', form=form)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

# docker build -t flask:latest .
# docker run -i -p 5000:5000 -d flask
# docker ps
# docker logs CONTAINER_ID
