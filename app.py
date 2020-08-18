from flask import Flask, render_template, request, flash, redirect,url_for,session,logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

Articles = Articles()

#config mysql
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='myflaskapp'
app.config['MYSQL_CURSORCLASS']='DictCursor'

#initialize mysql
mysql=MySQL(app)

# Homepage
@app.route('/')
def hello():
    return render_template('index.html')

# About Page
@app.route('/about')
def about():
    return render_template('about.html')

# All Article
@app.route('/articles')
def articles():
    #Create Cursor
    cur=mysql.connection.cursor()
    #Get Articles
    result=cur.execute("SELECT * FROM articles")
    articles=cur.fetchall()
    if result>0:
        return render_template(
        'articles.html', articles=articles
    )
    else:
        msg='No Articles Found'
        return render_template(
        'articles.html',msg=msg
    )
    # close connection
    cur.close()

# Single Article
@app.route('/article/<string:id>')
def article(id):
    #Create Cursor
    cur=mysql.connection.cursor()
    #Get Articles
    result=cur.execute("SELECT * FROM articles where id=%s",[id])
    article=cur.fetchone()
    return render_template('article.html',article=article)

# Login
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        #get form fields
        username=request.form['username']
        password_candidate=request.form['password']

        # Create a cursor
        cur=mysql.connection.cursor()
        # Get user by username
        result=cur.execute("SELECT * from users where username =%s",[username])
        if result>0:
            # Get stored hash
            data=cur.fetchone()
            password=data['password']

            #compare the passwords
            if sha256_crypt.verify(password_candidate,password):
                app.logger.info('PASSWORD MATCHED')
                session['logged_in']=True
                session['username']=username
                flash('You are now logged in','success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html',error=error)
        else:
            error = 'Username not found'
            return render_template('login.html',error=error)
    return render_template('login.html')

# Registration
class RegisterForm(Form):
    name=StringField('Name', [validators.Length(min=1,max=50)])
    username = StringField('Username',[validators.Length(min=1,max=26)])
    email=StringField('Email',[validators.Length(min=6,max=50)])
    password=PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm',message='Passwords do not match')
    ])
    confirm=PasswordField('Confirm Password')

# Registration
@app.route('/register',methods=['GET','POST'])
def register():
    form=RegisterForm(request.form)
    if request.method=='POST' and form.validate():
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))

        #Create Cursor
        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO users(name,email,password,username) VALUES(%s, %s, %s, %s)", (name,email,password,username))

        #commit to DB
        mysql.connection.commit()

        #close connnection
        cur.close()
        flash('You are now registered and can now log in','success')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)


# check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('Unauthorized, Please Login','danger')
            return redirect(url_for('login'))
    return wrap

# Dashboard
@app.route('/Dashboard')
@is_logged_in
def dashboard():
    #Create Cursor
    cur=mysql.connection.cursor()
    #Get Articles
    result=cur.execute("SELECT * FROM articles")
    articles=cur.fetchall()
    if result>0:
        return render_template(
        'dashboard.html', articles=articles
    )
    else:
        msg='No Articles Found'
        return render_template(
        'dashboard.html',msg=msg
    )
    # close connection
    cur.close()



# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You have been Logged out','success')
    return redirect(url_for('login'))

# Registration
class ArticleForm(Form):
    title=StringField('Title', [validators.Length(min=1,max=200)])
    body= TextAreaField('Body',[validators.Length(min=30)])

# Add Article
@app.route('/add_article',methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method=='POST' and form.validate():
        title=form.title.data
        body=form.body.data

        # Create Cursor
        cur=mysql.connection.cursor()
        # Execute
        cur.execute("INSERT INTO articles(title,body,author) VALUES(%s,%s,%s)",(title,body,session['username']))
        # Commit
        mysql.connection.commit()
        #close
        cur.close()
        flash('Article Created','success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_article.html', form=form)

# Edit Article
@app.route('/edit_article/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()
    # Get the article by id
    result = cur.execute("SELECT * FROM articles where id =%s",[id])
    article=cur.fetchone()
    #Get Form
    form = ArticleForm(request.form)
    #Populate fields
    form.title.data=article['title']
    form.body.data=article['body']
    if request.method=='POST' and form.validate():
        title=request.form['title']
        body=request.form['body']

        # Create Cursor
        cur=mysql.connection.cursor()
        # Execute
        cur.execute("UPDATE articles SET title=%s,body=%s Where id=%s",(title,body,[id]))
        # Commit
        mysql.connection.commit()
        #close
        cur.close()
        flash('Article Updated','success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_article.html', form=form)


# Delete article
@app.route('/delete_article/<string:id>',methods=['POST'])
@is_logged_in
def delete_article(id):
    #create cursor
    cur=mysql.connection.cursor()
    #execute
    cur.execute("DELETE FROM articles where id=%s",[id])
    #commit
    mysql.connection.commit()
    #close connection
    cur.close()
    flash('Article Deleted','success')
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.secret_key='secret123'
    app.run(debug=True)
