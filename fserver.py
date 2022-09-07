# System for MRI_flow analysis
#     python test.py runserver -p 5005 -d
#                       port 5005, debug mode
#
#     /insert_patient
#     /insert_session
from flask import Flask, render_template, session, redirect, request, url_for
#from flask_moment import Moment
#from flask_script import Manager
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, DateField, DateTimeField, HiddenField, BooleanField
from wtforms import TextAreaField, SelectField, SelectMultipleField, IntegerField, SubmitField
from wtforms.validators import Required, Length
import psycopg2
import datetime

app = Flask(__name__)
bootstrap = Bootstrap(app)
#manager = Manager(app)
#moment = Moment(app)

app.config['SECRET_KEY'] = 'penfield'

class PatientForm(FlaskForm):
    patient_id = StringField('patient_id', validators=[Length(min=8, max=8)])
    kanji_name = StringField('kanji_name')
    age = IntegerField('age')
    sex = SelectField('sex', choices =[('m', 'm'), ('f', 'f')])
    birthdate = StringField('birthdate')
    study_type = SelectField('type', choices=[('patient', 'patient'), ('volunteer', 'volunteer')])
    hospital = SelectField('hospital', choices=[('Tokai', 'Tokai'), ('Kawagoe', 'Kawagoe')])
    op_date = StringField('op_date')
    syrinx = BooleanField('syrinx')
    submit = SubmitField('Submit')

class SubmitForm(FlaskForm):
    submit = SubmitField('Submit')

class SessionForm(FlaskForm):
    serial_id = StringField('serial_id')
    pre_post = SelectField('pre_post', choices = [('pre', 'pre'), ('post', 'post')])
    #timing = IntegerField('timing')
    session_date = StringField('session_date')
    venc= IntegerField('venc')
    submit = SubmitField('Submit')

@app.route('/')
def index():
    return '<h1>Hello World!</h1>'

@app.route('/list_patients')
def list_patients():
    try:
        conn = psycopg2.connect('dbname=MRI_flow host=localhost')
        cur = conn.cursor()
    except:
        return render_template("message.html", message="database connection error!")
    header=['serial_id', 'patient_id', 'name', 'age', 'syrinx', 'birthdate', 'hospital', 'type', 'op_date' ]
    sql = "SELECT serial_id, patient_id, kanji_name, age, syrinx, birthdate, hospital, type, op_date FROM patients "\
            "ORDER BY serial_id"
    result = cur.execute(sql)
    result_dict_list = []
    for row in cur:
        result_dict_list.append({'serial_id': row[0], 'patient_id': row[1], 'name': row[2], 'age': row[3], 'syrinx': row[4],
            'birthdate': row[5], 'hospital': row[6], 'type': row[7], 'op_date': row[8]})
    return render_template("display_dictionary.html", title = "患者リスト", header=header, result=result_dict_list)
    
@app.route('/insert_patient', methods=['GET', 'POST'])
def insert_patient():
    form = PatientForm()
    if form.validate_on_submit():
        patient_id = form.patient_id.data
        kanji_name = form.kanji_name.data
        age = form.age.data
        sex = form.sex.data
        birthdate = form.birthdate.data
        study_type = form.study_type.data
        hospital = form.hospital.data
        op_date = form.op_date.data
        syrinx = form.syrinx.data
        header = ['patient_id', 'kanji_name', 'age', 'birthdate', 'type', 'hospital', 'op_date', 'syrinx']
        patient = {'patient_id': patient_id, 'kanji_name': kanji_name, 'age': age, 'sex': sex, 'birthdate': birthdate,
                'type': study_type, 'hospital': hospital, 'op_date': op_date, 'syrinx': syrinx}
        session['header'] = header
        session['patient'] = patient
        return redirect(url_for('confirm_patient'))
    return render_template("patient_form.html", form=form)
    
