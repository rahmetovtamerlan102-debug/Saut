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
    conn.commit()
    conn.close()

init_db()

# ---------- HTML (МАГАЗИН) ----------
MAIN_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>HowScad — виртуальные номера Telegram</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0f;
            color: #fff;
            padding: 20px;
            line-height: 1.5;
        }

        /* Контейнер */
        .container {
            max-width: 600px;
            margin: 0 auto;
        }

        /* Шапка */
        .hero {
            text-align: center;
            padding: 32px 20px;
            background: linear-gradient(135deg, rgba(15, 25, 35, 0.6), rgba(5, 10, 18, 0.8));
            backdrop-filter: blur(12px);
            border-radius: 32px;
            margin-bottom: 32px;
            border: 1px solid rgba(38, 165, 228, 0.25);
        }

        .badge {
            display: inline-block;
            background: rgba(38, 165, 228, 0.15);
            padding: 6px 14px;
            border-radius: 40px;
            font-size: 0.75rem;
            color: #26A5E4;
            margin-bottom: 16px;
            border: 1px solid rgba(38, 165, 228, 0.3);
        }

        h1 {
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #FFFFFF, #26A5E4, #A855F7);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            margin-bottom: 12px;
        }

        .hero-desc {
            color: #9ca3af;
            font-size: 0.9rem;
        }

        .features {
            display: flex;
            justify-content: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-top: 20px;
        }

        .feature {
            background: rgba(255, 255, 255, 0.03);
            padding: 6px 14px;
            border-radius: 40px;
            font-size: 0.75rem;
        }

        .feature i {
            margin-right: 6px;
            color: #26A5E4;
        }

        /* Табы */
        .tabs {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-bottom: 30px;
        }

        .tab {
            background: rgba(255, 255, 255, 0.05);
            padding: 10px 24px;
            border-radius: 60px;
            cursor: pointer;
            font-weight: 600;
            transition: 0.2s;
        }

        .tab.active {
            background: linear-gradient(135deg, #26A5E4, #1e6f9e);
            box-shadow: 0 4px 12px rgba(38, 165, 228, 0.3);
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Сетка товаров */
        .products-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 16px;
            margin-bottom: 40px;
        }

        .product-card {
            background: rgba(18, 24, 34, 0.7);
            backdrop-filter: blur(12px);
            border-radius: 28px;
            padding: 20px;
            transition: 0.2s;
            border: 1px solid rgba(255, 255, 255, 0.05);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
        }

        .product-card:hover {
            border-color: rgba(38, 165, 228, 0.5);
            background: rgba(38, 165, 228, 0.05);
        }

        .product-name {
            font-size: 1.1rem;
            font-weight: 700;
        }

        .product-price {
            font-size: 1.4rem;
            font-weight: 800;
            color: #26A5E4;
        }

        .btn-buy {
            background: linear-gradient(90deg, #26A5E4, #1e6f9e);
            border: none;
            padding: 12px 24px;
            border-radius: 40px;
            font-weight: 600;
            color: white;
            cursor: pointer;
            font-size: 0.9rem;
            transition: 0.2s;
        }

        .btn-buy:active {
            transform: scale(0.97);
        }

        /* Инструкция */
        .info-card {
            background: rgba(18, 24, 34, 0.7);
            backdrop-filter: blur(12px);
            border-radius: 28px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .info-card h3 {
            font-size: 1.3rem;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .info-card h3 i {
            color: #26A5E4;
        }

        .step {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 20px;
        }

        .step-number {
            width: 32px;
            height: 32px;
            background: #26A5E4;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }

        .faq-item {
            margin-bottom: 16px;
            padding: 12px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 20px;
        }

        .faq-question {
            font-weight: 600;
            color: #26A5E4;
            margin-bottom: 6px;
        }

        .faq-answer {
            color: #ccc;
            font-size: 0.9rem;
        }

        /* Модальное окно заказа */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(5, 5, 15, 0.95);
            backdrop-filter: blur(16px);
            justify-content: center;
            align-items: center;
            z-index: 1000;
            padding: 20px;
        }

        .modal.active {
            display: flex;
        }

        .modal-card {
            background: radial-gradient(ellipse at 30% 20%, rgba(22, 32, 48, 0.98), rgba(8, 12, 22, 0.98));
            border-radius: 56px;
            max-width: 480px;
            width: 100%;
            max-height: 85vh;
            overflow-y: auto;
            padding: 32px 28px;
            border: 1px solid rgba(38, 165, 228, 0.5);
            animation: slideUp 0.3s ease;
        }

        @keyframes slideUp {
            from { opacity: 0; transform: translateY(40px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .modal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
        }

        .modal-header h3 {
            font-size: 1.6rem;
            font-weight: 700;
            background: linear-gradient(135deg, #fff, #26A5E4);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .modal-close {
            background: rgba(255, 255, 255, 0.05);
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            cursor: pointer;
        }

        .order-summary {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 32px;
            padding: 20px;
            margin-bottom: 24px;
            text-align: center;
        }

        .order-summary p {
            margin: 8px 0;
        }

        .input-field {
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 60px;
            padding: 14px 20px;
            width: 100%;
            color: white;
            font-size: 1rem;
            margin-bottom: 8px;
        }

        .input-hint {
            font-size: 0.7rem;
            color: #9ca3af;
            margin-bottom: 16px;
            padding-left: 12px;
        }

        .input-hint i {
            color: #26A5E4;
            margin-right: 4px;
        }

        .rekvizity {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 28px;
            padding: 16px;
            margin: 16px 0;
            text-align: center;
        }

        .rekvizity .phone {
            font-size: 1.4rem;
            font-weight: 700;
            color: #26A5E4;
            cursor: pointer;
            letter-spacing: 1px;
        }

        .file-area {
            background: rgba(255, 255, 255, 0.03);
            border: 1px dashed rgba(38, 165, 228, 0.5);
            border-radius: 60px;
            padding: 20px;
            text-align: center;
            margin: 16px 0;
            cursor: pointer;
        }

        .preview-img {
            max-width: 100%;
            max-height: 150px;
            border-radius: 16px;
            margin-top: 10px;
            display: none;
        }

        .btn {
            background: linear-gradient(90deg, #26A5E4, #1e6f9e);
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

        .btn:active {
            transform: scale(0.97);
        }

        .btn-back {
            background: #333;
            margin-top: 12px;
        }

        .toast {
            position: fixed;
            bottom: 20px;
            left: 20px;
            right: 20px;
            background: #26A5E4;
            padding: 14px;
            border-radius: 60px;
            text-align: center;
            transform: translateY(100px);
            transition: 0.3s;
            z-index: 1100;
            font-weight: 500;
        }

        .toast.show {
            transform: translateY(0);
        }

        .toast.error {
            background: #e53e3e;
        }

        .admin-fab {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #1e293b;
            border: 1px solid rgba(38, 165, 228, 0.5);
            width: 56px;
            height: 56px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: 0.2s;
            z-index: 90;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        .admin-fab:hover {
            transform: scale(1.05);
            border-color: #26A5E4;
        }

        .benefits-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin: 32px 0;
        }

        .benefit-card {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 24px;
            padding: 20px;
            text-align: center;
        }

        .benefit-card i {
            font-size: 2rem;
            color: #26A5E4;
            margin-bottom: 12px;
        }

        .footer {
            text-align: center;
            padding: 24px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            color: #7e8493;
            font-size: 0.7rem;
        }
    </style>
</head>
<body>
<div class="container">
    <div class="hero">
        <div class="badge">⚡ Мгновенная доставка</div>
        <h1>HowScad</h1>
        <div class="hero-desc">Виртуальные номера для Telegram и любых сервисов</div>
        <div class="features">
            <span class="feature"><i class="fas fa-bolt"></i> Мгновенно</span>
            <span class="feature"><i class="fas fa-shield-alt"></i> Гарантия 24ч</span>
            <span class="feature"><i class="fas fa-headset"></i> Поддержка 24/7</span>
        </div>
    </div>

    <div class="tabs">
        <div class="tab active" data-tab="numbers">📱 Номера</div>
        <div class="tab" data-tab="info">ℹ️ Инструкция</div>
    </div>

    <div id="numbers-tab" class="tab-content active">
        <div class="products-grid" id="productsGrid"></div>
    </div>

    <div id="info-tab" class="tab-content">
        <div class="info-card">
            <h3><i class="fas fa-shopping-cart"></i> Как купить?</h3>
            <div class="step"><div class="step-number">1</div> Выберите страну → нажмите «Купить»</div>
            <div class="step"><div class="step-number">2</div> Укажите Telegram username (5-7 символов, латиница, цифры, _)</div>
            <div class="step"><div class="step-number">3</div> Оплатите по реквизитам</div>
            <div class="step"><div class="step-number">4</div> Прикрепите скриншот чека</div>
            <div class="step"><div class="step-number">5</div> Нажмите «Отправить заказ»</div>
            <div class="step"><div class="step-number">6</div> Админ проверит и выдаст номер</div>
        </div>
        <div class="info-card">
            <h3><i class="fas fa-question-circle"></i> Частые вопросы</h3>
            <div class="faq-item"><div class="faq-question">❓ Как долго ждать?</div><div class="faq-answer">Обычно 2–5 минут после подтверждения оплаты.</div></div>
            <div class="faq-item"><div class="faq-question">❓ Что если не пришёл код?</div><div class="faq-answer">Напишите в поддержку — поменяем номер или вернём деньги.</div></div>
            <div class="faq-item"><div class="faq-question">❓ Есть ли гарантия?</div><div class="faq-answer">Да, 24 часа. При проблемах — замена или возврат.</div></div>
            <div class="faq-item"><div class="faq-question">❓ Как связаться с поддержкой?</div><div class="faq-answer">Telegram: <strong>@HowScad_support</strong></div></div>
        </div>
    </div>

    <div class="benefits-grid">
        <div class="benefit-card"><i class="fas fa-shield-alt"></i><h4>Гарантия 24ч</h4><p>Замена номера</p></div>
        <div class="benefit-card"><i class="fas fa-bolt"></i><h4>Мгновенно</h4><p>1-3 минуты</p></div>
        <div class="benefit-card"><i class="fas fa-headset"></i><h4>Поддержка 24/7</h4><p>Всегда на связи</p></div>
        <div class="benefit-card"><i class="fas fa-credit-card"></i><h4>Безопасно</h4><p>СБП без комиссии</p></div>
    </div>

    <div class="footer">© 2025 HowScad — цифровые товары с гарантией качества</div>
</div>

<div id="orderModal" class="modal">
    <div class="modal-card">
        <div class="modal-header">
            <h3>Оформление заказа</h3>
            <div class="modal-close" onclick="closeModal()"><i class="fas fa-times"></i></div>
        </div>
        <div id="modalOrderContent" class="order-summary"></div>
        <input type="text" id="tgUser" class="input-field" placeholder="Telegram username" autocomplete="off">
        <div class="input-hint">
            <i class="fas fa-info-circle"></i> Только латиница, цифры, _ , длина от 5 до 7 символов. Без @
        </div>
        <div class="rekvizity">
            <p>💳 ОПЛАТА ПО СБП</p>
            <p class="phone" id="copyPhone">+7 902 736 57 59</p>
            <p>Получатель: <strong>Егор</strong></p>
        </div>
        <div class="file-area" id="fileArea">
            📸 Нажмите или перетащите скриншот чека
            <input type="file" id="screenshotFile" accept="image/*" style="display: none;">
            <div id="fileName"></div>
            <img id="preview" class="preview-img">
        </div>
        <button class="btn" id="submitOrderBtn">✅ Отправить заказ</button>
        <button class="btn btn-back" onclick="closeModal()">← Назад</button>
    </div>
</div>

<div id="toast" class="toast"></div>

<div class="admin-fab" id="adminFab">
    <i class="fas fa-lock" style="font-size: 1.4rem; color: #26A5E4;"></i>
</div>

<script>
    // FontAwesome подключаем динамически
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css';
    document.head.appendChild(link);

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

    function isValidUsername(username) {
        if (!username) return false;
        let clean = username.trim();
        if (clean.startsWith('@')) clean = clean.substring(1);
        return clean.length >= 5 && clean.length <= 7 && /^[a-zA-Z0-9_]+$/.test(clean);
    }

    function showMsg(msg, isError = false) {
        const toast = document.getElementById('toast');
        toast.textContent = msg;
        toast.classList.add('show');
        if (isError) toast.classList.add('error');
        else toast.classList.remove('error');
        setTimeout(() => toast.classList.remove('show'), 3000);
    }

    function renderProducts() {
        const grid = document.getElementById('productsGrid');
        grid.innerHTML = products.map(p => `
            <div class="product-card" data-id="${p.id}" data-name="${p.name}" data-price="${p.price}">
                <div>
                    <div class="product-name">${p.name}</div>
                    <div class="product-price">${p.price} ₽</div>
                </div>
                <button class="btn-buy">Купить</button>
            </div>
        `).join('');

        document.querySelectorAll('.product-card').forEach(card => {
            const btn = card.querySelector('.btn-buy');
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = parseInt(card.dataset.id);
                const name = card.dataset.name;
                const price = parseInt(card.dataset.price);
                currentProduct = { id, name, price };
                document.getElementById('modalOrderContent').innerHTML = `
                    <p><strong>${currentProduct.name}</strong></p>
                    <p>Сумма: ${currentProduct.price} ₽</p>
                `;
                document.getElementById('tgUser').value = '';
                selectedFile = null;
                document.getElementById('screenshotFile').value = '';
                document.getElementById('fileName').innerHTML = '';
                document.getElementById('preview').style.display = 'none';
                document.getElementById('orderModal').classList.add('active');
            });
        });
    }

    function closeModal() {
        document.getElementById('orderModal').classList.remove('active');
        currentProduct = null;
        selectedFile = null;
    }

    // Копирование номера
    document.getElementById('copyPhone').addEventListener('click', () => {
        navigator.clipboard.writeText('+79027365759');
        showMsg('✅ Номер скопирован');
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

    // Отправка заказа
    document.getElementById('submitOrderBtn').addEventListener('click', async () => {
        if (!currentProduct) {
            showMsg('Сначала выберите товар', true);
            return;
        }
        let username = document.getElementById('tgUser').value.trim();
        if (!isValidUsername(username)) {
            showMsg('❌ Неверный username: 5-7 символов, латиница, цифры, _ (без @)', true);
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

        showMsg('🔄 Отправка...');
        try {
            const res = await fetch('/api/orders', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.ok) {
                showMsg('✅ Заказ отправлен! Админ проверит оплату.');
                closeModal();
            } else {
                showMsg('❌ ' + (data.error || 'Ошибка'), true);
            }
        } catch (err) {
            showMsg('❌ Ошибка соединения', true);
        }
    });

    // Админ-панель (модалка с паролем)
    const adminFab = document.getElementById('adminFab');
    adminFab.addEventListener('click', () => {
        const pwd = prompt('Введите пароль администратора:');
        if (pwd === 'admin123') {
            window.location.href = '/admin?key=' + encodeURIComponent(pwd);
        } else if (pwd) {
            showMsg('Неверный пароль', true);
        }
    });

    // Переключение табов
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.dataset.tab;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });

    renderProducts();
    window.closeModal = closeModal;
</script>
</body>
</html>
'''

# ---------- АДМИН-ПАНЕЛЬ ----------
ADMIN_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HowScad — Админ-панель</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0f;
            color: #fff;
            padding: 20px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        .header {
            background: rgba(18, 24, 34, 0.9);
            backdrop-filter: blur(12px);
            border-radius: 32px;
            padding: 24px;
            margin-bottom: 24px;
            border: 1px solid rgba(38, 165, 228, 0.3);
            text-align: center;
        }
        h1 { font-size: 1.8rem; background: linear-gradient(135deg, #fff, #26A5E4); -webkit-background-clip: text; background-clip: text; color: transparent; margin-bottom: 8px; }
        .stats { color: #9ca3af; font-size: 0.85rem; }
        .order-card {
            background: rgba(18, 24, 34, 0.9);
            border-radius: 28px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid rgba(38, 165, 228, 0.2);
            transition: 0.2s;
        }
        .order-header {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .order-id { color: #26A5E4; font-weight: bold; }
        .order-date { color: #9ca3af; font-size: 0.8rem; }
        .order-details p { margin: 8px 0; }
        .order-details strong { color: #26A5E4; }
        .screenshot-img {
            max-width: 180px;
            border-radius: 16px;
            margin: 10px 0;
            cursor: pointer;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 40px;
            font-size: 0.75rem;
            font-weight: 600;
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
            background: #26A5E4;
            border: none;
            padding: 10px 24px;
            border-radius: 60px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: 0.2s;
        }
        button:hover { opacity: 0.9; transform: scale(1.02); }
        .reject-btn { background: #e53e3e; }
        .empty { text-align: center; padding: 40px; color: #9ca3af; }
        .toast {
            position: fixed;
            bottom: 20px;
            left: 20px;
            right: 20px;
            background: #26A5E4;
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
    <div class="header">
        <h1>👑 Админ-панель</h1>
        <div class="stats" id="stats">Загрузка...</div>
    </div>
    <div id="ordersList" class="orders-list">
        <div class="empty">Загрузка заказов...</div>
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
        const statsDiv = document.getElementById('stats');
        
        const pendingCount = orders.filter(o => o.status === 'pending').length;
        statsDiv.innerHTML = `📊 Всего заказов: ${orders.length} | ⏳ Ожидают: ${pendingCount}`;
        
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
                        <p>📦 ${o.product_name} — <strong>${o.product_price} ₽</strong></p>
                        <p>Статус: <span class="status-badge ${statusClass}">${statusText}</span></p>
                        ${o.screenshot ? `<a href="${o.screenshot}" target="_blank"><img src="${o.screenshot}" class="screenshot-img" onerror="this.style.display='none'"></a>` : '<p style="color:#9ca3af;">📸 Чек не прикреплён</p>'}
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
            showMsg('Ошибка обновления статуса', true);
        }
    }
    
    loadOrders();
</script>
</body>
</html>
'''

# ---------- API ----------
@app.route('/')
def index():
    return MAIN_HTML

@app.route('/admin')
def admin_panel():
    key = request.args.get('key')
    if key != 'admin123':
        return '<h3>Доступ запрещён</h3>', 403
    return ADMIN_HTML

@app.route('/api/orders', methods=['POST'])
def create_order():
    username = request.form.get('username')
    product_name = request.form.get('product_name')
    product_price = request.form.get('product_price')
    screenshot = request.files.get('screenshot')
    
    if not username or not product_name or not product_price:
        return jsonify({'error': 'Missing fields'}), 400
    
    clean_username = username.strip()
    if clean_username.startswith('@'):
        clean_username = clean_username[1:]
    if len(clean_username) < 5 or len(clean_username) > 7 or not clean_username.replace('_', '').isalnum():
        return jsonify({'error': 'Invalid username (5-7 символов, латиница, цифры, _)'}), 400
    
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
              (order_id, clean_username, product_name, int(product_price), screenshot_path))
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
