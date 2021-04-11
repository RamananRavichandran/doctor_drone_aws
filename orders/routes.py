from flask import render_template, flash, request, jsonify, redirect, url_for, make_response
from orders import app, db
from orders.models import Orders, Orders_items, Products, Users
import pdfkit
from datetime import date
from sqlalchemy import func
from orders.forms import RegisterForm
from flask_login import login_user, current_user, logout_user, login_required
from passlib.hash import sha256_crypt
import boto3
from botocore.exceptions import ClientError
import urllib3
import sys
import logging
import csv
# import psycopg2

# # Amazon Redshift connect string
# conn_string = "dbname='***' port='5439' user='***' password='***' host='mycluster.***.redshift.amazonaws.com'"
# # connect to Redshift (database should be open to the world)
# con = psycopg2.connect(conn_string)
# sql = """COPY %s FROM '%s' credentials
#       'aws_access_key_id=%s; aws_secret_access_key=%s'
#        delimiter '%s' FORMAT CSV %s %s; commit;""" %
# (to_table, fn, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, delim, quote, gzip)

# Here
#  fn - s3://path_to__input_file.gz
#  gzip = 'gzip'

# cur = con.cursor()
# cur.execute(sql)
# con.close()

http = urllib3.PoolManager()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def connect_aws():
    session = boto3.session.Session()
    client = session.client(
        service_name='s3',
        region_name='us-east-2'
    )


def getlist():
    user = Users.query.filter_by(email=current_user.email).first()
    my_list = user.Roles.split(",")
    return my_list

# HOME_PAGE


@app.route('/', methods=['POST', 'GET'])
def login():

    return render_template('login.html')

# LOGIN


@app.route('/rootlogin', methods=['POST', 'GET'])
def rootlogin():

    if current_user.is_authenticated:
        return redirect(url_for('rootdash'))
    if request.method == 'POST':
        # Get Form Fields
        email = request.form['email']
        password_candidate = request.form['password']

        user = Users.query.filter_by(email=email).first()
        if user:

            passwordd = Users.query.filter_by(email=email).first()
            if sha256_crypt.verify(password_candidate, passwordd.password):
                login_user(user)
                # flash('You are now logged in', 'success')
                return redirect(url_for('rootdash'))

            else:
                error = "Invalid Password"
                return render_template('r_login.html', error=error)

        else:
            error = "Invalid email"
            return render_template('r_login.html', error=error)

    return render_template('r_login.html')


@app.route('/hublogin', methods=['POST', 'GET'])
def hublogin():

    return render_template('h_login.html')

# REGISTER


@app.route('/rootregister', methods=['POST', 'GET'])
def rootregister():
    if current_user.is_authenticated:
        return redirect(url_for('rootdash'))
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        addd = Users(username=username, email=email, password=password)
        db.session.add(addd)
        db.session.commit()
        flash('You are now registered', 'success')
        return redirect(url_for('login'))
    return render_template('RootReg.html', form=form)


@app.route('/hubregister', methods=['POST', 'GET'])
def hubregister():

    return render_template('HubReg.html')

# DASHBOARD


@app.route('/rootdash', methods=['POST', 'GET'])
def rootdash():
    # order = db.session.query(Orders).filter(
    #     func.date(Orders.date_creation) == date.today()).all()
    # count = 0
    # for i in order:
    #     count += int(i.total_amount)
    # num_orders = db.session.query(Orders).filter(
    #     func.date(Orders.date_creation) == date.today()).count()

    # context = {
    #     'daily': count,
    #     'orders': num_orders
    # }

    return render_template('RootDash.html')


@app.route('/hubdash', methods=['POST', 'GET'])
def hubdash():
    # order = db.session.query(Orders).filter(
    #     func.date(Orders.date_creation) == date.today()).all()
    # count = 0
    # for i in order:
    #     count += int(i.total_amount)
    # num_orders = db.session.query(Orders).filter(
    #     func.date(Orders.date_creation) == date.today()).count()

    # context = {
    #     'daily': count,
    #     'orders': num_orders
    # }

    return render_template('HubDash.html')

