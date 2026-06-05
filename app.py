import os
import sqlite3
import uuid
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ---------- ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ----------
def init_db():
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        product_id INTEGER,
        product_name TEXT,
        price INTEGER,
        status TEXT DEFAULT 'pending',
        screenshot TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price INTEGER NOT NULL,
        in_stock INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('SELECT COUNT(*) FROM products')
    if c.fetchone()[0] == 0:
        test_products = [
            ('🇺🇸 США (USA) — виртуальный номер', 80, 1),
            ('🇨🇦 Канада (Canada) — виртуальный номер', 65, 1),
            ('🇷🇺 Россия (новорег) — виртуальный номер', 140, 1),
            ('🇬🇧 Великобритания — виртуальный номер', 120, 1),
            ('🇩🇪 Германия — виртуальный номер', 110, 1),
            ('🇧🇩 Бангладеш — виртуальный номер', 90, 1),
            ('🇵🇭 Филиппины — виртуальный номер', 65, 1),
            ('🇳🇬 Нигерия — виртуальный номер', 60, 1),
            ('🇮🇳 Индия — виртуальный номер', 50, 1)
        ]
        c.executemany('INSERT INTO products (name, price, in_stock) VALUES (?, ?, ?)', test_products)
        conn.commit()
    conn.close()

init_db()

