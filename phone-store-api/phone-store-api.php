<?php
/*
Plugin Name: Phone Store API
Description: Каталог телефонов из Core API
Version: 1.0
*/

if (!defined('ABSPATH')) exit;

define('PHONE_STORE_API_BASE', 'http://127.0.0.1:8000');

/**
 * ===== НАСТРОЙ СЛАГИ СТРАНИЦ ЗДЕСЬ =====
 */
function phone_store_product_page_url($id) {
    $base = site_url('/product-view/'); // <-- замени если у тебя другой slug страницы товара
    return add_query_arg('id', intval($id), $base);
}

function phone_store_request_page_url($product_id) {
    $base = site_url('/site-request/'); // <-- slug страницы заявки
    return add_query_arg('product_id', intval($product_id), $base);
}

/**
 * ===== API =====
 */
function phone_store_get_catalog() {
    $response = wp_remote_get(PHONE_STORE_API_BASE . '/catalog', [
        'timeout' => 20,
    ]);

    if (is_wp_error($response)) {
        return [];
    }

    $body = wp_remote_retrieve_body($response);
    $data = json_decode($body, true);

    return is_array($data) ? $data : [];
}

function phone_store_get_product($id) {
    $response = wp_remote_get(PHONE_STORE_API_BASE . '/catalog/' . intval($id), [
        'timeout' => 20,
    ]);

    if (is_wp_error($response)) {
        return null;
    }

    $body = wp_remote_retrieve_body($response);
    $data = json_decode($body, true);

    return is_array($data) ? $data : null;
}

/**
 * ===== СТИЛИ =====
 */
function phone_store_styles() {
    wp_register_style('phone-store-inline-style', false);
    wp_enqueue_style('phone-store-inline-style');

    $css = "
    .phone-catalog-list {
        display: flex;
        flex-direction: column;
        gap: 24px;
        width: 100%;
        margin: 20px 0;
    }

    .phone-card-link-wrap {
        text-decoration: none !important;
        color: inherit !important;
        display: block;
        width: 100%;
    }

    .phone-card-horizontal {
        display: flex;
        flex-direction: row;
        align-items: stretch;
        gap: 24px;
        width: 100%;
        border: 1px solid #e5e5e5;
        border-radius: 18px;
        overflow: hidden;
        background: #fff;
        transition: 0.2s ease;
        cursor: pointer;
    }

    .phone-card-horizontal:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.08);
    }

    .phone-card-image-box {
        width: 320px;
        min-width: 320px;
        max-width: 320px;
        background: #f7f7f7;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }

    .phone-card-image-box img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }

    .phone-card-content {
        flex: 1;
        padding: 24px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        gap: 16px;
    }

    .phone-card-title {
        margin: 0;
        font-size: 28px;
        font-weight: 700;
        line-height: 1.2;
    }

    .phone-card-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
    }

    .phone-card-badge {
        background: #f4f4f4;
        border-radius: 999px;
        padding: 8px 14px;
        font-size: 14px;
        line-height: 1;
    }

    .phone-card-notes {
        color: #555;
        font-size: 15px;
        line-height: 1.5;
        margin: 0;
    }

    .phone-card-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        margin-top: 8px;
    }

    .phone-card-price {
        font-size: 30px;
        font-weight: 800;
        color: #111;
    }

    .phone-card-btn {
        display: inline-block;
        background: #111;
        color: #fff !important;
        text-decoration: none !important;
        padding: 14px 22px;
        border-radius: 12px;
        font-weight: 600;
    }

    .phone-product-page {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 32px;
        align-items: start;
        margin: 30px 0;
    }

    .phone-product-image img {
        width: 100%;
        border-radius: 16px;
        display: block;
        background: #f7f7f7;
    }

    .phone-product-info h1 {
        margin-top: 0;
        margin-bottom: 16px;
        font-size: 36px;
        line-height: 1.2;
    }

    .phone-product-price {
        font-size: 32px;
        font-weight: 800;
        margin: 18px 0;
    }

    .phone-product-meta {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-bottom: 24px;
    }

    .phone-product-request-btn {
        display: inline-block;
        background: #111;
        color: #fff !important;
        text-decoration: none !important;
        padding: 16px 24px;
        border-radius: 12px;
        font-weight: 700;
        margin-top: 18px;
    }

    .phone-request-form {
        max-width: 700px;
        margin: 30px 0;
    }

    .phone-request-form input,
    .phone-request-form textarea,
    .phone-request-form select {
        width: 100%;
        padding: 14px 16px;
        margin-bottom: 14px;
        border: 1px solid #ddd;
        border-radius: 10px;
        font-size: 16px;
    }

    .phone-request-form button {
        background: #111;
        color: #fff;
        border: 0;
        padding: 14px 22px;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 700;
        cursor: pointer;
    }

    .phone-request-product-box {
        background: #f8f8f8;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 20px;
    }

    @media (max-width: 900px) {
        .phone-card-horizontal {
            flex-direction: column;
        }

        .phone-card-image-box {
            width: 100%;
            min-width: 100%;
            max-width: 100%;
            height: 280px;
        }

        .phone-product-page {
            grid-template-columns: 1fr;
        }
    }
    ";

    wp_add_inline_style('phone-store-inline-style', $css);
}
add_action('wp_enqueue_scripts', 'phone_store_styles');

