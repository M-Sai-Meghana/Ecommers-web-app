from flask import Flask, request, redirect, render_template, url_for, flash, session, send_file
import mysql.connector
from flask_session import Session
from otp import genotp
from cmail import sendmail
from iotp import geniotp
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from tokenreset import token
import io
from io import BytesIO
import stripe
import os
app = Flask(__name__)
app.secret_key = '*2023_1!meghana'
app.config['SESSION_TYPE'] = 'filesystem'
stripe.api_key='sk_test_51MvxJqSJVkjXE2R4vNgcdIAa7ELbFTgwjrulaSo0XTkdxdjZJOARysGFDak7WyRHEsYCIzxGHPa4gw9iPyPyMoDv00HKzslp9N'
db = os.environ['RDS_DB_NAME']
user = os.environ['RDS_USERNAME']
password = os.environ['RDS_PASSWORD']
host = os.environ['RDS_HOSTNAME']
mydb = mysql.connector.connect(host=host, user=user, password=password, db=db)
# mydb = mysql.connector.connect(host='localhost', user='root', password='admin', db='main_sample')    
Session(app)
@app.route('/')
def home():
    return render_template('homepage.html')
@app.route('/adminsignup',methods=['GET','POST'])
def adminsign():
    if request.method=='POST':
        uname=request.form['name']
        email=request.form['email']
        password=request.form['password']
        passcode=request.form['passcode']
        upasscode='4567'
        cursor=mydb.cursor(buffered=True)
        # check if the email already exists
        cursor.execute('SELECT COUNT(*) FROM admin WHERE email = %s', [email])
        count = cursor.fetchone()[0]
        if count > 0:
            flash('Email id already exists')
            return render_template('adminsignup.html')
        # check if the passcode matches
        elif upasscode != passcode:
            flash('Invalid passcode')
            return render_template('adminsignup.html')
        # insert the admin details
        else:
            cursor.execute('INSERT INTO admin VALUES (%s,%s,%s,%s)',[uname,email,password,passcode])
            mydb.commit()
            cursor.close()
            flash("Admin account created successfully")
            return render_template('adminlogin.html')
    return render_template('adminsignup.html')
@app.route('/adminlogin',methods=['GET','POST'])
def adminlogin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT COUNT(*) FROM admin WHERE email = %s AND password = %s', [email, password])
        count = cursor.fetchone()[0]
        if count == 0:
            flash('Invalid email or password')
            return render_template('login.html')
        else:
            session['user'] = email
            return render_template('admindash.html')
    return render_template('adminlogin.html')
@app.route('/adminforgot',methods=['GET','POST'])
def adminforget():
    if request.method=='POST':        
        email=request.form['email']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email from admin')
        data=cursor.fetchall()
        if (email,) in data:
            cursor.execute('select email from admin where email=%s',[email])
            data=cursor.fetchone()[0]
            cursor.close()
            subject='Reset Password for SmartShop Login'
            body=f'Reset the passwword using -{request.host+url_for("admincreatepassword",atoken=token(email,120))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your mail')
            return redirect(url_for('adminlogin'))
        else:
            return 'Invalid user id' 
    return render_template('adminforgot.html')
@app.route('/admincreatepassword/<atoken>',methods=['GET','POST'])
def admincreatepassword(atoken):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        email=s.loads(atoken)['user']
        if request.method=='POST':
            npass=request.form['npassword']
            cpass=request.form['cpassword']
            if npass==cpass:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update admin set password=%s where email=%s',[npass,email])
                mydb.commit()
                cursor.close()
                return 'Password changed successfully'
            else:
                return 'Written password was mismatched'
        return render_template('adminnewpassword.html')
    except:
        return 'Link expired start over again'
    else:
        return redirect(url_for('login'))
@app.route('/admindashboard')
def admindash():
    if session.get('user'):
        return render_template('admindash.html')
    else:
        flash('Login to access dashboard')
        return redirect(url_for('adminlogin'))
@app.route('/adminlogout')
def adminlogout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('adminlogin'))
    else:
        flash('already signed off!')
        return redirect(url_for('adminlogin'))
@app.route('/additems',methods=['GET','POST'])
def additems():
    if request.method=="POST":
        name=request.form['name']
        description=request.form['desc']
        quantity=request.form['qty']
        category=request.form['category']
        price=request.form['price']
        image=request.files['image']
        cursor=mydb.cursor()
        id1=geniotp()
        filename=id1+'.jpg'
        cursor.execute('insert into items(item_id,item_name,item_description,qty,category,price) values(%s,%s,%s,%s,%s,%s)',[id1,name,description,quantity,category,price])
        mydb.commit()
        print(filename)
        path=r"\static"
        image.save(os.path.join(path,filename))
        print('success')
    return render_template('additems.html')