# ---------- HTML (ФРОНТЕНД С АДМИНКОЙ ПО ПАРОЛЮ) ----------
MAIN_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>HowScad — магазин</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0f;
            color: #fff;
            padding: 20px;
        }
        .container { max-width: 700px; margin: 0 auto; }
        .card {
            background: rgba(18, 24, 34, 0.9);
            backdrop-filter: blur(12px);
            border-radius: 32px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid rgba(38, 165, 228, 0.3);
        }
        h1 { font-size: 1.8rem; background: linear-gradient(135deg, #fff, #26a5e4); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .sub { color: #9ca3af; margin: 8px 0 24px; }
        .admin-link {
            text-align: right;
            margin-bottom: 16px;
        }
        .admin-link a {
            color: #26a5e4;
            font-size: 0.7rem;
            text-decoration: none;
        }
        .product-list { display: flex; flex-direction: column; gap: 12px; }
        .product-item {
            background: rgba(255,255,255,0.05);
            border-radius: 28px;
            padding: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }
        .stock-badge { padding: 4px 12px; border-radius: 40px; font-size: 0.75rem; }
        .in-stock { background: #10b981; }
        .out-stock { background: #e53e3e; }
        button, .btn {
            background: #26a5e4;
            border: none;
            padding: 8px 20px;
            border-radius: 40px;
            color: white;
            cursor: pointer;
        }
        .input-field, .file-area {
            background: rgba(0,0,0,0.6);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 60px;
            padding: 12px 20px;
            width: 100%;
            color: white;
            margin-bottom: 16px;
        }
        .file-area {
            text-align: center;
            cursor: pointer;
        }
        .preview-img { max-width: 100%; max-height: 120px; border-radius: 16px; margin-top: 10px; display: none; }
        .toast {
            position: fixed;
            bottom: 20px;
            left: 20px;
            right: 20px;
            background: #26a5e4;
            padding: 12px;
            border-radius: 60px;
            text-align: center;
            transform: translateY(100px);
            transition: 0.3s;
            z-index: 1000;
        }
        .toast.show { transform: translateY(0); }
        .toast.error { background: #e53e3e; }
        .order-form { display: none; margin-top: 20px; }
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <div class="admin-link">
            <a href="#" id="adminLoginLink">🔐 Админ-панель</a>
        </div>
        <h1>HowScad</h1>
        <div class="sub">Виртуальные номера для Telegram</div>

        <div id="shopProductsList" class="product-list"></div>

        <div id="orderForm" class="order-form">
            <input type="text" id="orderUsername" class="input-field" placeholder="Telegram username (5-7 символов, латиница, цифры, _)">
            <div class="file-area" id="fileArea">
                📸 Нажмите или перетащите скриншот чека
                <input type="file" id="screenshotFile" accept="image/*" style="display: none;">
                <div id="fileName"></div>
                <img id="preview" class="preview-img">
            </div>
            <button id="submitOrderBtn" class="btn">✅ Оплатил → отправить заказ</button>
            <button id="cancelOrderBtn" class="btn" style="background:#333; margin-top:8px;">← Назад</button>
        </div>
    </div>
</div>
<div id="toast" class="toast"></div>

<script>
    let currentProduct = null;
    let selectedFile = null;

    function showMsg(msg, isError = false) {
        const toast = document.getElementById('toast');
        toast.textContent = msg;
        toast.classList.add('show');
        if (isError) toast.classList.add('error');
        else toast.classList.remove('error');
        setTimeout(() => toast.classList.remove('show'), 3000);
    }

    function isValidUsername(username) {
        if (!username) return false;
        let clean = username.trim();
        if (clean.startsWith('@')) clean = clean.substring(1);
        return clean.length >= 5 && clean.length <= 7 && /^[a-zA-Z0-9_]+$/.test(clean);
    }

    async function loadProducts() {
        const res = await fetch('/api/products');
        const products = await res.json();
        const container = document.getElementById('shopProductsList');
        container.innerHTML = products.map(p => `
            <div class="product-item" data-id="${p.id}">
                <div>
                    <strong>${p.name}</strong> — ${p.price} ₽
                    ${p.in_stock ? '<span class="stock-badge in-stock">✅ в наличии</span>' : '<span class="stock-badge out-stock">❌ нет</span>'}
                </div>
                ${p.in_stock ? `<button class="buy-btn" data-id="${p.id}" data-name="${p.name}" data-price="${p.price}">Купить</button>` : '<button disabled style="opacity:0.5;">Нет в наличии</button>'}
            </div>
        `).join('');
        document.querySelectorAll('.buy-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                currentProduct = {
                    id: btn.dataset.id,
                    name: btn.dataset.name,
                    price: parseInt(btn.dataset.price)
                };
                document.getElementById('orderForm').style.display = 'block';
                document.getElementById('orderUsername').value = '';
                selectedFile = null;
                document.getElementById('screenshotFile').value = '';
                document.getElementById('fileName').innerHTML = '';
                document.getElementById('preview').style.display = 'none';
                showMsg(`Вы выбрали: ${currentProduct.name}`);
            });
        });
    }

    // Отправка заказа
    document.getElementById('submitOrderBtn').addEventListener('click', async () => {
        if (!currentProduct) {
            showMsg('Сначала выберите товар', true);
            return;
        }
        const username = document.getElementById('orderUsername').value.trim();
        if (!isValidUsername(username)) {
            showMsg('❌ Укажите корректный username: 5-7 символов, латиница, цифры, _', true);
            return;
        }
        if (!selectedFile) {
            showMsg('❌ Прикрепите скриншот чека', true);
            return;
        }
        const formData = new FormData();
        formData.append('username', username);
        formData.append('product_id', currentProduct.id);
        formData.append('screenshot', selectedFile);
        const res = await fetch('/api/orders', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.ok) {
            showMsg('✅ Заказ отправлен! Админ проверит оплату.');
            document.getElementById('orderForm').style.display = 'none';
            currentProduct = null;
            selectedFile = null;
        } else {
            showMsg('❌ Ошибка: ' + (data.error || 'unknown'), true);
        }
    });

    document.getElementById('cancelOrderBtn').addEventListener('click', () => {
        document.getElementById('orderForm').style.display = 'none';
        currentProduct = null;
    });

    // Работа с файлом
    const fileArea = document.getElementById('fileArea');
    const fileInput = document.getElementById('screenshotFile');
    fileArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            selectedFile = e.target.files[0];
            document.getElementById('fileName').innerHTML = `✅ ${selectedFile.name}`;
            const reader = new FileReader();
            reader.onload = (ev) => {
                const preview = document.getElementById('preview');
                preview.src = ev.target.result;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(selectedFile);
        }
    });

    // Админ-панель (открывается по паролю)
    document.getElementById('adminLoginLink').addEventListener('click', (e) => {
        e.preventDefault();
        const password = prompt('Введите пароль администратора:');
        if (password === 'admin123') {
            window.location.href = '/admin?key=' + encodeURIComponent(password);
        } else {
            showMsg('Неверный пароль', true);
        }
    });

    loadProducts();