# PRODUCT


@app.route('/rootproduct', methods=['POST', 'GET'])
def rootproduct():

    return redirect(url_for('viewproducts'))


@app.route('/hubproductadd', methods=['POST', 'GET'])
def hubproductadd():

    return redirect(url_for('products'))


@app.route('/hubmanageproduct', methods=['POST', 'GET'])
def hubmanageproduct():

    return redirect(url_for('products'))

# ORDER


@app.route('/rootorder')
def rootorder():
    return render_template('r_makeorder.html')


@app.route('/rootmanageorder')
def rootmanageorder():
    return render_template('r_manageorder.html')


@app.route('/huborder')
def huborder():
    return render_template('h_makeorder.html')


@app.route('/hubmanageorder')
def hubmanageorder():
    return render_template('h_manageorder.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/roles')
def roles():
    users = Users.query.all()
    return render_template('roles.html', users=users)


@app.route('/insert', methods=['POST', 'GET'])
def insert():
    barcode = request.form.getlist('item_bar[]')
    qua = request.form.getlist('item_quantity[]')
    name = request.form.getlist('item_name[]')
    total = request.form.getlist('total[]')
    price = request.form.getlist('price[]')
    total_amount = request.form.get('total_amount')

    for n, q in zip(barcode, qua):
        product = Products.query.filter_by(barcode=n).first()
        if product.quantity > 0:
            product.quantity = product.quantity - int(q)
        else:
            print("you do not have this much of quantity", n)
    db.session.commit()
    medicine_list = [barcode, qua, name, price]
    with open("MedicinesRequired.csv", "a") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(medicine_list)
    s3 = boto3.resource('s3',
                        aws_access_key_id='AKIAU56YN4TZRNNHKYLU',
                        aws_secret_access_key='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')
    s3.meta.client.upload_file(
        'MedicinesRequired.csv', 'ramjan', 'MedicinesRequired.csv')

    # conn_string = "dbname='***' port='5439' user='***' password='***' host='mycluster.***.redshift.amazonaws.com'"
    # to_table = ""
    # fn = ""
    # AWS_ACCESS_KEY_ID = "AKIAU56YN4TZRNNHKYLU"
    # AWS_SECRET_ACCESS_KEY = "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"
    # delim = ","
    # quote = ""
    # gzip = "gzip"
    # # connect to Redshift (database should be open to the world)
    # con = psycopg2.connect(conn_string)
    # sql = """COPY %s FROM '%s' credentials
    #     'aws_access_key_id=%s; aws_secret_access_key=%s'
    #     delimiter '%s' FORMAT CSV %s %s; commit;""" %
    # (to_table, fn, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, delim, quote, gzip)
    add = Orders(total_amount=total_amount, user_order=current_user)

    db.session.add(add)
    db.session.commit()
    for q, p, t, n, b in zip(qua, price, total, name, barcode):
        ord = Orders_items(barcode=b, quantity=q, name=n,
                           price=p, total=t, Orders_items=add)
        db.session.add(ord)
    db.session.commit()
    return jsonify({'data': 'ok'})


@app.route('/data', methods=['POST'])
def getdata():
    input_item = request.json
    pro = Products.query.filter_by(barcode=input_item).first()
    return jsonify({'price': pro.price, 'name': pro.name, 'quantity': pro.quantity})


