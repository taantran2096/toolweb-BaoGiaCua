import json
import os
import uuid
from datetime import date, datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from pdf_generator import generate_pdf

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "quotes.json")


def load_quotes():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_quotes(quotes):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(quotes, f, ensure_ascii=False, indent=2)


def get_quote(quote_id):
    for q in load_quotes():
        if q["id"] == quote_id:
            return q
    return None


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    quotes = load_quotes()
    # Sort newest first
    quotes = sorted(quotes, key=lambda q: q.get("created_at", ""), reverse=True)
    return render_template("index.html", quotes=quotes)


@app.route("/new")
def new_quote():
    today = date.today().strftime("%d/%m/%Y")
    empty_quote = {
        "id": "",
        "so_bao_gia": "",
        "ngay": today,
        "cong_ty": "CÔNG TY TNHH SẢN XUẤT - THƯƠNG MẠI HƯNG PHÁT",
        "dia_chi_ct": "Lô B23, Đường số 3, KCN Vĩnh Lộc, Quận Bình Chánh, TP.HCM",
        "dien_thoai_ct": "0909 123 456",
        "email_ct": "info@hungphat.com.vn",
        "khach_hang": "",
        "dien_thoai": "",
        "dia_chi": "",
        "items": [
            {"hang_muc": "", "kich_thuoc": "", "so_luong": 1, "don_vi": "m²", "dien_tich": 0, "don_gia": 0, "thanh_tien": 0}
        ],
        "vat": 10,
        "dieu_khoan": "- Đặt cọc 50% khi ký hợp đồng\n- Thanh toán 50% còn lại khi nghiệm thu bàn giao",
        "ghi_chu": "",
        "nguoi_lap": "",
    }
    return render_template("edit.html", quote=empty_quote, is_new=True)


@app.route("/save", methods=["POST"])
def save_quote():
    data = request.get_json()
    quotes = load_quotes()

    if data.get("id"):
        # Update existing
        for i, q in enumerate(quotes):
            if q["id"] == data["id"]:
                data["updated_at"] = datetime.now().isoformat()
                quotes[i] = data
                break
    else:
        data["id"] = str(uuid.uuid4())[:8]
        data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = data["created_at"]
        quotes.append(data)

    save_quotes(quotes)
    return jsonify({"success": True, "id": data["id"]})


@app.route("/edit/<quote_id>")
def edit_quote(quote_id):
    q = get_quote(quote_id)
    if not q:
        return redirect(url_for("index"))
    return render_template("edit.html", quote=q, is_new=False)


@app.route("/preview/<quote_id>")
def preview_quote(quote_id):
    q = get_quote(quote_id)
    if not q:
        return redirect(url_for("index"))
    # Calculate totals server-side to ensure consistency
    q = _compute_totals(q)
    return render_template("preview.html", quote=q)


@app.route("/delete/<quote_id>", methods=["POST"])
def delete_quote(quote_id):
    quotes = [q for q in load_quotes() if q["id"] != quote_id]
    save_quotes(quotes)
    return redirect(url_for("index"))


@app.route("/pdf/<quote_id>")
def export_pdf(quote_id):
    q = get_quote(quote_id)
    if not q:
        return "Không tìm thấy báo giá", 404
    q = _compute_totals(q)
    pdf_path = generate_pdf(q)
    filename = f"BaoGia_{q.get('so_bao_gia', quote_id)}.pdf"
    return send_file(pdf_path, as_attachment=True, download_name=filename, mimetype="application/pdf")


@app.route("/api/quote/<quote_id>")
def api_get_quote(quote_id):
    q = get_quote(quote_id)
    if not q:
        return jsonify({"error": "not found"}), 404
    return jsonify(q)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _compute_totals(q):
    items = q.get("items", [])
    for item in items:
        try:
            sl = float(item.get("so_luong", 0) or 0)
            dv = item.get("don_vi", "m²")
            kd = item.get("kich_thuoc", "") or ""

            # Parse kích thước WxH (mét) để tính diện tích nếu không có sẵn
            dien_tich = float(item.get("dien_tich", 0) or 0)
            if dien_tich == 0 and "x" in kd.lower():
                parts = kd.lower().replace(" ", "").split("x")
                try:
                    dien_tich = float(parts[0]) * float(parts[1]) * sl
                except Exception:
                    dien_tich = 0

            don_gia = float(item.get("don_gia", 0) or 0)
            # Nếu đơn vị m² và có diện tích thì tính theo diện tích
            if dv == "m²" and dien_tich > 0:
                thanh_tien = dien_tich * don_gia
            else:
                thanh_tien = sl * don_gia

            item["dien_tich"] = round(dien_tich, 3)
            item["thanh_tien"] = round(thanh_tien, 0)
        except Exception:
            item["thanh_tien"] = 0

    tong_dien_tich = sum(float(it.get("dien_tich", 0) or 0) for it in items)
    tong_chua_vat = sum(float(it.get("thanh_tien", 0) or 0) for it in items)
    vat_rate = float(q.get("vat", 10) or 0) / 100
    tong_vat = round(tong_chua_vat * vat_rate, 0)
    tong_cong = round(tong_chua_vat + tong_vat, 0)

    q["tong_dien_tich"] = round(tong_dien_tich, 3)
    q["tong_chua_vat"] = round(tong_chua_vat, 0)
    q["tong_vat"] = tong_vat
    q["tong_cong"] = tong_cong
    return q


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, port=5000)
