from flask import Flask, render_template, redirect, request, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt

DATABASE = "C:/Users/GGPC/PycharmProjects/HomeworkSite/homework.db" # Desktop
# DATABASE = "C:/Users/ethan/PycharmProjects/HomeworkSite/homework.db"  # Laptop

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "Suffering"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


def is_logged_in():
    if session.get('email') is None:
        print('not logged in')
        return False
    else:
        print('logged in')
        return True


def get_role():
    return session.get('role')


@app.route('/')
def render_home():
    return render_template('home.html', logged_in=is_logged_in(), role=get_role())


@app.route('/login', methods=['POST', 'GET'])
def render_login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()
        query = """SELECT id, fname, password, role FROM users WHERE email= ?"""
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchone()
        con.close()
        try:
            user_id = user_data[0]
            first_name = user_data[1]
            db_password = user_data[2]
            role = user_data[3]
        except IndexError:
            return redirect('/login?error=Invalid+username+or+password')

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")

        session['email'] = email
        session['user_id'] = user_id
        session['firstname'] = first_name
        session['role'] = role
        return redirect('/')

    return render_template('login.html')


@app.route('/logout')
def logout():
    [session.pop(key) for key in list(session.keys())]
    return redirect('/?message=See+you+next+time!')


@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    if request.method == 'POST':
        fname = request.form.get('fname').title().strip()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        role = request.form.get('signup').split()[1]

        if password != password2:
            return redirect('/signup?error=Passwords+do+not+match')

        if len(password) < 8:
            return redirect('/signup?error=Passwords+must+be+at+least+8+characters')

        hashed_password = bcrypt.generate_password_hash(password)
        con = create_connection(DATABASE)
        query = 'INSERT INTO users (fname, lname, email, password, role) VALUES (?, ?, ?, ?, ?)'
        cur = con.cursor()

        try:
            cur.execute(query, (fname, lname, email, hashed_password, role))
        except sqlite3.IntegrityError:
            con.close()
            return redirect('/signup?error=Email+is+already+used')

        con.commit()
        con.close()

        return redirect('/login')

    return render_template('signup.html')

# Sign in for student and teacher
# Students should have a page with only their homework where they can submit homework
# Only teachers can view all students homework
# Only teachers should be able to add, remove and mark work


if __name__ == '__main__':
    app.run()
