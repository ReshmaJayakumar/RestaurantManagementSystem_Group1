from flask import Flask, jsonify,request,session,send_file
import pyodbc
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime
import json as js
from flask import Response
from decimal import Decimal
import os

app=Flask(__name__)
server = 'DESKTOP-6CJA95D\SQLEXPRESS'
database = 'Project'
app.config['SECRET_KEY']="group1"
"""connection = pyodbc.connect(
    'DRIVER={SQL Server};SERVER=RESHMA\\SQLEXPRESS;DATABASE=RestaurantManagementSystem;Trusted_Connection=yes;'
)"""

connection = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')

class MyException(Exception):
    pass

@app.route('/')
def index():
    if 'username' in session:
        username=session['username']
        role=session['role']
        return jsonify({'message': 'You are already logged in','username':username,'role':role})
    else:
        resp=jsonify({'message':'Unauthorized'})
        resp.status_code=401
        return resp

@app.route('/login',methods=['POST' ])
def login():    
    json=request.json
    username=json['username']
    password=json['password']
    if username and password:
        try:
            #conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
            conn=connection
            cursor = conn.cursor()
            print("\n DB Connected")
            cursor.execute('SELECT * FROM employees WHERE employeeid=?',(username))
            row=cursor.fetchone()
            print("\nFetched")
            
            
            if row:
                print(row)
                uName=row[0]
                pWord=row[6]
                role=row[3]
                
                if check_password_hash(pWord,password):
                    session['username']=uName
                    cursor.execute('SELECT RoleName FROM roles WHERE roleid=?',(role))
                    row=cursor.fetchone()
                    role=row[0]
                    session['role']=role
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
        conn=connection
        #conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
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
        


@app.route('/orders',defaults={'orderno': None})
@app.route('/orders/',defaults={'orderno': None})
@app.route('/orders/<orderno>')
def orders(orderno):
    if request.method=='GET':
        if 'username' in session:
            if orderno:
                try:
                    query=f"Select * from Orders where OrderID ='{orderno}'"
                    #conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
                    conn=connection
                    cursor = conn.cursor()
                    print("\n DB Connected")
                    cursor.execute(query)
                    row=cursor.fetchone()
                    if row:
                        orderid=str(row[0])
                        employeeid=str(row[1])
                        ordertype=str(row[2])
                        table=str(row[3])
                        source=str(row[4])
                        phone=str(row[5])
                        time=str(row[6])
                        orderstatus=str(row[8])
                        amount=str(row[9])
                        created=str(row[10])
                        completed=str(row[11])
                        cursor.execute(f"Select * from OrderItems WHERE OrderID={orderid}")
                        items=[]
                        for row in cursor:
                            ItemID=row[2]
                            Quantity=row[3]
                            Price=row[4]
                            Notes=row[5]
                            item={'ItemID':str(ItemID),'Quantity':str(Quantity),'Price':str(Price),'Notes':str(Notes)}
                            items.append(item)
                        innerresp={'orderid':orderid,'employeeid':employeeid,'ordertype':ordertype,'table':table,'source':source,
                        'phone':phone,'time':time,'orderstatus':orderstatus,'amount':amount,'createdat':created,'completed':completed,'items':items}
                        return Response(js.dumps(innerresp),content_type='application/json')
                    else:
                        return jsonify({'message':"No order found for given order ID"})
                except pyodbc.Error as db_error:
                    sqlstate = db_error.args[0]
                    if sqlstate == '22018':
                        return jsonify({f"message":"Fail","reason":"Invalid OrderID Type"})
                    else:
                        return jsonify({f"message":"Fail","reason":str(db_error)})
                except Exception as e:
                    return jsonify({f"message":"Fail","reason":str(e)})
            else:
                try:
                    resp=[]
                    resp2=""
                    query="select * from Orders"
                    where=''
                    print("hello")
                    json=request.json
                    
                    count=0
                    statusflag=False
                    typeflag=False
                    dateflag=False
                    if "orderstatus" in json:
                        status=json['orderstatus']
                        where=where+f"OrderStatus='{status}'"
                        count=count+1
                        statusflag=True
                    if "ordertype" in json:
                        type=json['ordertype']
                        where=where+f" and OrderType='{type}'"
                        count=count+1
                        typeflag=True
                    if "date" in json:
                        date=json['date']
                        where=where+f" and CreatedAt>'{date}'"
                        count=count+1
                        dateflag=True
                    if statusflag!=True:
                        if typeflag:
                            where=where.replace("and OrderType","OrderType")
                        elif dateflag:
                            where=where.replace("and CreatedAt","CreatedAt")
                    if statusflag or typeflag or dateflag:
                        query=query+" where "+where
                    #conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
                    conn=connection
                    cursor = conn.cursor()
                    print("\n DB Connected")
                    cursor.execute(query)
                    rows=cursor.fetchall()
                    for row in rows:
                        orderid=str(row[0])
                        employeeid=str(row[1])
                        ordertype=str(row[2])
                        table=str(row[3])
                        source=str(row[4])
                        phone=str(row[5])
                        time=str(row[6])
                        orderstatus=str(row[8])
                        amount=str(row[9])
                        created=str(row[10])
                        completed=str(row[11])
                        cursor.execute(f"Select * from OrderItems WHERE OrderID={orderid}")
                        items=[]
                        for row in cursor:
                            ItemID=row[2]
                            Quantity=row[3]
                            Price=row[4]
                            Notes=row[5]
                            item={'ItemID':str(ItemID),'Quantity':str(Quantity),'Price':str(Price),'Notes':str(Notes)}
                            items.append(item)
                        innerresp={'orderid':orderid,'employeeid':employeeid,'ordertype':ordertype,'table':table,'source':source,
                        'phone':phone,'time':time,'orderstatus':orderstatus,'amount':amount,'createdat':created,'completed':completed,'items':items}
                        resp.append(innerresp)
                    print("all worked")
                    resp= js.dumps(resp)
                    return Response(resp,status=200,content_type='application/json')
                    
                    
                except pyodbc.Error as db_error:
                    return jsonify({f"message":"Fail","reason":db_error})
                    
                except Exception as e:
                    return jsonify({f"message":"Fail","reason":str(e)})
        else:
            return jsonify({f"message":"Fail","reason":"you are not logged, in please login"})


