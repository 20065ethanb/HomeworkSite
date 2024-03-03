from flask import Flask, render_template, redirect, request, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt

DATABASE = "C:/Users/GGPC/PycharmProjects/HomeworkSite/homework.db" # Desktop
# DATABASE = "C:/Users/ethan/PycharmProjects/SmileCafe/smile.db"  # Laptop

app = Flask(__name__)


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


@app.route('/', methods=['POST', 'GET'])
def render_login():
    return render_template('login.html')


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
            return redirect('\signup?error=Passwords+do+not+match')

        if len(password) < 8:
            return redirect('\signup?error=Passwords+must+be+at+least+8+characters')

        con = create_connection(DATABASE)
        query = 'INSERT INTO users (fname, lname, email, password, role) VALUES (?, ?, ?, ?, ?)'
        cur = con.cursor()

        try:
            cur.execute(query, (fname, lname, email, password, role))
        except sqlite3.IntegrityError:
            con.close()
            return redirect('\signup?error=Email+is+already+used')

        con.commit()
        con.close()

        return redirect('/')

    return render_template('signup.html')

# Sign in for student and teacher (first name, last name, role, email, id number)
# Students should have a page with only their homework where they can submit homework
# Only teachers can view all students homework
# Only teachers should be able to add, remove and mark work (id, title, description, time, student id, work, isdone, mark)


if __name__ == '__main__':
    app.run()