/**
 * ===== SHORTCODE: КАТАЛОГ =====
 */
function phone_catalog_shortcode() {
    $items = phone_store_get_catalog();

    if (empty($items)) {
        return '<p>Товаров пока нет.</p>';
    }

    ob_start();
    ?>
    <div class="phone-catalog-list">
        <?php foreach ($items as $item): ?>
            <?php
                $id         = intval($item['id']);
                $title      = esc_html($item['title'] ?? 'Без названия');
                $price_raw  = $item['sell_price_uzs'] ?? 0;
                $price      = number_format((float)$price_raw, 0, '.', ' ');
                $condition  = esc_html($item['condition_grade'] ?? '');
                $battery    = esc_html($item['battery_health'] ?? '');
                $notes      = esc_html($item['notes'] ?? '');
                $photo_url  = PHONE_STORE_API_BASE . '/catalog/photo/' . $id;
                $product_url = phone_store_product_page_url($id);
            ?>

            <a class="phone-card-link-wrap" href="<?php echo esc_url($product_url); ?>">
                <div class="phone-card-horizontal">
                    <div class="phone-card-image-box">
                        <img src="<?php echo esc_url($photo_url); ?>" alt="<?php echo $title; ?>">
                    </div>

                    <div class="phone-card-content">
                        <div>
                            <h2 class="phone-card-title"><?php echo $title; ?></h2>

                            <div class="phone-card-meta">
                                <?php if (!empty($condition)): ?>
                                    <span class="phone-card-badge">Состояние: <?php echo $condition; ?></span>
                                <?php endif; ?>

                                <?php if (!empty($battery)): ?>
                                    <span class="phone-card-badge">Батарея: <?php echo $battery; ?>%</span>
                                <?php endif; ?>

                                <?php if (!empty($item['is_used'])): ?>
                                    <span class="phone-card-badge">Б/У</span>
                                <?php else: ?>
                                    <span class="phone-card-badge">Новый</span>
                                <?php endif; ?>
                            </div>

                            <?php if (!empty($notes)): ?>
                                <p class="phone-card-notes">
                                    <?php echo mb_strimwidth($notes, 0, 180, '...'); ?>
                                </p>
                            <?php endif; ?>
                        </div>

                        <div class="phone-card-footer">
                            <div class="phone-card-price"><?php echo $price; ?> сум</div>
                            <span class="phone-card-btn">Подробнее</span>
                        </div>
                    </div>
                </div>
            </a>
        <?php endforeach; ?>
    </div>
    <?php
    return ob_get_clean();
}
add_shortcode('phone_catalog', 'phone_catalog_shortcode');

/**
 * ===== SHORTCODE: СТРАНИЦА ТОВАРА =====
 * shortcode: [phone_product]
 * URL: /product-view/?id=3
 */