</script>
</body>
</html>
'''

ADMIN_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Админ-панель HowScad</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0f;
            color: #fff;
            padding: 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        .card {
            background: rgba(18, 24, 34, 0.9);
            border-radius: 32px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid rgba(38, 165, 228, 0.3);
        }
        h1, h2 { margin-bottom: 20px; }
        .tabs {
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }
        .tab {
            background: rgba(255,255,255,0.05);
            padding: 10px 20px;
            border-radius: 60px;
            cursor: pointer;
        }
        .tab.active { background: #26a5e4; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .product-list, .orders-list { display: flex; flex-direction: column; gap: 16px; }
        .product-item, .order-item {
            background: rgba(255,255,255,0.05);
            border-radius: 28px;
            padding: 16px;
        }
        .edit-input {
            background: #1e293b;
            border: 1px solid #26a5e4;
            border-radius: 40px;
            padding: 6px 12px;
            color: white;
            margin-right: 8px;
        }
        button, .btn {
            background: #26a5e4;
            border: none;
            padding: 6px 16px;
            border-radius: 40px;
            color: white;
            cursor: pointer;
            margin-right: 8px;
        }
        .delete-btn { background: #e53e3e; }
        img { max-width: 200px; border-radius: 16px; margin-top: 10px; }
        .toast {
            position: fixed;
            bottom: 20px;
            left: 20px;
            right: 20px;
            background: #26a5e4;
            padding: 12px;
            border-radius: 60px;
            text-align: center;
            transform: translateY(100px);
            transition: 0.3s;
            z-index: 1000;
        }
        .toast.show { transform: translateY(0); }
        .toast.error { background: #e53e3e; }
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <h1>👑 Админ-панель</h1>
        <div class="tabs">
            <div class="tab active" data-tab="products">📦 Товары</div>
            <div class="tab" data-tab="orders">📋 Заказы</div>
        </div>

        <div id="products-tab" class="tab-content active">
            <button id="addProductBtn" class="btn" style="margin-bottom: 20px;">+ Добавить товар</button>
            <div id="productsList" class="product-list"></div>
        </div>

        <div id="orders-tab" class="tab-content">
            <div id="ordersList" class="orders-list"></div>
        </div>
    </div>
</div>
<div id="toast" class="toast"></div>

<script>
    let ADMIN_KEY = new URLSearchParams(window.location.search).get('key');

    function showMsg(msg, isError = false) {
        const toast = document.getElementById('toast');
        toast.textContent = msg;
        toast.classList.add('show');
        if (isError) toast.classList.add('error');
        else toast.classList.remove('error');
        setTimeout(() => toast.classList.remove('show'), 3000);
    }

    // ---------- ТОВАРЫ ----------
    async function loadProducts() {
        const res = await fetch('/api/products');
        const products = await res.json();
        const container = document.getElementById('productsList');
        container.innerHTML = products.map(p => `
            <div class="product-item" data-id="${p.id}">
                <div>
                    <input type="text" id="name-${p.id}" value="${p.name.replace(/"/g, '&quot;')}" class="edit-input" style="width:250px;">
                    <input type="number" id="price-${p.id}" value="${p.price}" class="edit-input" style="width:80px;">
                    <select id="stock-${p.id}" class="edit-input">
                        <option value="1" ${p.in_stock ? 'selected' : ''}>✅ В наличии</option>
                        <option value="0" ${!p.in_stock ? 'selected' : ''}>❌ Нет</option>
                    </select>
                </div>
                <div>
                    <button onclick="saveProduct(${p.id})">💾 Сохранить</button>
                    <button onclick="deleteProduct(${p.id})" class="delete-btn">🗑 Удалить</button>
                </div>
            </div>
        `).join('');
    }

    window.saveProduct = async function(id) {
        const name = document.getElementById(`name-${id}`).value;
        const price = parseInt(document.getElementById(`price-${id}`).value);
        const in_stock = parseInt(document.getElementById(`stock-${id}`).value);
        const res = await fetch('/api/products/' + id, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, price, in_stock })
        });
        if (res.ok) {
            showMsg('Товар обновлён');
            loadProducts();
            loadShopProducts();
        } else {
            showMsg('Ошибка', true);
        }
    };

    window.deleteProduct = async function(id) {
        if (!confirm('Удалить товар?')) return;
        const res = await fetch('/api/products/' + id, { method: 'DELETE' });
        if (res.ok) {
            showMsg('Товар удалён');
            loadProducts();
            loadShopProducts();
        } else {
            showMsg('Ошибка', true);
        }
    };

    document.getElementById('addProductBtn').addEventListener('click', async () => {
        const name = prompt('Название товара:');
        const price = parseInt(prompt('Цена:'));
        if (!name || !price) return;
        const res = await fetch('/api/products', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, price, in_stock: 1 })
        });
        if (res.ok) {
            showMsg('Товар добавлен');
            loadProducts();
            loadShopProducts();
        } else {
            showMsg('Ошибка', true);
        }
    });

    // ---------- ЗАКАЗЫ ----------
    async function loadOrders() {
        const res = await fetch(`/api/orders?key=${ADMIN_KEY}`);
        if (!res.ok) {
            showMsg('Ошибка загрузки заказов', true);
            return;
        }
        const orders = await res.json();
        const container = document.getElementById('ordersList');
        if (orders.length === 0) {
            container.innerHTML = '<div style="text-align:center;">Заказов пока нет</div>';
            return;
        }
        container.innerHTML = orders.map(o => `
            <div class="order-item">
                <p><strong>🆔 ${o.id}</strong> — ${o.created_at}</p>
                <p>👤 ${o.username}</p>
                <p>📦 ${o.product_name} — ${o.price} ₽</p>
                <p>Статус: ${o.status === 'pending' ? '⏳ Ожидает' : (o.status === 'approved' ? '✅ Принят' : '❌ Отклонён')}</p>
                ${o.screenshot ? `<a href="${o.screenshot}" target="_blank">📸 Скриншот чека</a><br>` : ''}
                ${o.status === 'pending' ? `
                    <button onclick="updateStatus('${o.id}', 'approved')">✅ Принять</button>
                    <button onclick="updateStatus('${o.id}', 'rejected')" style="background:#e53e3e;">❌ Отклонить</button>
                ` : ''}
            </div>
        `).join('');
    }

    window.updateStatus = async function(orderId, status) {
        const res = await fetch(`/api/orders/${orderId}?key=${ADMIN_KEY}&status=${status}`, { method: 'PUT' });
        if (res.ok) {
            showMsg('Статус обновлён');
            loadOrders();
        } else {
            showMsg('Ошибка', true);
        }
    };

    // ---------- ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК ----------
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`${tabName}-tab`).classList.add('active');
            if (tabName === 'products') loadProducts();
            if (tabName === 'orders') loadOrders();
        });
    });

    // Функция для обновления витрины (магазина) через AJAX
    async function loadShopProducts() {
        const res = await fetch('/api/products');
        // ничего не делаем, просто чтобы была синхронизация
    }

    loadProducts();
</script>
</body>
</html>
'''