@app.route('/itemstatus')
def itemstatus():
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT item_id, item_name, qty, price, category FROM items')
        items = cursor.fetchall()
        return render_template('itemsstatus.html',items=items)
    return render_template('itemsstatus.html')
@app.route('/updateitems/<itemid>', methods=['GET','POST'])
def updateitems(itemid):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT item_name, qty, item_description, category, price FROM items WHERE item_id=%s', [itemid])
        item = cursor.fetchone()
        cursor.close()
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['desc']
            qty = request.form['qty']
            price = request.form['price']
            category = request.form['category']
            cursor = mydb.cursor(buffered=True)
            cursor.execute('UPDATE items SET item_name=%s, item_description=%s, qty=%s, price=%s, category=%s WHERE item_id=%s', [name, description, qty, price, category, itemid])
            mydb.commit()
            cursor.close()
            flash('Item updated successfully')
            return redirect(url_for('itemstatus'))
        return render_template('updateitems.html', item=item)
    else:
        return redirect(url_for('itemstatus'))
@app.route('/deleteitems/<itemid>')
def deleteitems(itemid):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from items where item_id=%s',[itemid])
        mydb.commit()
        cursor.close()
        flash('items deleted successfully')
        return redirect(url_for('itemstatus'))
@app.route('/usignup', methods=['GET', 'POST'])
def UserSignup():
    if request.method == 'POST':
        mobile = request.form['mobile']
        name = request.form['name']
        password = request.form['password']
        email = request.form['email']
        address = request.form['useraddress']
        gender = request.form['gender']     
        otp = genotp()
        session['user'] = mobile
            # Send OTP to user's email 
        subject='Thanks for registering to our onlinshopping SmartShop'
        body=f'Use this otp to register {otp}'
        sendmail(email,subject,body)
            # insert into database
        cursor = mydb.cursor(buffered=True)
        cursor.execute('insert into users values(%s,%s,%s,%s,%s,%s)', (mobile, name, password, email, address, gender))
        mydb.commit()
        cursor.close()
        flash('OTP sent successfully. Please enter the OTP to complete the registration process.')
        return redirect(url_for('otp'))
    return render_template('signup.html')
@app.route('/otp_verification', methods=['GET', 'POST'])
def otp():
    if request.method == 'POST':
        user_otp = request.form['otp']
        flash('Account registered successfully!')
        session.pop('otp', None)
        session.pop('mobile', None)
        return redirect(url_for('login'))
    return render_template('otp.html')
@app.route('/ulogin', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT COUNT(*) FROM users WHERE mobile_number = %s AND password = %s', [mobile, password])
        count = cursor.fetchone()[0]
        if count == 0:
            flash('Invalid mobile number or password')
            return render_template('login.html')
        else:
            session['user'] = mobile
            if not session.get(mobile):
                session[mobile]={}
            return redirect(url_for('home'))
    return render_template('login.html')
@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    cursor=mydb.cursor()
    cursor.execute("select * from items")
    items=cursor.fetchall()
    return render_template('dashboard.html',items=items)
@app.route('/homepage/<category>')
def homepage(category):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from items where category=%s',[category])
    items=cursor.fetchall()
    return render_template('dashboard.html',items=items)
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home'))
    else:
        flash('already signed off!')
        return redirect(url_for('login'))
@app.route('/forgotpassword',methods=['GET','POST'])
def forget():
    if request.method=='POST':        
        mobile=request.form['mobile']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select mobile_number from users')
        data=cursor.fetchall()
        if (mobile,) in data:
            cursor.execute('select email from users where mobile_number=%s',[mobile])
            data=cursor.fetchone()[0]
            cursor.close()
            subject='Reset Password for SmartShop Login'
            body=f'Reset the passwword using -{request.host+url_for("createpassword",token=token(mobile,120))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your mail')
            return redirect(url_for('login'))
        else:
            return 'Invalid user id' 
    return render_template('forgotp.html')
