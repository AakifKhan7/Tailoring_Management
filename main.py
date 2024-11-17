from flask import send_file, render_template, redirect, url_for, flash, request, abort
from forms import *
from model import *
from database import create_app
from datetime import timedelta , datetime
from sqlalchemy import extract
from html2image import Html2Image
import io, os


app = create_app()

@app.route('/')
def home():
    clients = Client.query.all()
    return render_template('index.html', clients=clients)
    # orders = Order.query.all()
    # return render_template(
    #     "invoice_template.html",
    #     client_name="aakif",
    #     current_date="17-11-2024",
    #     orders=orders,
    #     total_amount=500
    # )

@app.route('/add-client', methods=['GET', 'POST'])
def add_client():
    form = AddClient()
    if form.validate_on_submit():
        new_client = Client(
            name=form.name.data,
            street=form.street.data,
            city=form.city.data,
            phone_number=form.phone_number.data
        )
        
        db.session.add(new_client)
        db.session.commit()
        
        flash('User added successfully!')
        
        return redirect(url_for('home'))
    return render_template('add_client.html', form=form)

@app.route('/client/<int:client_id>/edit', methods=['GET', 'POST'])
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
def client_info(client_id):
    client = Client.query.get_or_404(client_id)
    
    return render_template('client_info.html', client=client)

@app.route('/client/<int:client_id>/add_order', methods=['GET', 'POST'])
def add_order(client_id):
    form = AddOrder()
    client = Client.query.get_or_404(client_id)
    if form.validate_on_submit():
        
        order_date = datetime.utcnow()
        deadline = order_date + timedelta(days=7)

        new_order =  Order(
            client_id=client.id,
            product_name=form.product_name.data,
            price=form.price.data,
            quantity=form.quantity.data,
            status="Pending",
            order_date=order_date,
            deadline=deadline
        )
        
        db.session.add(new_order)
        db.session.commit()
        flash('Order added successfully!', 'success')
        return redirect(url_for('client_info', client_id=client.id))
    
    return render_template('add_order.html', client=client, form=form)

@app.route('/order/<int:order_id>')
def view_order(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('view_order.html', order=order)

@app.route('/order/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/generate_invoice/<int:client_id>', methods=['GET'])
def generate_invoice(client_id):
    orders = Order.query.filter_by(client_id=client_id, status='Completed').all()
    if not orders:
        return abort(404, "No completed orders found for this client")

    total_amount = sum(order.quantity * order.price for order in orders)
    current_date = datetime.now().strftime("%d-%m-%Y")

    client = Client.query.get(client_id)
    if not client:
        return abort(404, "Client not found")
    client_name = client.name

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

    new_invoice = Invoice(
        order_id=orders[0].id,
        invoice_image=invoice_filename,
        generated_at=datetime.utcnow()
    )
    db.session.add(new_invoice)
    db.session.commit()

    return send_file(
        img_io,
        as_attachment=True,
        download_name=invoice_filename,
        mimetype='image/jpeg'
    )
    
    
@app.route('/invoices', methods=['GET'])
def invoices():
    invoices = Invoice.query.order_by(Invoice.generated_at.desc()).all()
    return render_template('invoices_list.html', invoices=invoices)

@app.route('/view_invoice/<int:invoice_id>', methods=['GET'])
def view_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('invoice_detail.html', invoice=invoice)

@app.route('/download_invoice/<int:invoice_id>', methods=['GET'])
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
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    db.session.delete(invoice)
    db.session.commit()
    
    return redirect(url_for('invoices'))

@app.route('/edit_order/<int:order_id>', methods=['GET', 'POST'])
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
def pending_orders():
    pending_orders = Order.query.filter_by(status='Pending').all()
    
    return render_template('pending_orders.html', orders=pending_orders)


@app.route('/orders', methods=['GET'])
def orders():
    current_year = int(request.args.get('year', datetime.now().year))
    month = request.args.get('month', None)
    if month:
        month = int(month)
        
        orders = Order.query.filter(
            db.extract('year', Order.order_date) == current_year,
            db.extract('month', Order.order_date) == int(month)
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
def search():
    query = request.args.get('query')
    if query:
        order_query = Order.query.filter(
            (Order.id.ilike(f'%{query}%')) | 
            (Order.product_name.ilike(f'%{query}%')) | 
            (Order.client.has(Client.name.ilike(f'%{query}%'))) |
            (Order.status.ilike(f'%{query}%'))
        )
        orders = order_query.all()
    else:
        orders = Order.query.all()
    return render_template('search_results.html', orders=orders)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)