from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


# Istifadeci qeydiyyati
class RegisterForm(Form):
    name = StringField("Ad Soyad",validators=[validators.Length(min = 4, max = 25)])
    username = StringField("Istifadeci adi",validators=[validators.Length(min = 4, max = 25)])
    email = StringField("e-mail",validators=[validators.Email(message="E-mail adresiniz yanlisdir")])
    password = PasswordField("Sifreniz", validators=[
        validators.DataRequired(message="Parol teyin edin"),
        validators.EqualTo(fieldname = "confirm",message="Parolunuz uygun gelmir")
        ])
    confirm = PasswordField("Shifre dogrula")
app = Flask(__name__)
app.secret_key = "ybblog"

class LoginForm(Form):
    username = StringField("Istifadeci adiniz")
    password = PasswordField("Sifreniz")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sehifeni gire bilmek ucun daxil olmalisiniz","danger")
            return redirect(url_for("login"))
    return decorated_function
app.config["MYSQL_HOST"]= "localhost"
app.config["MYSQL_USER"]= "root"
app.config["MYSQL_PASSWORD"]= ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

@app.route("/")
def layout():
    a = [
        {"id": 1, "ad": "Alakbar", "familya":"Heyderov"},
        {"id": 2, "ad": "Ali", "familya":"Heyder"},
        {"id": 3, "ad": "Ahmed", "familya":"Aliyev"}]
    return render_template("index.html", a = a)
@app.route("/login", methods = ["GET","POST"])
def login():
    form =LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "Select * From users where username = %s"

        result = cursor.execute(sorgu, (username,))
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered, real_password):
                flash("Daxil olundu","success")
                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("layout"))
            else:
                flash("Yanlis Parol","danger")
                return redirect(url_for("login"))
        else:
            flash("Bele istifadeci bazada movcud deyil","danger")
            return redirect(url_for("login"))

    
    return render_template("login.html", form = form)
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles"
    result = cursor.execute(sorgu)
    if result >0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles = articles)
    else:
        return render_template("articles.html")
@app.route("/register",methods=["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():

        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()

        flash("Qeydiyyat tamamlandi","success")


        return redirect(url_for("login"))
    else:
        return render_template("register.html", form = form)
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("layout"))


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))
    if result  >0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles = articles)
    else:
        return render_template("dashboard.html")

#meqale silmek
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))

    if result  >0:
        sorgu2 = "Delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("Sizin bura giris icazeniz yoxdu","danger")
        return redirect(url_for("layout"))
    
#deyisiklik etmek
@app.route("/edit/<string:id>", methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))
        if result == 0:
            flash("Bele meqale yoxdu","danger")
            return redirect(url_for("layout"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html", form = form)
    else:
        #post 
        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data
        sorgu2 = "Update articles Set title = %s, content = %s where id = %s"

        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connection.commit()

        flash("Deyisiklik ugurla qeyde alindi","success")
        return redirect(url_for("dashboard"))
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select *From articles where id = %s"
    result = cursor.execute(sorgu,(id,))

    if result >0:
        article = cursor.fetchone()
        return render_template("article.html", article = article)
    else:
        return render_template("article.html")



@app.route("/addarticel", methods = ["GET","POST"])
@login_required
def addarticel():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s) "

        cursor.execute(sorgu,(title, session["username"],content))
        mysql.connection.commit()
        cursor.close()

        flash("Meqale elave olundu","success")
        return redirect(url_for("dashboard"))
    return render_template("addarticel.html", form = form)
#MEQALE FORM

class ArticleForm(Form):
    title = StringField("Meqale basligi",validators=[validators.Length(min = 5, max = 100)])
    content = TextAreaField("Meqale", validators= [validators.Length(min = 50)])
#AXTARIS
@app.route("/search", methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("layout"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where title like '%"+ keyword +"%' "

        result = cursor.execute(sorgu)
        if result == 0:
            flash("Axtarilan kelimeye uygun hec bir meqale yoxdur...","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html", articles = articles)

if __name__ == "__main__":
    app.run(debug=True)