# ---------- API МАРШРУТЫ ----------
@app.route('/')
def index():
    return MAIN_HTML

@app.route('/admin')
def admin_panel():
    key = request.args.get('key')
    if key != 'admin123':
        return 'Доступ запрещён. Используйте /admin?key=admin123', 403
    return ADMIN_HTML

@app.route('/api/products')
def get_products():
    conn = sqlite3.connect('shop.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM products ORDER BY id')
    products = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('INSERT INTO products (name, price, in_stock) VALUES (?, ?, ?)',
              (data['name'], data['price'], data.get('in_stock', 1)))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.json
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('UPDATE products SET name=?, price=?, in_stock=? WHERE id=?',
              (data['name'], data['price'], data['in_stock'], product_id))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id=?', (product_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/orders', methods=['POST'])
def create_order():
    username = request.form.get('username')
    product_id = request.form.get('product_id')
    screenshot = request.files.get('screenshot')

    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT name, price FROM products WHERE id=?', (product_id,))
    product = c.fetchone()
    if not product:
        conn.close()
        return jsonify({'error': 'Product not found'}), 404

    order_id = str(uuid.uuid4())[:8]
    screenshot_path = ''
    if screenshot:
        ext = screenshot.filename.rsplit('.', 1)[-1].lower()
        filename = f"{order_id}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        screenshot.save(filepath)
        screenshot_path = f"/uploads/{filename}"

    c.execute('''INSERT INTO orders (id, username, product_id, product_name, price, screenshot)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (order_id, username, product_id, product[0], product[1], screenshot_path))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'order_id': order_id})

@app.route('/api/orders')
def get_orders():
    key = request.args.get('key')
    if key != 'admin123':
        return jsonify({'error': 'Unauthorized'}), 403
    conn = sqlite3.connect('shop.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM orders ORDER BY created_at DESC')
    orders = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(orders)

@app.route('/api/orders/<order_id>', methods=['PUT'])
def update_order_status(order_id):
    key = request.args.get('key')
    status = request.args.get('status')
    if key != 'admin123':
        return jsonify({'error': 'Unauthorized'}), 403
    if status not in ('approved', 'rejected'):
        return jsonify({'error': 'Invalid status'}), 400
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('UPDATE orders SET status=? WHERE id=?', (status, order_id))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return app.send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