function phone_product_shortcode() {
    $id = isset($_GET['id']) ? intval($_GET['id']) : 0;

    if (!$id) {
        return '<p>Товар не найден.</p>';
    }

    $item = phone_store_get_product($id);

    if (!$item) {
        return '<p>Не удалось загрузить товар.</p>';
    }

    $title     = esc_html($item['title'] ?? 'Без названия');
    $price_raw = $item['sell_price_uzs'] ?? 0;
    $price     = number_format((float)$price_raw, 0, '.', ' ');
    $condition = esc_html($item['condition_grade'] ?? '');
    $battery   = esc_html($item['battery_health'] ?? '');
    $notes     = esc_html($item['notes'] ?? '');
    $photo_url = PHONE_STORE_API_BASE . '/catalog/photo/' . $id;
    $request_url = phone_store_request_page_url($id);

    ob_start();
    ?>
    <div class="phone-product-page">
        <div class="phone-product-image">
            <img src="<?php echo esc_url($photo_url); ?>" alt="<?php echo $title; ?>">
        </div>

        <div class="phone-product-info">
            <h1><?php echo $title; ?></h1>

            <div class="phone-product-meta">
                <?php if (!empty($condition)): ?>
                    <div><strong>Состояние:</strong> <?php echo $condition; ?></div>
                <?php endif; ?>

                <?php if (!empty($battery)): ?>
                    <div><strong>Батарея:</strong> <?php echo $battery; ?>%</div>
                <?php endif; ?>

                <?php if (isset($item['imei']) && !empty($item['imei'])): ?>
                    <div><strong>IMEI:</strong> <?php echo esc_html($item['imei']); ?></div>
                <?php endif; ?>
            </div>

            <div class="phone-product-price"><?php echo $price; ?> сум</div>

            <?php if (!empty($notes)): ?>
                <div>
                    <strong>Описание:</strong><br>
                    <?php echo nl2br($notes); ?>
                </div>
            <?php endif; ?>

            <a class="phone-product-request-btn" href="<?php echo esc_url($request_url); ?>">
                Оставить заявку
            </a>
        </div>
    </div>
    <?php
    return ob_get_clean();
}
add_shortcode('phone_product', 'phone_product_shortcode');

/**
 * ===== SHORTCODE: ФОРМА ЗАЯВКИ =====
 * shortcode: [phone_request_form]
 * URL: /site-request/?product_id=3
 */