@app.route('/products', methods=['GET', 'POST'])
def products():
    products = Products.query.all()
    if request.method == 'POST':
        name = request.form.get('name')
        barcode = request.form.get('barcode')
        quantity = request.form.get('quantity')
        price = request.form.get('price')
        add = Products(name=name, barcode=barcode,
                       quantity=quantity, price=price)

        product_list = [name, barcode, quantity, price]
        with open("InventoryAvailables.csv", "a") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(product_list)
        s3 = boto3.resource('s3',
                            aws_access_key_id='AKIAU56YN4TZRNNHKYLU',
                            aws_secret_access_key='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')
        s3.meta.client.upload_file(
            'InventoryAvailables.csv', 'ramjan', 'InventoryAvailables.csv')
        # conn_string = "dbname='***' port='5439' user='***' password='***' host='mycluster.***.redshift.amazonaws.com'"
        # to_table = ""
        # fn = ""
        # AWS_ACCESS_KEY_ID = "AKIAU56YN4TZRNNHKYLU"
        # AWS_SECRET_ACCESS_KEY = "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"
        # delim = ","
        # quote = ""
        # gzip = "gzip"
        # # connect to Redshift (database should be open to the world)
        # con = psycopg2.connect(conn_string)
        # sql = """COPY %s FROM '%s' credentials
        #     'aws_access_key_id=%s; aws_secret_access_key=%s'
        #     delimiter '%s' FORMAT CSV %s %s; commit;""" %
        # (to_table, fn, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, delim, quote, gzip)
        db.session.add(add)
        db.session.commit()
        return redirect(url_for('products'))
    return render_template('h_product.html', products=products)


@app.route('/viewproducts', methods=['GET', 'POST'])
def viewproducts():
    products = Products.query.all()
    if request.method == 'POST':
        name = request.form.get('name')
        barcode = request.form.get('barcode')
        quantity = request.form.get('quantity')
        price = request.form.get('price')
        add = Products(name=name, barcode=barcode,
                       quantity=quantity, price=price)
        db.session.add(add)
        db.session.commit()
        return redirect(url_for('viewproducts'))
    return render_template('r_product.html', products=products)


@app.route("/product/delete/<int:product_id>", methods=['POST'])
def delete_product(product_id):
    product = Products.query.get(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('products'))


@app.route("/product/update/<int:product_id>", methods=['POST', 'GET'])
def update_product(product_id):
    product = Products.query.get(product_id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.barcode = request.form.get('barcode')
        product.quantity = request.form.get('quantity')
        product.price = request.form.get('price')
        db.session.commit()
        return redirect(url_for('products'))

    return render_template('h_updateProduct.html', product=product)


@app.route("/manageorder")
@login_required
def manageorder():
    orders = Orders.query.all()
    return render_template('manageorder.html', orders=orders)


def deleteorder(order_id):
    order = Orders.query.get(order_id)
    for i in order.orders:
        product = Products.query.filter_by(barcode=i.barcode).first()
        product.quantity = product.quantity + int(i.quantity)
    db.session.commit()
    db.session.delete(order)
    db.session.commit()


@app.route("/order/delete/<int:order_id>", methods=['POST'])
@login_required
def delete_order(order_id):
    deleteorder(order_id)
    return redirect(url_for('manageorder'))


@app.route("/order/update/<int:order_id>", methods=['POST', 'GET'])
@login_required
def update_order(order_id):
    order = Orders.query.get(order_id)
    if request.method == 'POST':
        barcode = request.form.getlist('item_bar[]')
        qua = request.form.getlist('item_quantity[]')
        name = request.form.getlist('item_name[]')
        total = request.form.getlist('total[]')
        price = request.form.getlist('price[]')
        total_amount = request.form.get('total_amount')
        deleteorder(order_id)
        for n, q in zip(barcode, qua):
            product = Products.query.filter_by(barcode=n).first()
            if product.quantity > 0:
                product.quantity = product.quantity - int(q)
            else:
                print("you do not have this much of quantity", n)
        db.session.commit()

        add = Orders(total_amount=total_amount, user_order=current_user)
        db.session.add(add)
        db.session.commit()
        for q, p, t, n, b in zip(qua, price, total, name, barcode):
            ord = Orders_items(barcode=b, quantity=q, name=n,
                               price=p, total=t, Orders_items=add)
            db.session.add(ord)
        db.session.commit()

        return redirect(url_for('manageorder'))

    return render_template('update_order.html', order=order.orders, order_amount=order)


@app.route("/printInvoice/<int:order_id>")
@login_required
def printInvoice(order_id):
    order = Orders.query.get(order_id)
    renderd = render_template('print.html', order=order)
    css = ['orders/static/css/sb-admin-2.min.css']
    pdf = pdfkit.from_string(renderd, False, css=css)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename = {order_id}.pdf'
    return response
