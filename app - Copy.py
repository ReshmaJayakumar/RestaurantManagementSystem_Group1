from flask import Flask, jsonify,request,session
import pyodbc
from werkzeug.security import generate_password_hash,check_password_hash

app=Flask(__name__)
server = 'DESKTOP-6CJA95D\SQLEXPRESS'
database = 'Project'
print(generate_password_hash('test'))
app.config['SECRET_KEY']="group1"

@app.route('/')
def index():
    if 'username' in session:
        username=session['username']
        return jsonify({'message': 'You are already logged in','username':username})
    else:
        resp=jsonify({'message':'Unauthorized'})
        resp.status_code=401
        return resp

@app.route('/login',methods=['POST'])
def login():
    json=request.json
    username=json['username']
    password=json['password']
    if username and password:
        try:
            conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
            cursor = conn.cursor()
            print("\n DB Connected")
            cursor.execute('SELECT * FROM users1 WHERE username=?',(username))
            #cursor.execute('insert into users1 (username) values(?)',('dominic'))
            row=cursor.fetchone()
            print("\nFetched")
            
            
            if row:
                print(row)
                uName=row[0]
                pWord=row[1]
                role=row[3]
                
                if check_password_hash(pWord,password):
                    session['username']=uName
                    return jsonify({'message':'Success','role':role})
                else:
                    resp=jsonify({'message':'Fail','reason':'Invalid password'})
                    resp.status_code=400
                    return resp
            else:
                resp=jsonify({'message':'Fail','reason':'Invalid Username'})
                resp.status_code=400
                return resp
        except pyodbc.Error as db_error:
            resp=jsonify({'message':'Fail','reason':str(db_error)})
            resp.status_code=400
            return resp
        except ValueError as val_error:
            resp=jsonify({'message':'Fail','reason':str(val_error)})
            resp.status_code=400
            return resp
        except Exception as e:
            resp=jsonify({'message':'Fail','reason':str(e)})
            resp.status_code=400
            return resp
        #finally:
         #if conn is not None:
            #conn.close()
    else:
        resp=jsonify({'message':'Fail','reason':'empty username or password'})
        resp.status_code=400
        return resp
    
@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username',None)
    return jsonify({"message":"Logged Out"})