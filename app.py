from flask import Flask, request, redirect, render_template_string, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from dateutil.parser import parse
from markupsafe import escape
import logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Secure secret key
db = SQLAlchemy(app)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    production_date = db.Column(db.String(10), nullable=False)
    expiry_date = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Product {self.name}>'

def init_db():
    with app.app_context():
        db.create_all()

def validate_date(date_str):
    try:
        parsed_date = parse(date_str, fuzzy=False)
        if parsed_date > datetime.now() + timedelta(days=365*5):  # Prevent far-future dates
            return None
        return parsed_date.strftime('%Y-%m-%d')
    except ValueError:
        return None

def get_near_expiry(days=7):
    try:
        near_expiry = []
        now = datetime.now()
        products = Product.query.all()
        for product in products:
            try:
                expiry_date = parse(product.expiry_date)
                if 0 <= (expiry_date - now).days <= days:
                    near_expiry.append((product.name, product.expiry_date))
            except ValueError:
                logger.warning(f"Invalid date format for product {product.name}")
                continue
        return sorted(near_expiry, key=lambda x: parse(x[1]))  # Sort by expiry date
    except Exception as e:
        logger.error(f"Error in get_near_expiry: {str(e)}")
        return []

# HTML Template with enhanced features and accessibility
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="نظام إدارة المنتجات لتتبع تواريخ الإنتاج والانتهاء">
    <title>نظام إدارة المنتجات</title>
    <style>
        :root {
            --primary-color: #0057b8;
            --danger-color: #dc3545;
            --success-color: #28a745;
            --background-color: #f8fafc;
            --card-background: #ffffff;
            --text-color: #333333;
            --border-radius: 0.5rem;
        }
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: var(--background-color);
            color: var(--text-color);
            padding: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            line-height: 1.6;
        }
        .container {
            max-width: 900px;
            width: 100%;
        }
        h1 {
            color: var(--primary-color);
            margin-bottom: 2rem;
            text-align: center;
            font-size: 2rem;
        }
        .card {
            background-color: var(--card-background);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        form {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        .form-group {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }
        label {
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--text-color);
        }
        input[type="text"], input[type="date"] {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #ced4da;
            border-radius: 0.25rem;
            font-size: 1rem;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        input[type="text"]:focus, input[type="date"]:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(0, 87, 184, 0.2);
        }
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 0.25rem;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: background-color 0.2s, transform 0.1s;
        }
        .btn-primary {
            background-color: var(--primary-color);
            color: white;
        }
        .btn-primary:hover, .btn-primary:focus {
            background-color: #003d82;
            transform: translateY(-1px);
        }
        .btn-danger {
            background-color: var(--danger-color);
            color: white;
        }
        .btn-danger:hover, .btn-danger:focus {
            background-color: #b02a37;
            transform: translateY(-1px);
        }
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 1rem;
            background-color: var(--card-background);
        }
        th, td {
            padding: 1rem;
            text-align: right;
            border-bottom: 1px solid #dee2e6;
        }
        th {
            background-color: var(--primary-color);
            color: white;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        tr:hover {
            background-color: #f1f5f9;
        }
        .alert {
            padding: 1rem;
            border-radius: 0.25rem;
            margin-bottom: 1rem;
            text-align: center;
            font-weight: 500;
        }
        .alert-success {
            background-color: #d4edda;
            color: #155724;
        }
        .alert-danger {
            background-color: #f8d7da;
            color: #721c24;
        }
        .links {
            margin-top: 1.5rem;
            text-align: center;
        }
        .links a {
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
            padding: 0.5rem 1rem;
            transition: color 0.2s;
        }
        .links a:hover, .links a:focus {
            color: #003d82;
 REPLACED
            text-decoration: underline;
        }
        .no-products {
            text-align: center;
            color: var(--text-color);
            padding: 1rem;
        }
        @media (max-width: 600px) {
            .container {
                padding: 0 1rem;
            }
            table {
                font-size: 0.9rem;
            }
            th, td {
                padding: 0.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="container" role="main">
        <h1>إدارة المنتجات</h1>
        <div class="card" role="region" aria-label="إضافة منتج">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}" role="alert">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="POST" id="productForm" aria-label="نموذج إضافة منتج">
                <div class="form-group">
                    <label for="name">اسم المنتج</label>
                    <input type="text" id="name" name="name" placeholder="أدخل اسم المنتج" required maxlength="100" aria-required="true">
                </div>
                <div class="form-group">
                    <label for="production_date">تاريخ الإنتاج</label>
                    <input type="date" id="production_date" name="production_date" required aria-required="true">
                </div>
                <div class="form-group">
                    <label for="expiry_date">تاريخ الانتهاء</label>
                    <input type="date" id="expiry_date" name="expiry_date" required aria-required="true">
                </div>
                <button type="submit" class="btn btn-primary" aria-label="إضافة المنتج">إضافة المنتج</button>
            </form>
        </div>

        <div class="card" role="region" aria-label="قائمة المنتجات">
            <h2>قائمة المنتجات</h2>
            {% if products %}
            <table role="grid">
                <thead>
                    <tr>
                        <th scope="col">اسم المنتج</th>
                        <th scope="col">تاريخ الإنتاج</th>
                        <th scope="col">تاريخ الانتهاء</th>
                        <th scope="col">إجراءات</th>
                    </tr>
                </thead>
                <tbody>
                    {% for product in products %}
                    <tr role="row">
                        <td>{{ product.name | e }}</td>
                        <td>{{ product.production_date }}</td>
                        <td>{{ product.expiry_date }}</td>
                        <td>
                            <form method="POST" action="{{ url_for('delete', product_id=product.id) }}" style="display: inline;">
                                <button type="submit" class="btn btn-danger" onclick="return confirm('هل أنت متأكد من حذف هذا المنتج؟')" aria-label="حذف المنتج {{ product.name | e }}">حذف</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
                <p class="no-products">لا توجد منتجات مسجلة حالياً.</p>
            {% endif %}
        </div>

        <div class="links">
            <a href="{{ url_for('near_expiry') }}" aria-label="عرض المنتجات القريبة من الانتهاء">عرض المنتجات القريبة من الانتهاء</a>
        </div>
    </div>

    <script>
        document.getElementById('productForm').addEventListener('submit', function(e) {
            const prodDate = new Date(document.getElementById('production_date').value);
            const expDate = new Date(document.getElementById('expiry_date').value);
            const name = document.getElementById('name').value.trim();
            
            if (!name) {
                e.preventDefault();
                alert('الرجاء إدخال اسم المنتج');
                return;
            }
            if (!document.getElementById('production_date').value || !document.getElementById('expiry_date').value) {
                e.preventDefault();
                alert('الرجاء إدخال جميع التواريخ');
                return;
            }
            if (expDate <= prodDate) {
                e.preventDefault();
                alert('تاريخ الانتهاء يجب أن يكون بعد تاريخ الإنتاج');
                return;
            }
            if (expDate > new Date().setFullYear(new Date().getFullYear() + 5)) {
                e.preventDefault();
                alert('تاريخ الانتهاء بعيد جدًا في المستقبل');
                return;
            }
        });
    </script>
</body>
</html>
'''

NEAR_EXPIRY_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="عرض المنتجات التي ستنتهي صلاحيتها خلال 7 أيام">
    <title>منتجات قريبة الانتهاء</title>
    <style>
        :root {
            --primary-color: #0057b8;
            --warning-color: #dc3545;
            --background-color: #f8fafc;
            --card-background: #ffffff;
            --text-color: #333333;
        }
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: var(--background-color);
            color: var(--text-color);
            padding: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            line-height: 1.6;
        }
        .container {
            max-width: 600px;
            width: 100%;
        }
        h1 {
            color: var(--warning-color);
            margin-bottom: 2rem;
            text-align: center;
            font-size: 2rem;
        }
        .card {
            background-color: var(--card-background);
            border-radius: 0.5rem;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        ul {
            list-style-type: none;
            padding: 0;
        }
        li {
            background-color: #ffe6e6;
            margin: 0.5rem 0;
            padding: 1rem;
            border-radius: 0.25rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: transform 0.2s;
        }
        li:hover {
            transform: translateX(5px);
        }
        a {
            display: inline-block;
            margin-top: 1.5rem;
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
            padding: 0.5rem 1rem;
        }
        a:hover, a:focus {
            text-decoration: underline;
        }
        .no-products {
            text-align: center;
            color: var(--text-color);
            padding: 1rem;
        }
        @media (max-width: 600px) {
            .container {
                padding: 0 1rem;
            }
            li {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="container" role="main">
        <h1>منتجات تنتهي خلال 7 أيام</h1>
        <div class="card" role="region" aria-label="قائمة المنتجات القريبة من الانتهاء">
            {% if products %}
                <ul role="list">
                    {% for name, expiry_date in products %}
                        <li role="listitem"><strong>{{ name | e }}</strong> - ينتهي في: {{ expiry_date }}</li>
                    {% endfor %}
                </ul>
            {% else %}
                <p class="no-products">لا توجد منتجات قريبة من الانتهاء.</p>
            {% endif %}
        </div>
        <a href="{{ url_for('index') }}" aria-label="العودة إلى الصفحة الرئيسية">رجوع إلى الصفحة الرئيسية</a>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name'].strip()
        production_date = request.form['production_date']
        expiry_date = request.form['expiry_date']
        
        prod_date = validate_date(production_date)
        exp_date = validate_date(expiry_date)
        
        if not name:
            flash('الرجاء إدخال اسم المنتج', 'danger')
            logger.warning('Attempt to add product with empty name')
        elif len(name) > 100:
            flash('اسم المنتج طويل جدًا (الحد الأقصى 100 حرف)', 'danger')
            logger.warning('Attempt to add product with name exceeding 100 characters')
        elif not prod_date or not exp_date:
            flash('خطأ في تنسيق التواريخ. الرجاء استخدام تنسيق صحيح', 'danger')
            logger.warning('Invalid date format in product submission')
        elif parse(exp_date) <= parse(prod_date):
            flash('تاريخ الانتهاء يجب أن يكون بعد تاريخ الإنتاج', 'danger')
            logger.warning('Expiry date before production date')
        else:
            try:
                product = Product(name=escape(name), production_date=prod_date, expiry_date=exp_date)
                db.session.add(product)
                db.session.commit()
                flash('تم إضافة المنتج بنجاح', 'success')
                logger.info(f'Product added: {name}')
            except Exception as e:
                db.session.rollback()
                flash('حدث خطأ أثناء إضافة المنتج', 'danger')
                logger.error(f'Error adding product: {str(e)}')
        
        return redirect(url_for('index'))

    try:
        products = Product.query.order_by(Product.expiry_date.asc()).all()
    except Exception as e:
        logger.error(f'Error fetching products: {str(e)}')
        products = []
        flash('حدث خطأ أثناء جلب قائمة المنتجات', 'danger')
    
    return render_template_string(HTML_TEMPLATE, products=products)

@app.route('/delete/<int:product_id>', methods=['POST'])
def delete(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        db.session.delete(product)
        db.session.commit()
        flash('تم حذف المنتج بنجاح', 'success')
        logger.info(f'Product deleted: {product.name}')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء حذف المنتج', 'danger')
        logger.error(f'Error deleting product {product_id}: {str(e)}')
    return redirect(url_for('index'))

@app.route('/near-expiry')
def near_expiry():
    products = get_near_expiry()
    return render_template_string(NEAR_EXPIRY_TEMPLATE, products=products)

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=5000)