from flask import Flask, render_template, redirect, request, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import date

DATABASE = "C:/Users/GGPC/PycharmProjects/HomeworkSite/homework.db" # Desktop
# DATABASE = "C:/Users/ethan/PycharmProjects/HomeworkSite/homework.db"  # Laptop

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "Suffering"


def database_select(database, query, info):
    con = create_connection(database)
    cur = con.cursor()
    cur.execute(query, info)
    info = cur.fetchall()
    con.close()
    return info


def database_insert(database, query, info):
    con = create_connection(database)
    cur = con.cursor()
    cur.execute(query, info)
    con.commit()
    con.close()


def database_delete(database, query, info):
    con = create_connection(database)
    cur = con.cursor()
    cur.execute(query, info)
    con.commit()
    con.close()


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


def is_logged_in():
    if session.get('email') is None:
        return False
    else:
        return True


def user_info():
    return session


@app.route('/')
def render_home():
    return render_template('home.html', logged_in=is_logged_in(), user_info=user_info())


@app.route('/login', methods=['POST', 'GET'])
def render_login():
    if is_logged_in():
        return redirect('/')
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        user_data = database_select(DATABASE, "SELECT id, fname, lname, password, role FROM users WHERE email= ?", (email,))[0]

        try:
            user_id = user_data[0]
            first_name = user_data[1]
            last_name = user_data[2]
            db_password = user_data[3]
            role = user_data[4]
        except IndexError:
            return redirect('/login?error=Invalid+username+or+password')

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")

        session['email'] = email
        session['user_id'] = user_id
        session['firstname'] = first_name
        session['lastname'] = last_name
        session['role'] = role
        return redirect('/')

    return render_template('login.html')


@app.route('/logout')
def logout():
    [session.pop(key) for key in list(session.keys())]
    return redirect('/?message=See+you+next+time!')


@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    if is_logged_in():
        return redirect('/')
    if request.method == 'POST':
        fname = request.form.get('fname').title().strip()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        role = request.form.get('role')

        if password != password2:
            return redirect('/signup?error=Passwords+do+not+match')

        if len(password) < 8:
            return redirect('/signup?error=Passwords+must+be+at+least+8+characters')

        hashed_password = bcrypt.generate_password_hash(password)
        try:
            database_insert(DATABASE, 'INSERT INTO users (fname, lname, email, password, role) VALUES (?, ?, ?, ?, ?)',(fname, lname, email, hashed_password, role))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')

        return redirect('/login')

    return render_template('signup.html')


@app.route('/submit', methods=['POST', 'GET'])
def render_submit():
    if not is_logged_in():
        return redirect('/')
    if request.method == 'POST':
        title = request.form.get('title').strip()
        detail = request.form.get('detail').strip()
        student_id = session['user_id']
        submit_date = date.today()

        database_insert(DATABASE, 'INSERT INTO homework (title, details, studentid, date) VALUES (?, ?, ?, ?)',
                        (title, detail, student_id, submit_date))

        return redirect('/?message=Work+submitted!')

    return render_template('studentsubmit.html')


@app.route('/view')
def render_view():
    if user_info().get('role') != 'Teacher':
        return redirect('/')

    homework = database_select(DATABASE, 'SELECT id, title, details, studentid, date FROM homework', ())
    users = database_select(DATABASE, 'SELECT id, fname, lname FROM users', ())

    homework_list = []
    for homework in homework:
        for user in users:
            if homework[3] == user[0]:
                homework_list.append((homework[0], homework[1], homework[2], user[1] + ' ' + user[2], homework[4]))
                break

    return render_template('teachermark.html', homework=homework_list)


@app.route('/remove/<work_id>')
def remove(work_id):
    if user_info().get('role') != 'Teacher':
        return redirect('/')

    database_delete(DATABASE, 'DELETE FROM homework WHERE id = ?', (work_id,))
    return redirect('/view')


if __name__ == '__main__':
    app.run()
