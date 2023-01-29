from datetime import datetime
from flask import Flask,request, render_template, redirect, url_for,g,session
from flask_mysqldb import MySQL
import os
from os import path
import json
from random import randint
#from werkzeug.utils import secure_filename
#from werkzeug.datastructures import  FileStorage


appp = Flask(__name__)
appp.secret_key = os.urandom(24) #to encrypt session data, a Flask appplication needs a defined SECRET_Key

appp.config['MYSQL_HOST'] = 'localhost'
appp.config['MYSQL_USER'] = 'root'
appp.config['MYSQL_PASSWORD'] = ''
appp.config['MYSQL_DB'] = 'eamp'

mysql = MySQL(appp)

@appp.before_request
def before_request():
    g.user = None#global, referring to the data being global within a context
    if 'user' in session:#Server-side session is the time between the client logs in and logs out of the server
        g.user = session['user']#data saved in the Session is stored in a temporary directory on the server


@appp.route('/dropsession')
def dropsession():
    session.pop('user', None)
    return render_template('index.html')

@appp.route('/',methods=['GET','POST'])
def index():
    if 'user' in session:
        name= session['user']
        customer_info = get_cid_info(name)
        return render_template('index.html',name= name,customer_info= customer_info)
    return render_template('index.html')

@appp.route('/manage',methods=['GET','POST'])
def manage():
    if 'user' in session:
        name= session['user']
        cur = mysql.connection.cursor()
        hj= cur.execute("SELECT * FROM orders")
        hj = [dict(oid=col[0],cost=col[1],daddress=col[2],cid=col[3],pid=col[4],quantity=col[5],tcost=col[6]) for col in cur.fetchall()]
        
        return render_template('manage.html',hj= hj)
    return render_template('index.html')

@appp.route('/products',methods=['GET','POST'])
def products():
    if 'user' in session:
        name = session['user']
        cur = mysql.connection.cursor()
        hj= cur.execute("SELECT * FROM product")
        hj = [dict(pid=col[0],pname=col[1],pdesc=col[2],ncost=col[3],pimg=col[4]) for col in cur.fetchall()]
        customer_info = get_cid_info(name)
        for i in hj:
            kl = i['pdesc'].split(';')
            i['description'] = kl
        print(hj)
        return render_template('products.html',hj=hj,name=name,customer_info=customer_info)
    #return render_template('pleaselogin.html') 
    cur = mysql.connection.cursor()
    hj= cur.execute("SELECT * FROM product")
    hj = [dict(pid=col[0],pname=col[1],pdesc=col[2],ncost=col[3],pimg=col[4]) for col in cur.fetchall()]
    for i in hj:
        kl = i['pdesc'].split(';')
        i['description'] = kl
    print(hj)
    return render_template('products.html',hj=hj)

@appp.route('/order_placed',methods=['GET','POST'])
def order_placed():
    if 'user' in session:
        name = session['user']
        pid = request.form['pid']
        cid = request.form['cid']
        cost = request.form['cost']
        quantity = request.form['quantity']
        print(cost)
        customer_info = get_cid_info(cid)
        cost1 = int(cost)
        tcost=int(quantity)*int(cost)#here t cost is generated
        cur = mysql.connection.cursor()
        hj= cur.execute("INSERT INTO orders(pid,cid,cost,daddress,quantity,tcost) values(%s,%s,%s,%s,%s,%s)",(pid,cid,cost1,customer_info[0]['address'],quantity,tcost))#here insert in order table
        mysql.connection.commit()
        return render_template('osuccess.html')
    return "Not Logged In"

@appp.route('/orders',methods=['GET','POST'])
def orders():
    if 'user' in session:
        name = session['user']
        customer_info = get_cid_info(name)
        cur = mysql.connection.cursor()
        orders = cur.execute("SELECT pid,daddress,tcost,oid,cid,quantity FROM orders where cid='"+str(int(name))+"'")
        orders = [dict(pid=col[0],daddress=col[1],cost=col[2],oid=col[3],cid=col[4],quantity=col[5]) for col in cur.fetchall()]
        return render_template('orders.html',name=name,customer_info=customer_info,orders=orders)
    return "Not Logged In"

