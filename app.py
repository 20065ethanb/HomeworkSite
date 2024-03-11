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
    # selects stuff from database
    con = create_connection(database)
    cur = con.cursor()
    cur.execute(query, info)
    info = cur.fetchall()
    con.close()
    return info


def database_insert(database, query, info):
    # puts stuff into the database
    con = create_connection(database)
    cur = con.cursor()
    cur.execute(query, info)
    con.commit()
    con.close()


def database_delete(database, query, info):
    # deletes from database
    con = create_connection(database)
    cur = con.cursor()
    cur.execute(query, info)
    con.commit()
    con.close()


def create_connection(db_file):
    # create a database connection to the SQLite
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


def is_logged_in():
    # checks if your logged in
    if session.get('email') is None:
        return False
    else:
        return True


def user_info():
    # gets user info
    return session


@app.route('/')
def render_home():
    return render_template('home.html', logged_in=is_logged_in(), user_info=user_info())


@app.route('/login', methods=['POST', 'GET'])
def render_login():
    # checks if they're logged in, if so they're sent to homepage
    if is_logged_in():
        return redirect('/')

    # get your email and password
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()
        # selects your account info
        user_data = database_select(DATABASE, "SELECT id, fname, lname, password, role FROM users WHERE email= ?", (email,))[0]

        # checks account info to see if it is valid, error will occur if the email does not exist
        try:
            user_id = user_data[0]
            first_name = user_data[1]
            last_name = user_data[2]
            db_password = user_data[3]
            role = user_data[4]
        except IndexError:
            return redirect('/login?error=Invalid+username+or+password')

        # checks the password
        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")

        # creates the user's session
        session['email'] = email
        session['user_id'] = user_id
        session['firstname'] = first_name
        session['lastname'] = last_name
        session['role'] = role
        return redirect('/')

    return render_template('login.html')


@app.route('/logout')
def logout():
    # removes all info from the user's session
    [session.pop(key) for key in list(session.keys())]
    return redirect('/?message=See+you+next+time!')


@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    # checks if you're logged in, if you your send to the home page
    if is_logged_in():
        return redirect('/')

    # gets your signup information
    if request.method == 'POST':
        fname = request.form.get('fname').title().strip()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        role = request.form.get('role')

        # checks if your passwords are the same
        if password != password2:
            return redirect('/signup?error=Passwords+do+not+match')

        # make the minimum length 8 charters
        if len(password) < 8:
            return redirect('/signup?error=Passwords+must+be+at+least+8+characters')

        # changes the password for the database so the site's owner can't see it
        hashed_password = bcrypt.generate_password_hash(password)
        # insert the information unless email is already used
        try:
            database_insert(DATABASE, 'INSERT INTO users (fname, lname, email, password, role) VALUES (?, ?, ?, ?, ?)',(fname, lname, email, hashed_password, role))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')

        return redirect('/login')

    return render_template('signup.html')


@app.route('/submit', methods=['POST', 'GET'])
def render_submit():
    # if you are not logged in you are sent to the home page
    if not is_logged_in():
        return redirect('/')
    # gets the homework information
    if request.method == 'POST':
        title = request.form.get('title').strip()
        detail = request.form.get('detail').strip()
        student_id = session['user_id']
        submit_date = date.today()

        # puts the information into the database
        database_insert(DATABASE, 'INSERT INTO homework (title, details, studentid, date) VALUES (?, ?, ?, ?)',
                        (title, detail, student_id, submit_date))

        return redirect('/?message=Work+submitted!')

    return render_template('studentsubmit.html')


@app.route('/view/<student_id>')
def render_view(student_id):
    # makes sure that students can view their own work
    if user_info().get('role') != 'Student' or user_info().get('user_id') != int(student_id):
        return redirect('/')

    homework = database_select(DATABASE, 'SELECT id, title, details, studentid, date, score FROM homework WHERE studentid = ?', (student_id, ))

    return render_template('studentview.html', homework=homework)


@app.route('/mark', methods=['POST', 'GET'])
def render_mark():
    # only allows teachers to access this page
    if user_info().get('role') != 'Teacher':
        return redirect('/')

    # applies scores to the selected bit of work
    if request.method == 'POST':
        # using a for loop to be able to convert the dictionary to a string
        score = None
        work_id = None
        for item in request.form:
            score = request.form.get(item)
            work_id = item.split('score')[1]
            if work_id is int:
                break

        if (score is None) or (work_id is None):
            return redirect('/mark?error=Unable+to+mark+work')
        else:
            database_insert(DATABASE, 'UPDATE homework SET score = ? WHERE id = ?', (score, work_id, ))
            return redirect('/mark?message=Work+marked')

    homework = database_select(DATABASE, 'SELECT id, title, details, studentid, date, score FROM homework', ())
    users = database_select(DATABASE, 'SELECT id, fname, lname FROM users', ())

    # replaces student id's with the student's name
    homework_list = []
    for homework in homework:
        for user in users:
            if homework[3] == user[0]:
                homework_list.append((homework[0], homework[1], homework[2], user[1] + ' ' + user[2], homework[4], homework[5]))
                break

    return render_template('teachermark.html', homework=homework_list)


@app.route('/remove/<work_id>')
def remove(work_id):
    # prevents non teachers from deleting work
    if user_info().get('role') != 'Teacher':
        return redirect('/')

    database_delete(DATABASE, 'DELETE FROM homework WHERE id = ?', (work_id,))
    return redirect('/mark')


if __name__ == '__main__':
    app.run()