function phone_request_form_shortcode() {
    $product_id = isset($_GET['product_id']) ? intval($_GET['product_id']) : 0;
    $item = null;

    if ($product_id) {
        $item = phone_store_get_product($product_id);
    }

    $product_title = $item['title'] ?? '';
    $product_price = (float)($item['sell_price_uzs'] ?? 0);

    $message = '';

    if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['phone_request_submit'])) {
        $client_name   = sanitize_text_field($_POST['client_name'] ?? '');
        $client_phone  = sanitize_text_field($_POST['client_phone'] ?? '');
        $buy_type      = sanitize_text_field($_POST['buy_type'] ?? '');
        $comment       = sanitize_textarea_field($_POST['comment'] ?? '');
        $product_id_post = intval($_POST['product_id'] ?? 0);

        $down_payment  = floatval($_POST['down_payment'] ?? 0);
        $months        = intval($_POST['months'] ?? 0);
        $monthly_payment = floatval($_POST['monthly_payment'] ?? 0);
        $remaining_amount = floatval($_POST['remaining_amount'] ?? 0);

        $product = $product_id_post ? phone_store_get_product($product_id_post) : null;

        $payload = [
            'client_name'       => $client_name,
            'client_phone'      => $client_phone,
            'buy_type'          => $buy_type,
            'comment'           => $comment,
            'product_id'        => $product_id_post,
            'product_title'     => $product['title'] ?? '',
            'product_price'     => $product['sell_price_uzs'] ?? null,
            'down_payment'      => $down_payment,
            'months'            => $months,
            'monthly_payment'   => $monthly_payment,
            'remaining_amount'  => $remaining_amount,
        ];

        $response = wp_remote_post(PHONE_STORE_API_BASE . '/leads', [
            'timeout' => 20,
            'headers' => [
                'Content-Type' => 'application/json',
            ],
            'body' => wp_json_encode($payload),
        ]);

        if (is_wp_error($response)) {
            $message = '<p style="color:red;">Ошибка отправки заявки.</p>';
        } else {
            $message = '<p style="color:green;">Заявка отправлена. Менеджер свяжется с клиентом.</p>';
        }
    }

    ob_start();

    echo $message;
    ?>
    <div class="phone-request-form">
        <?php if ($item): ?>
            <div class="phone-request-product-box">
                <strong>Товар:</strong> <?php echo esc_html($product_title); ?><br>
                <strong>Цена:</strong> <span id="product-price-view"><?php echo number_format($product_price, 0, '.', ' '); ?></span> сум
            </div>
        <?php endif; ?>

        <form method="post" id="phone-request-form">
            <input type="hidden" name="product_id" value="<?php echo intval($product_id); ?>">
            <input type="hidden" name="monthly_payment" id="monthly_payment_input" value="0">
            <input type="hidden" name="remaining_amount" id="remaining_amount_input" value="0">

            <input type="text" name="client_name" placeholder="Имя клиента" required>
            <input type="text" name="client_phone" placeholder="Телефон / Telegram" required>

            <select name="buy_type" id="buy_type" required>
                <option value="">Выберите тип покупки</option>
                <option value="installment">Рассрочка</option>
                <option value="cash">Наличные</option>
            </select>

            <div id="installment-calculator" style="display:none; margin-bottom:20px; padding:18px; border:1px solid #ddd; border-radius:12px; background:#fafafa;">
                <h3 style="margin-top:0;">Калькулятор рассрочки</h3>

                <label style="display:block; margin-bottom:8px;">Первоначальный взнос</label>
                <input type="number" name="down_payment" id="down_payment" min="0" step="1000" placeholder="Например: 3000000">

                <label style="display:block; margin-bottom:8px;">Срок рассрочки</label>
                <select name="months" id="months">
                    <option value="3">3 месяца</option>
                    <option value="6">6 месяцев</option>
                    <option value="9">9 месяцев</option>
                    <option value="12">12 месяцев</option>
                </select>

                <div style="margin-top:18px; line-height:1.8;">
                    <div><strong>Цена товара:</strong> <span id="calc_product_price"><?php echo number_format($product_price, 0, '.', ' '); ?></span> сум</div>
                    <div><strong>Остаток после взноса:</strong> <span id="remaining_amount">0</span> сум</div>
                    <div><strong>Платёж в месяц:</strong> <span id="monthly_payment">0</span> сум</div>
                </div>
            </div>

            <textarea name="comment" placeholder="Комментарий"></textarea>

            <button type="submit" name="phone_request_submit">Отправить заявку</button>
        </form>
    </div>

    <script>
    (function() {
        const buyType = document.getElementById('buy_type');
        const calcBox = document.getElementById('installment-calculator');
        const downPaymentInput = document.getElementById('down_payment');
        const monthsInput = document.getElementById('months');
        const remainingAmountEl = document.getElementById('remaining_amount');
        const monthlyPaymentEl = document.getElementById('monthly_payment');
        const monthlyPaymentInput = document.getElementById('monthly_payment_input');
        const remainingAmountInput = document.getElementById('remaining_amount_input');

        const productPrice = <?php echo json_encode($product_price); ?>;

        function formatNumber(num) {
            return new Intl.NumberFormat('ru-RU').format(Math.round(num));
        }

        function toggleCalculator() {
            if (buyType.value === 'installment') {
                calcBox.style.display = 'block';
            } else {
                calcBox.style.display = 'none';
            }
            calculateInstallment();
        }

        function calculateInstallment() {
            const downPayment = parseFloat(downPaymentInput.value || 0);
            const months = parseInt(monthsInput.value || 1, 10);

            let remaining = productPrice - downPayment;
            if (remaining < 0) remaining = 0;

            let monthly = months > 0 ? (remaining / months) : 0;

            remainingAmountEl.textContent = formatNumber(remaining);
            monthlyPaymentEl.textContent = formatNumber(monthly);

            remainingAmountInput.value = remaining.toFixed(2);
            monthlyPaymentInput.value = monthly.toFixed(2);
        }

        if (buyType) buyType.addEventListener('change', toggleCalculator);
        if (downPaymentInput) downPaymentInput.addEventListener('input', calculateInstallment);
        if (monthsInput) monthsInput.addEventListener('change', calculateInstallment);

        toggleCalculator();
    })();
    </script>
    <?php

    return ob_get_clean();
}
add_shortcode('phone_request_form', 'phone_request_form_shortcode');