@app.route('/confirm_patient', methods=["GET", "POST"])
def confirm_patient():
    form = SubmitForm()
    url = url_for('confirm_patient')
    header = session['header']
    patient = session['patient']
    result = [patient]
    if form.validate_on_submit():
        try:
            conn = psycopg2.connect("dbname=MRI_flow host=localhost")
            cur = conn.cursor()
        except:
            return render_template("message.html", message="Database Connection Error")
        sql = "INSERT INTO patients (patient_id, kanji_name, age, sex, birthdate, type, hospital, op_date, syrinx)"\
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        value_tuple = (patient["patient_id"], patient["kanji_name"],
                patient["age"], patient["sex"],
                patient["birthdate"] if patient["birthdate"] else None,
                patient["type"],
                patient["hospital"],
                patient["op_date"] if patient["op_date"] else None,
                patient["syrinx"])
        cur.execute(sql, value_tuple)
        conn.commit()
        cur.close()
        conn.close()
        return render_template("successful_insertion.html")

    return render_template("confirm_patient_form.html", form=form, header=header, result=result)
     
@app.route('/list_sessions')
def list_sessions():
    "List all the data in sessions table"
    try:
        conn = psycopg2.connect('dbname=MRI_flow host=localhost')
        cur = conn.cursor()
    except:
        return render_template("message.html", message="database connection error!")
    header=['session_id', 'serial_id', 'patient_id', 'name', 'pre_post', 'syrinx', 'session_date', 'venc']
    sql = "SELECT s.session_id, s.serial_id, p.patient_id, p.kanji_name, "\
            "s.pre_post, p.syrinx, s.session_date, s.venc "\
            "FROM sessions s "\
            "INNER JOIN patients p ON s.serial_id = p.serial_id"
    cur.execute(sql)
    result = []
    for row in cur:
        result.append(dict(zip(header, row)))
    cur.close()
    conn.close()
    return render_template("display_dictionary.html", title="セッション・リスト", header=header, result=result)

@app.route('/insert_session', methods=['GET', 'POST'])
def insert_session():
    "Insert a session into sessions table"
    form = SessionForm()
    if form.validate_on_submit():
        serial_id = form.serial_id.data
        pre_post = form.pre_post.data
        session_date = form.session_date.data
        venc = form.venc.data
        try:
            conn = psycopg2.connect('dbname=MRI_flow host=localhost')
            cur = conn.cursor()
        except:
            return render_template("message.html", message="database connection error!")
        cur.execute("SELECT kanji_name FROM patients WHERE serial_id = %s", (serial_id,))
        kanji_name = cur.fetchone()[0]
        header = ['serial_id', 'kanji_name', 'pre_post', 'session_date', 'venc']
        session_data = {'serial_id': serial_id, 'kanji_name': kanji_name, 'pre_post': pre_post, 'session_date': session_date, 'venc': venc}
        session['header'] = header
        session['session_data'] = session_data
        cur.close()
        conn.close()
        return redirect(url_for('confirm_session'))
    return render_template("session_form.html", form=form)
    
@app.route('/confirm_session', methods=['GET', 'POST'])
def confirm_session():
    form = SubmitForm()
    url = url_for('confirm_session')
    header = session['header']
    session_data = session['session_data']
    result = [session_data]
    if form.validate_on_submit():
        try:
            conn = psycopg2.connect("dbname=MRI_flow host=localhost")
            cur = conn.cursor()
        except:
            return render_template("message.html", message="Database Connection Error")
        sql = "INSERT INTO sessions (serial_id, pre_post, session_date, venc) "\
                "VALUES (%s, %s, %s, %s)"
        cur.execute(sql, (session_data["serial_id"], session_data["pre_post"], session_data["session_date"], session_data['venc']))
        conn.commit()
        cur.close()
        conn.close()
        return render_template("message.html", message="Session succesfully inserted!")
    return render_template("confirm_session_form.html", form=form, header=header, result=result)

@app.route('/list_t2', methods=['GET', 'POST'])
def list_t2():
    session_ids = [1, 4, 5, 8, 9, 13, 14, 16, 23, 24, 51, 28, 35, 36, 40, 41,
            44, 45, 47, 52, 54, 55, 56, 57, 59, 60, 69, 61, 62, 66,
            63, 68, 94, 80, 67, 81, 82]
    def to_t2_file(i):
        """render a t2 image filename from a session number"""
        return "/static/" + str(i) + ".jpg"
    patient_list = []
    
    image_file_list = [to_t2_file(i) for i in session_ids]
    return render_template("t2_list.html", patient_list=patient_list, image_file_list = image_file_list)
    
if __name__ == '__main__':
    manager.run()