@appp.route('/success',methods=['GET','POST'])
def success():
    if 'user' in session:
        name = session['user']
        customer_info = get_cid_info(name)
        cur = mysql.connection.cursor()# no need of cursor
        return render_template('osuccess.html')
    return "order not placed"
@appp.route('/pchange',methods=['GET','POST'])
def pchange():  
    if 'user' in session:
        name = session['user']
        customer_info = get_cid_info(name)
        cur = mysql.connection.cursor()# no need of cursor
        return render_template('pchange.html')

@appp.route('/pch',methods=['GET','POST'])
def pch():
    if 'user' in session:
        pas1= request.form['cpd']
        pas2= request.form['npd']
        name = session['user']
        cur = mysql.connection.cursor()
        customer_info = get_cid_info(name)
        if customer_info[0]['password'] == pas1:
            hj=cur.execute("UPDATE customer SET password = (%s) WHERE cid='"+str(int(name))+"'",[pas2])
            mysql.connection.commit()
            return redirect(url_for('account'))
        else:
            return 'Enter Correct Password'


@appp.route('/account',methods=['GET','POST'])
def account():
    if 'user' in session:
        name = session['user']
        ci = get_cid_info(name)
        cur = mysql.connection.cursor()#no need of cursor
        return render_template('account.html', ci=ci)

@appp.route('/register_saved',methods=['GET','POST'])
def register_saved():
    namef = request.form['namef']
    email = request.form['email']
    addrf = request.form['addrf']
    passwd = request.form['passwd']
    phnno = request.form['phnno']
    fg= [passwd,addrf,namef,phnno,email]
    conn = mysql.connection.cursor()
    conn.execute("INSERT INTO customer(password,address,name,phno,email) values(%s,%s,%s,%s,%s)",(passwd,addrf,namef,phnno,email))
    mysql.connection.commit()
    hj= conn.execute("SELECT * FROM customer where email='"+email+"'")
    hj = [dict(cid=col[0]) for col in conn.fetchall()]
    print(hj)
    session['user'] = hj[0]['cid']
    return redirect(url_for('index'))

def get_cid_info(cid):
    conn = mysql.connection.cursor()
    hj= conn.execute("CALL new_procedure('"+str(int(cid))+"') ") 
    hj = [dict(cid=col[0],email=col[1],password=col[2],address=col[3],nam=col[4],ph=col[5]) for col in conn.fetchall()]
    return hj

@appp.route('/login_add',methods=['GET','POST'])
def login_add():
    email = request.form['email']
    password = request.form['password']
    conn = mysql.connection.cursor()
    hj= conn.execute("SELECT cid,email,password FROM customer where email='"+email+"'")
    hj = [dict(cid=col[0],email=col[1],password=col[2]) for col in conn.fetchall()]
    print(hj)
    if hj:
        if hj[0]['email'] == email and hj[0]['password'] == password:
            session['user'] = hj[0]['cid']
            return redirect(url_for('index'))
        else:
            return "Incorrect Password"
    else:
        return "Username doesn't exist. Register to continue"


@appp.route('/mlogadd',methods=['GET','POST'])
def mlogadd():
    email = request.form['log']
    password = request.form['pwd']
    conn = mysql.connection.cursor()
    hj= conn.execute("SELECT uid,passwd,name,addr FROM management where uid='"+email+"'")
    hj = [dict(uid=col[0],passwd=col[1],name=col[2],addr=col[3]) for col in conn.fetchall()]
    print(hj)
    if hj:
        if hj[0]['uid'] == email and hj[0]['passwd'] == password:
            session['user'] = hj[0]['uid']
            return redirect(url_for('manage'))
        else:
            return "Enter Correct Password"
    else:
        return "You are not authorised to access"

@appp.route('/register',methods=['GET','POST'])
def register():
    return render_template('register.html')

@appp.route('/mlogin',methods=['GET','POST'])
def mlogin():
    return render_template('mlogin.html')

@appp.route('/pleaselogin')
def pleaselogin():
    return render_template('pleaselogin.html')

if __name__ == '__main__':
    appp.run(debug=True)