@app.route('/createpassword/<token>',methods=['GET','POST'])
def createpassword(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        mobile=s.loads(token)['user']
        if request.method=='POST':
            npass=request.form['npassword']
            cpass=request.form['cpassword']
            if npass==cpass:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update users set password=%s where mobile_number=%s',[npass,mobile])
                mydb.commit()
                cursor.close()
                return 'Password changed successfully'
            else:
                return 'Written password was mismatched'
        return render_template('newpassword.html')
    except:
        return 'Link expired start over again'
    else:
        return redirect(url_for('login'))
@app.route('/cart/<itemid>/<name>/<price>')
def cart(itemid,name,price):
    if not session.get('user'):
        return redirect(url_for('login'))
    if name not in session[session.get('user')]:
        session[session.get('user')][itemid]=[name,1,price]
        session.modified=True
        print(session[session.get('user')])
        flash(f'{name} added to cart')
        return redirect(url_for('viewcart'))
    session[session.get('user')][itemid][1]+=1
    flash('Item already in cart  quantity increased to +1')
    return redirect(url_for('viewcart'))
@app.route('/viewcart')
def viewcart():
    if not session.get('user'):
        return redirect(url_for('login'))
    items=session.get(session.get('user')) if session.get(session.get('user')) else 'empty'
    if items=='empty':
        return 'no products in cart'
    return render_template('cart.html',items=items)
@app.route('/remcart/<item>')
def rem(item):
    if session.get('user'):
        session[session.get('user')].pop(item)
        return redirect(url_for('viewcart'))
    return(redirect(url_for('login')))
@app.route('/itemsdetails/<itemid>')
def itemsdetails(itemid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT * from items where item_id=%s',(itemid,))
    items=cursor.fetchall()
    return render_template('itemdetails.html',items=items)
@app.route('/pay/<itemid>/<name>/<int:price>',methods=['POST'])
def pay(itemid,name,price):
    if session.get('user'):
        q=int(request.form['qty'])
        mobile=session.get('user')
        total=price*q
        checkout_session=stripe.checkout.Session.create(
            success_url=url_for('success',itemid=itemid,name=name,q=q,total=total,_external=True),
            line_items=[
                {
                    'price_data': {
                        'product_data': {
                            'name': name,
                        },
                        'unit_amount': price*100,
                        'currency': 'inr',
                    },
                    'quantity': q,
                },
                ],
            mode="payment",)
        return redirect(checkout_session.url)
    else:
        return redirect(url_for('login'))
@app.route('/success/<itemid>/<name>/<q>/<total>')
def success(itemid,name,q,total):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('insert into orders(itemid,name,qty,total_price,mobile) values(%s,%s,%s,%s,%s)',[itemid,name,q,total,session.get('user')])
        mydb.commit()
        return redirect(url_for('orders'))
    return redirect(url_for('login'))
@app.route('/orderplaced')
def orders():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from orders where mobile=%s', (session['user'],))
        order=cursor.fetchall()
        mydb.commit()
        cursor.close()
        return render_template('order.html', order=order)
    return redirect(url_for('login'))
@app.route('/review/<itemid>', methods=['GET', 'POST'])
def addreview(itemid):
    if session.get('user'):
        if request.method == 'POST':
            print(request.form)
            mobile = session.get('user')
            title = request.form['title']
            desc = request.form['review']
            rate = request.form['rating']
            cursor = mydb.cursor(buffered=True)
            cursor.execute('INSERT INTO reviews(mobile, itemid, title, review, rating) VALUES(%s, %s, %s, %s, %s)', [mobile, itemid, title, desc, rate])
            mydb.commit()
        return render_template('addreview.html')
    else:
        return redirect(url_for('login'))
@app.route('/readreview/<itemid>')
def readreview(itemid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute("select * from reviews where itemid=%s",[itemid])
    reviews=cursor.fetchall()
    return render_template('readreview.html',reviews=reviews)
@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        name = request.form['search']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT * from items where item_name=%s',[name])
        data= cursor.fetchall()
        return render_template('dashboard.html',items=data)
@app.route('/contactus',methods=['GET','POST'])
def contactus():
    if request.method=="POST":
        print(request.form)
        name=request.form['name']
        emailid=request.form['emailid']
        message=request.form['message']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('insert into contactus(name,emailid,message) values(%s,%s,%s)',[name,emailid,message])
        mydb.commit()
    return render_template('contactus.html')
    

@app.route('/readcontactus')
def readcontactus():
    cursor=mydb.cursor(buffered=True)
    cursor.execute("select * from contactus ")
    contact=cursor.fetchall()
    return render_template('readcontact.html',contact=contact)
if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
