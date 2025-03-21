from flask import send_file, render_template, redirect, url_for, flash, request, abort
from forms import *
from model import *
from database import create_app
from datetime import timedelta , datetime
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from html2image import Html2Image
from weasyprint import HTML
import io, os


app = create_app()
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(admin_id):
    return db.get_or_404(Admin, admin_id)

@app.route('/')
def home():
    if current_user.is_authenticated:
        clients = Client.query.filter_by(admin_id=current_user.id).all()
    
    else:
        clients = []
    return render_template('index.html', clients=clients)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUp()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )

        new_user = Admin(
            email=form.email.data,
            admin_name=form.name.data,
            password=hashed_password,
            phone_number=form.phone_number.data
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash('Account created and logged in successfully!', 'success')
        return redirect(url_for('home')) 
    
    return render_template('signup.html', form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        result = db.session.execute(db.select(Admin).where(Admin.email == email))
        user = result.scalar()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        
    return render_template("login.html", form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/add-client', methods=['GET', 'POST'])
def add_client():
    form = AddClient()
    if current_user.is_authenticated:
        current_admin_id = current_user.id
    else:
        return redirect('signup')
    if form.validate_on_submit():
        new_client = Client(
            name=form.name.data,
            street=form.street.data,
            city=form.city.data,
            phone_number=form.phone_number.data,
            admin_id = current_admin_id
        )
        
        db.session.add(new_client)
        db.session.commit()
        
        flash('User added successfully!')
        
        return redirect(url_for('home'))
    return render_template('add_client.html', form=form)

@app.route('/client/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    form = EditClientForm(obj=client)
    if form.validate_on_submit():
        client.name = form.name.data
        client.street = form.street.data
        client.city = form.city.data
        client.phone_number = form.phone_number.data
        
        db.session.commit()
        return redirect(url_for('client_info', client_id=client.id))
    
    return render_template('edit_client.html', form=form, client=client)

@app.route('/client/<int:client_id>')
@login_required
def client_info(client_id):
    client = Client.query.get_or_404(client_id)
    
    return render_template('client_info.html', client=client)

@app.route('/client/<int:client_id>/add_order', methods=['GET', 'POST'])
@login_required
def add_order(client_id):
    form = AddOrder()
    client = Client.query.get_or_404(client_id)
    if form.validate_on_submit():
        if current_user.is_authenticated:
            current_admin_id = current_user.id
        else:
            flash("please login for add Order!")
            return redirect('login')
        
        order_date = datetime.utcnow()
        deadline = order_date + timedelta(days=10)
        
        last_order = (
            Order.query.filter_by(client_id=client.id)
            .order_by(Order.order_number.desc())
            .first()
        )
        next_order_number = last_order.order_number + 1 if last_order else 1

        new_order =  Order(
            client_id=client.id,
            product_name=form.product_name.data,
            price=form.price.data,
            quantity=form.quantity.data,
            status="Pending",
            order_date=order_date,
            deadline=deadline,
            admin_id = current_admin_id,
            order_number=next_order_number
        )
        
        db.session.add(new_order)
        db.session.commit()
        flash('Order added successfully!', 'success')
        return redirect(url_for('client_info', client_id=client.id))
    
    return render_template('add_order.html', client=client, form=form)

@app.route('/admin/<int:admin_id>/order/<int:order_number>')
@login_required
def view_order(admin_id, order_number):
    order = Order.query.filter_by(admin_id=admin_id, order_number=order_number).first_or_404()
    if order.admin_id != current_user.id:
        flash("You are not authorized to view this order.")
        return redirect(url_for('home'))
    return render_template('view_order.html', order=order)

@app.route('/order/<int:order_id>/delete', methods=['POST'])
@login_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.admin_id != current_user.id:
        flash("You are not authorized to delete this order.")
        return redirect(url_for('home'))
    db.session.delete(order)
    db.session.commit()
    return redirect('client_info', client_id=order.client_id)


@app.route('/generate_invoice/<int:client_id>', methods=['GET'])
@login_required
def generate_invoice(client_id):
    # Fetch completed orders for the client
    orders = Order.query.filter_by(client_id=client_id, status='Completed').all()
    if not orders:
        return abort(404, "No completed orders found for this client")

    # Ensure the user is authenticated
    if current_user.is_authenticated:
        current_admin_id = current_user.id
    else:
        flash("Please log in to generate an invoice")
        return redirect('login')

    # Calculate total amount
    total_amount = sum(order.quantity * order.price for order in orders)
    current_date = datetime.now().strftime("%d-%m-%Y")

    # Fetch client details
    client = Client.query.get(client_id)
    if not client:
        return abort(404, "Client not found")
    client_name = client.name

    # Generate the next invoice number
    last_invoice = (
        Invoice.query.filter_by(admin_id=current_admin_id)
        .order_by(Invoice.invoice_number.desc())
        .first()
    )
    next_invoice_number = (last_invoice.invoice_number + 1) if last_invoice else 1

    # Render HTML template for the invoice
    rendered_html = render_template(
        "invoice_template.html",
        client_name=client_name,
        current_date=current_date,
        orders=orders,
        total_amount=total_amount,
    )

    # Generate the PDF using WeasyPrint
    pdf_io = io.BytesIO()
    HTML(string=rendered_html).write_pdf(pdf_io)
    pdf_io.seek(0)

    # Save the invoice record to the database
    invoice_filename = f"{client_name.replace(' ', '')}_invoice.pdf"
    new_invoice = Invoice(
        order_id=orders[0].id,
        invoice_image=invoice_filename,
        generated_at=datetime.utcnow(),
        admin_id=current_admin_id,
        invoice_number=next_invoice_number
    )
    db.session.add(new_invoice)
    db.session.commit()

    # Return the PDF file as a downloadable response
    return send_file(
        pdf_io,
        as_attachment=True,
        download_name=invoice_filename,
        mimetype='application/pdf'
    )

    
@app.route('/invoices', methods=['GET'])
@login_required
def invoices():
    invoices = Invoice.query.filter_by(admin_id=current_user.id).order_by(Invoice.generated_at.desc()).all()
    return render_template('invoices_list.html', invoices=invoices)

@app.route('/view_invoice/<int:invoice_number>', methods=['GET'])
@login_required
def view_invoice(invoice_number):
    invoice = Invoice.query.filter_by(invoice_number=invoice_number, admin_id=current_user.id).first_or_404()
    return render_template('invoice_detail.html', invoice=invoice)

@app.route('/download_invoice/<int:invoice_id>', methods=['GET'])
@login_required
def download_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    orders = Order.query.filter_by(id=invoice.order_id).all()
    
    if not orders:
        return "No orders found for this invoice", 404
    
    total_amount = sum(order.quantity * order.price for order in orders)
    current_date = datetime.now().strftime("%d-%m-%Y")
    
    client = Client.query.get(orders[0].client_id)
    client_name = client.name if client else "Unknown Client"
    
    rendered_html = render_template(
        "invoice_template.html",
        client_name=client_name,
        current_date=current_date,
        orders=orders,
        total_amount=total_amount
    )
    
    hti = Html2Image()
    hti.browser.viewport_size = (1080, 2000)
    hti.size = (1080, 1920)
    temp_file = 'temp_invoice.png'
    hti.screenshot(html_str=rendered_html, save_as=temp_file)

    with open(temp_file, "rb") as img_file:
        img_data = img_file.read()

    img_io = io.BytesIO()
    img_io.write(img_data)
    img_io.seek(0)
    os.remove(temp_file)

    invoice_filename = f"{client_name.replace(' ', '')}_invoice.jpg"
    
    return send_file(
        img_io,
        as_attachment=True,
        download_name=invoice_filename,
        mimetype='image/jpeg'
    )
    
    
@app.route('/view_invoice/<int:invoice_id>', methods=["POST"])
@login_required
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    db.session.delete(invoice)
    db.session.commit()
    
    return redirect(url_for('invoices'))

@app.route('/edit_order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)
    form = EditOrderForm()
    print(order)

    if form.validate_on_submit():
        order.product_name = form.product_name.data
        order.status = form.status.data
        order.price = form.price.data
        order.order_date = form.order_date.data
        order.deadline = form.deadline.data

        db.session.commit()
        flash('Order updated successfully!', 'success')
        return redirect(url_for('client_info', client_id=order.client_id))
    
    form.product_name.data = order.product_name
    form.status.data = order.status
    form.price.data = order.price
    form.order_date.data = order.order_date
    form.deadline.data = order.deadline

    return render_template('edit_order.html', form=form, order=order)


@app.route('/pending-orders', methods=["GET", "POST"])
@login_required
def pending_orders():
    pending_orders = Order.query.filter_by(admin_id=current_user.id, status='Pending').all()
    
    return render_template('pending_orders.html', orders=pending_orders)

@app.route('/orders', methods=['GET'])
@login_required
def orders():
    current_year = int(request.args.get('year', datetime.now().year))
    month = request.args.get('month', None)
    if month:
        month = int(month)
        
        orders = Order.query.filter(
            db.extract('year', Order.order_date) == current_year,
            db.extract('month', Order.order_date) == int(month),
            Order.admin_id == current_user.id
        ).all()
        
        total_earnings = db.session.query(db.func.sum(Order.price * Order.quantity)).filter(
            db.extract('year', Order.order_date) == current_year,
            db.extract('month', Order.order_date) == month,
            Order.status == 'Paid'
        ).scalar() or 0
    else:
        orders = []
        total_earnings = 0

    return render_template('all_orders.html', current_year=current_year, orders=orders, month=month, total_earnings=total_earnings)


@app.route('/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('query')
    if query:
        order_query = Order.query.filter( 
        (Order.product_name.ilike(f"%{query}%")) | 
        (Order.client.has(Client.name.ilike(f"%{query}%"))) |
        (Order.status.ilike(f"%{query}%"))).filter_by(admin_id=current_user.id)
        orders = order_query.all()
    else:
        orders = Order.query.all()
    return render_template('search_results.html', orders=orders)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)