@app.route('/schedule',methods=['GET','POST'])
def schedule():
    if request.method=='GET':
        schedules=[]
        try:
            username=session['username']
            date=datetime.today().strftime('%Y-%m-%d')
            print(date)
            print(username)
            conn=connection
            #conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
            cursor = conn.cursor()
            print("\n Schedule DB Connected")
            cursor.execute(f"SELECT * FROM schedule WHERE userid='{username}' and date>='{date}'")
            print("\n Schedule Fetched")
            rows=cursor.fetchall()
            for row in rows:
                print("loop")
                id=str(row[0])
                date=str(row[2])
                starts=str(row[3])
                ends=str(row[4])
                hours=str(row[5])
                sched={'id':id,'date':date,'start':starts,'ends':ends,'hours':hours}
                schedules.append(sched)
            print(schedules)
            schedules=js.dumps(schedules)
            return(Response(schedules,status=200,content_type='application/json'))
        except Exception as e:
            return jsonify({f"message":"Fail","reason":e})

    elif request.method=='POST':
        return 'post'


def checkClockin(username):
    date=datetime.today().strftime('%Y-%m-%d')
    time=datetime.today().strftime('%H:%M:%S')
    try:
        #conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
        conn=connection
        cursor = conn.cursor()
        print("\n Clock in DB Connected")
        print(username)
        cursor.execute('SELECT * FROM shift WHERE empid=? and date=?',(username,date))
        print("\n Clock in Fetched")
        row=cursor.fetchone()
        if row:
            return(0)
        else:
            conn=connection
            #conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
            cursor = conn.cursor()
            print("\n Clock in 2 DB Connected")
            cursor.execute('insert into shift (date,empid,starts) values(?,?,?)',(date,username,time))
            cursor.commit()
            print("clock in inserted")
            return(1)
    except pyodbc.Error as db_error:
        raise MyException(f"Clock in Failed,{db_error}")
    except Exception as e:
        raise MyException(f"Clock in Failed :",str(e))

