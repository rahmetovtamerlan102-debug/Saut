import os
import sqlite3
import uuid
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ---------- БАЗА ДАННЫХ ----------
def init_db():
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        product_name TEXT,
        product_price INTEGER,
        status TEXT DEFAULT 'pending',
        screenshot TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('SELECT COUNT(*) FROM orders')
    conn.commit()
    conn.close()

init_db()

# ---------- HTML (МАГАЗИН + АДМИНКА ПО ПАРОЛЮ) ----------
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
        .container { max-width: 600px; margin: 0 auto; }
        .card {
            background: rgba(18, 24, 34, 0.9);
            backdrop-filter: blur(12px);
            border-radius: 32px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid rgba(38, 165, 228, 0.3);
        }
        h1 { font-size: 2rem; text-align: center; background: linear-gradient(135deg, #fff, #26a5e4); -webkit-background-clip: text; background-clip: text; color: transparent; margin-bottom: 8px; }
        .sub { text-align: center; color: #9ca3af; margin-bottom: 32px; }
        
        /* Товары */
        .products-grid {
            display: flex;
            flex-direction: column;
            gap: 16px;
            margin-bottom: 24px;
        }
        .product-card {
            background: rgba(255,255,255,0.05);
            border-radius: 28px;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: 0.2s;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .product-card:hover {
            border-color: #26a5e4;
            background: rgba(38,165,228,0.05);
        }
        .product-name {
            font-size: 1.1rem;
            font-weight: 600;
        }
        .product-price {
            font-size: 1.3rem;
            font-weight: 700;
            color: #26a5e4;
        }
        .buy-btn {
            background: linear-gradient(90deg, #26a5e4, #1e6f9e);
            border: none;
            padding: 12px 28px;
            border-radius: 60px;
            font-weight: 600;
            color: white;
            font-size: 1rem;
            cursor: pointer;
            transition: 0.2s;
        }
        .buy-btn:hover { transform: scale(1.02); }
        .buy-btn:active { transform: scale(0.98); }
        
        /* Форма заказа */
        .order-form {
            display: none;
            margin-top: 24px;
            padding-top: 24px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        .input-field {
            background: rgba(0,0,0,0.6);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 60px;
            padding: 14px 20px;
            width: 100%;
            color: white;
            font-size: 1rem;
            margin-bottom: 16px;
        }
        .file-area {
            background: rgba(255,255,255,0.03);
            border: 1px dashed #26a5e4;
            border-radius: 60px;
            padding: 20px;
            text-align: center;
            margin: 16px 0;
            cursor: pointer;
            transition: 0.2s;
        }
        .file-area:hover {
            background: rgba(38,165,228,0.1);
        }
        .preview-img {
            max-width: 100%;
            max-height: 150px;
            border-radius: 16px;
            margin-top: 10px;
            display: none;
        }
        .btn {
            background: linear-gradient(90deg, #26a5e4, #1e6f9e);
            border: none;
            padding: 14px 24px;
            border-radius: 60px;
            font-weight: 600;
            color: white;
            width: 100%;
            font-size: 1rem;
            cursor: pointer;
            transition: 0.2s;
        }
        .btn:active { transform: scale(0.97); }
        .btn-back {
            background: #333;
            margin-top: 12px;
        }
        
        /* Тосты */
        .toast {
            position: fixed;
            bottom: 20px;
            left: 20px;
            right: 20px;
            background: #26a5e4;
            padding: 14px;
            border-radius: 60px;
            text-align: center;
            transform: translateY(100px);
            transition: 0.3s;
            z-index: 1000;
            font-weight: 500;
        }
        .toast.show { transform: translateY(0); }
        .toast.error { background: #e53e3e; }
        
        /* Админ-кнопка */
        .admin-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0,0,0,0.5);
            border: none;
            padding: 12px 16px;
            border-radius: 60px;
            color: #26a5e4;
            font-size: 0.8rem;
            cursor: pointer;
            backdrop-filter: blur(8px);
            z-index: 100;
        }
        
        /* Модальное окно пароля */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            backdrop-filter: blur(8px);
            justify-content: center;
            align-items: center;
            z-index: 2000;
        }
        .modal-card {
            background: #1e293b;
            border-radius: 48px;
            padding: 32px;
            width: 90%;
            max-width: 350px;
            text-align: center;
        }
        .modal-card input {
            width: 100%;
            padding: 14px;
            border-radius: 60px;
            border: none;
            margin: 20px 0;
            font-size: 1rem;
        }
        .modal-card button {
            background: #26a5e4;
            border: none;
            padding: 12px 24px;
            border-radius: 60px;
            color: white;
            font-weight: 600;
            width: 100%;
            cursor: pointer;
        }
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <h1>HowScad</h1>
        <div class="sub">Виртуальные номера для Telegram</div>
        
        <div class="products-grid" id="productsGrid"></div>
        
        <div id="orderForm" class="order-form">
            <div id="selectedProductInfo" style="background: rgba(38,165,228,0.1); padding: 12px; border-radius: 28px; margin-bottom: 16px;"></div>
            <input type="text" id="orderUsername" class="input-field" placeholder="Telegram username (5-7 символов, латиница, цифры, _)">
            <div class="rekvizity" style="background: rgba(0,0,0,0.3); border-radius: 28px; padding: 16px; text-align: center; margin-bottom: 16px;">
                <p style="color: #26a5e4; font-weight: bold;">💳 ОПЛАТА ПО СБП</p>
                <p style="font-size: 1.4rem; font-weight: 700;">+7 902 736 57 59</p>
                <p>Получатель: <strong>Егор</strong></p>
            </div>
            <div class="file-area" id="fileArea">
                📸 Нажмите или перетащите скриншот чека
                <input type="file" id="screenshotFile" accept="image/*" style="display: none;">
                <div id="fileName"></div>
                <img id="preview" class="preview-img">
            </div>
            <button id="submitOrderBtn" class="btn">✅ Отправить заказ</button>
            <button id="cancelOrderBtn" class="btn btn-back">← Назад</button>
        </div>
    </div>
</div>

<button class="admin-btn" id="adminBtn">🔐 Админ-панель</button>

<div id="passwordModal" class="modal">
    <div class="modal-card">
        <h3>🔐 Вход в админ-панель</h3>
        <input type="password" id="adminPassword" placeholder="Введите пароль">
        <button id="confirmPasswordBtn">Войти</button>
    </div>
</div>

<div id="toast" class="toast"></div>

<script>
    const products = [
        { id: 1, name: "🇺🇸 США (USA)", price: 80 },
        { id: 2, name: "🇨🇦 Канада (Canada)", price: 65 },
        { id: 3, name: "🇷🇺 Россия (новорег)", price: 140 },
        { id: 4, name: "🇬🇧 Великобритания", price: 120 },
        { id: 5, name: "🇩🇪 Германия", price: 110 },
        { id: 6, name: "🇧🇩 Бангладеш", price: 90 },
        { id: 7, name: "🇵🇭 Филиппины", price: 65 },
        { id: 8, name: "🇳🇬 Нигерия", price: 60 },
        { id: 9, name: "🇮🇳 Индия", price: 50 }
    ];
    
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
    
    function renderProducts() {
        const grid = document.getElementById('productsGrid');
        grid.innerHTML = products.map(p => `
            <div class="product-card">
                <div>
                    <div class="product-name">${p.name}</div>
                    <div class="product-price">${p.price} ₽</div>
                </div>
                <button class="buy-btn" data-id="${p.id}" data-name="${p.name}" data-price="${p.price}">Купить</button>
            </div>
        `).join('');
        
        document.querySelectorAll('.buy-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                currentProduct = {
                    id: btn.dataset.id,
                    name: btn.dataset.name,
                    price: parseInt(btn.dataset.price)
                };
                document.getElementById('selectedProductInfo').innerHTML = `<strong>${currentProduct.name}</strong> — ${currentProduct.price} ₽`;
                document.getElementById('orderForm').style.display = 'block';
                document.getElementById('orderUsername').value = '';
                selectedFile = null;
                document.getElementById('screenshotFile').value = '';
                document.getElementById('fileName').innerHTML = '';
                document.getElementById('preview').style.display = 'none';
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
        formData.append('product_name', currentProduct.name);
        formData.append('product_price', currentProduct.price);
        formData.append('screenshot', selectedFile);
        
        showMsg('🔄 Отправка заказа...');
        try {
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
        } catch (err) {
            showMsg('❌ Ошибка соединения', true);
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
    
    // Админ-панель (модалка с паролем)
    const adminBtn = document.getElementById('adminBtn');
    const passwordModal = document.getElementById('passwordModal');
    const confirmPasswordBtn = document.getElementById('confirmPasswordBtn');
    const adminPassword = document.getElementById('adminPassword');
    
    adminBtn.addEventListener('click', () => {
        passwordModal.style.display = 'flex';
        adminPassword.value = '';
    });
    
    confirmPasswordBtn.addEventListener('click', () => {
        const pwd = adminPassword.value;
        if (pwd === 'admin123') {
            window.location.href = '/admin?key=' + encodeURIComponent(pwd);
        } else {
            showMsg('Неверный пароль', true);
            passwordModal.style.display = 'none';
        }
    });
    
    passwordModal.addEventListener('click', (e) => {
        if (e.target === passwordModal) passwordModal.style.display = 'none';
    });
    
    renderProducts();
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
        .container { max-width: 800px; margin: 0 auto; }
        h1 { font-size: 1.8rem; margin-bottom: 24px; text-align: center; }
        .orders-list { display: flex; flex-direction: column; gap: 20px; }
        .order-card {
            background: rgba(18, 24, 34, 0.9);
            border-radius: 32px;
            padding: 20px;
            border: 1px solid rgba(38, 165, 228, 0.3);
        }
        .order-header {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .order-id { color: #26a5e4; font-weight: bold; }
        .order-date { color: #9ca3af; font-size: 0.8rem; }
        .order-details p { margin: 8px 0; }
        .screenshot-img {
            max-width: 200px;
            border-radius: 16px;
            margin: 10px 0;
            cursor: pointer;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 40px;
            font-size: 0.75rem;
        }
        .status-pending { background: #f59e0b; }
        .status-approved { background: #10b981; }
        .status-rejected { background: #e53e3e; }
        .action-buttons {
            display: flex;
            gap: 12px;
            margin-top: 16px;
        }
        button {
            background: #26a5e4;
            border: none;
            padding: 10px 24px;
            border-radius: 60px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: 0.2s;
        }
        button:hover { transform: scale(1.02); }
        .reject-btn { background: #e53e3e; }
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
        .empty { text-align: center; padding: 40px; color: #9ca3af; }
    </style>
</head>
<body>
<div class="container">
    <h1>👑 Админ-панель</h1>
    <div id="ordersList" class="orders-list">
        <div class="empty">Загрузка...</div>
    </div>
</div>
<div id="toast" class="toast"></div>

<script>
    const ADMIN_KEY = new URLSearchParams(window.location.search).get('key');
    
    function showMsg(msg, isError = false) {
        const toast = document.getElementById('toast');
        toast.textContent = msg;
        toast.classList.add('show');
        if (isError) toast.classList.add('error');
        else toast.classList.remove('error');
        setTimeout(() => toast.classList.remove('show'), 3000);
    }
    
    async function loadOrders() {
        const res = await fetch(`/api/orders?key=${ADMIN_KEY}`);
        if (!res.ok) {
            document.getElementById('ordersList').innerHTML = '<div class="empty">Ошибка загрузки заказов</div>';
            return;
        }
        const orders = await res.json();
        const container = document.getElementById('ordersList');
        if (orders.length === 0) {
            container.innerHTML = '<div class="empty">📭 Заказов пока нет</div>';
            return;
        }
        
        container.innerHTML = orders.map(o => {
            let statusText = '', statusClass = '';
            if (o.status === 'pending') { statusText = '⏳ Ожидает'; statusClass = 'status-pending'; }
            else if (o.status === 'approved') { statusText = '✅ Принят'; statusClass = 'status-approved'; }
            else { statusText = '❌ Отклонён'; statusClass = 'status-rejected'; }
            
            return `
                <div class="order-card">
                    <div class="order-header">
                        <span class="order-id">🆔 ${o.id}</span>
                        <span class="order-date">📅 ${o.created_at}</span>
                    </div>
                    <div class="order-details">
                        <p>👤 <strong>${o.username}</strong></p>
                        <p>📦 ${o.product_name} — ${o.product_price} ₽</p>
                        <p>Статус: <span class="status-badge ${statusClass}">${statusText}</span></p>
                        ${o.screenshot ? `<a href="${o.screenshot}" target="_blank"><img src="${o.screenshot}" class="screenshot-img" onerror="this.style.display='none'"></a>` : '<p>📸 Чек не прикреплён</p>'}
                    </div>
                    ${o.status === 'pending' ? `
                        <div class="action-buttons">
                            <button onclick="updateStatus('${o.id}', 'approved')">✅ Принять заказ</button>
                            <button onclick="updateStatus('${o.id}', 'rejected')" class="reject-btn">❌ Отклонить</button>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }
    
    async function updateStatus(orderId, status) {
        const res = await fetch(`/api/orders/${orderId}?key=${ADMIN_KEY}&status=${status}`, { method: 'PUT' });
        if (res.ok) {
            showMsg(status === 'approved' ? '✅ Заказ принят' : '❌ Заказ отклонён');
            loadOrders();
        } else {
            showMsg('Ошибка', true);
        }
    }
    
    loadOrders();
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
        return 'Доступ запрещён', 403
    return ADMIN_HTML

@app.route('/api/orders', methods=['POST'])
def create_order():
    username = request.form.get('username')
    product_name = request.form.get('product_name')
    product_price = request.form.get('product_price')
    screenshot = request.files.get('screenshot')
    
    if not username or not product_name or not product_price:
        return jsonify({'error': 'Missing fields'}), 400
    
    # Проверка username
    if len(username) < 5 or len(username) > 7 or not username.replace('_', '').isalnum():
        return jsonify({'error': 'Invalid username'}), 400
    
    order_id = str(uuid.uuid4())[:8]
    screenshot_path = ''
    if screenshot:
        ext = screenshot.filename.rsplit('.', 1)[-1].lower()
        filename = f"{order_id}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        screenshot.save(filepath)
        screenshot_path = f"/uploads/{filename}"
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''INSERT INTO orders (id, username, product_name, product_price, screenshot)
                 VALUES (?, ?, ?, ?, ?)''',
              (order_id, username, product_name, int(product_price), screenshot_path))
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
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
