from flask import Flask, jsonify,request,session
import pyodbc
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime

app=Flask(__name__)
server = 'DESKTOP-6CJA95D\SQLEXPRESS'
database = 'Project'
print(generate_password_hash('test'))
app.config['SECRET_KEY']="group1"

class MyException(Exception):
    pass

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
                    resp=checkClockin(uName)
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
        except MyException as e:
            resp=jsonify({'message':'Fail','reason':str(e)})
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


@app.route('/clockout')
def clockout():
    
    try:
        empid=session['username']
        time=datetime.today().strftime('%H:%M:%S')
        date=datetime.today().strftime('%Y-%m-%d')
        conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
        cursor = conn.cursor()
        print("\n Clock  out Connected")
        cursor.execute('UPDATE shift set ends=? where empid=? and date=?',(time,empid,date))
        print("\n Clock  out update 1")
        cursor.execute('UPDATE shift set hours=DATEDIFF(minute, starts ,ends) where empid=? and date=?',(empid,date))
        cursor.commit()
        print("clock out inserted")
        return jsonify({"message":"Clocked Out"})
    except pyodbc.Error as db_error:
        return jsonify({f"message":"Fail","reason":str(db_error)})
    except KeyError:
        return jsonify({f"message":"Fail",'reason':'you are not logged in or session expired'})
        


def checkClockin(username):
    date=datetime.today().strftime('%Y-%m-%d')
    time=datetime.today().strftime('%H:%M:%S')
    try:
        conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
        cursor = conn.cursor()
        print("\n Clock in DB Connected")
        cursor.execute('SELECT * FROM shift WHERE empid=? and date=?',(username,date))
        print("\n Clock in Fetched")
        row=cursor.fetchone()
        if row:
            return(0)
        else:
            conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
            cursor = conn.cursor()
            print("\n Clock in 2 DB Connected")
            cursor.execute('insert into shift (date,empid,starts) values(?,?,?)',(date,username,time,))
            cursor.commit()
            print("clock in inserted")
            return(1)
    except pyodbc.Error as db_error:
        raise MyException("Clock in Failed, DB Isuue")
    except Exception as e:
        raise MyException(f"Clock in Failed :",str(e))

        
    