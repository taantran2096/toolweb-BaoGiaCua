"""
PDF generator using ReportLab.
Produces an A4 professional quotation that matches the Vietnamese door/fence quote style.
"""
import os
import tempfile

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Register fonts ────────────────────────────────────────────────────────────
_BASE = os.path.dirname(__file__)

def _reg_font(name, path):
    full = os.path.join(_BASE, path)
    if os.path.exists(full):
        try:
            pdfmetrics.registerFont(TTFont(name, full))
            return True
        except Exception:
            pass
    return False

# Try to register Vietnamese-compatible fonts from the system
_FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/freefont",
    "/usr/share/fonts",
]

FONT_NORMAL = "Helvetica"
FONT_BOLD   = "Helvetica-Bold"

for _d in _FONT_DIRS:
    _n = os.path.join(_d, "DejaVuSans.ttf")
    _b = os.path.join(_d, "DejaVuSans-Bold.ttf")
    if os.path.exists(_n) and os.path.exists(_b):
        try:
            pdfmetrics.registerFont(TTFont("DejaVu", _n))
            pdfmetrics.registerFont(TTFont("DejaVu-Bold", _b))
            FONT_NORMAL = "DejaVu"
            FONT_BOLD   = "DejaVu-Bold"
        except Exception:
            pass
        break

# ── Colours ───────────────────────────────────────────────────────────────────
BLUE_DARK  = colors.HexColor("#1a3a5c")
BLUE_MID   = colors.HexColor("#2563a8")
BLUE_LIGHT = colors.HexColor("#dbeafe")
GOLD       = colors.HexColor("#d4a017")
GRAY_LIGHT = colors.HexColor("#f3f4f6")
GRAY_MID   = colors.HexColor("#9ca3af")

# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_money(val):
    try:
        return "{:,.0f}".format(float(val)).replace(",", ".")
    except Exception:
        return "0"


def _fmt_num(val, decimals=3):
    try:
        f = float(val)
        if f == int(f):
            return str(int(f))
        return ("{:." + str(decimals) + "f}").format(f).rstrip("0").rstrip(".")
    except Exception:
        return str(val)


def _p(text, style):
    """Safe paragraph – strips None."""
    return Paragraph(str(text) if text is not None else "", style)


# ── Main generator ────────────────────────────────────────────────────────────

def generate_pdf(quote: dict) -> str:
    """Generate PDF for *quote* dict, return path to temp file."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()
    path = tmp.name

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    styles = _build_styles()
    story  = _build_story(quote, styles)
    doc.build(story)
    return path


def _build_styles():
    base = getSampleStyleSheet()
    def s(name, **kw):
        kw.setdefault("fontName", FONT_NORMAL)
        kw.setdefault("fontSize", 9)
        kw.setdefault("leading",  12)
        return ParagraphStyle(name, **kw)

    return {
        "title"     : s("title",    fontName=FONT_BOLD, fontSize=16, textColor=BLUE_DARK,
                         alignment=TA_CENTER, spaceAfter=2),
        "subtitle"  : s("subtitle", fontName=FONT_BOLD, fontSize=10, textColor=BLUE_MID,
                         alignment=TA_CENTER, spaceAfter=4),
        "company"   : s("company",  fontName=FONT_BOLD, fontSize=9, textColor=BLUE_DARK),
        "company_sm": s("company_sm", fontSize=8, textColor=colors.black),
        "section"   : s("section",  fontName=FONT_BOLD, fontSize=9, textColor=BLUE_DARK),
        "normal"    : s("normal",   fontSize=9),
        "small"     : s("small",    fontSize=8, textColor=colors.gray),
        "right"     : s("right",    fontSize=9, alignment=TA_RIGHT),
        "center"    : s("center",   fontSize=9, alignment=TA_CENTER),
        "th"        : s("th",       fontName=FONT_BOLD, fontSize=8, textColor=colors.white,
                         alignment=TA_CENTER, leading=10),
        "td"        : s("td",       fontSize=8, leading=10),
        "td_c"      : s("td_c",     fontSize=8, leading=10, alignment=TA_CENTER),
        "td_r"      : s("td_r",     fontSize=8, leading=10, alignment=TA_RIGHT),
        "total_lbl" : s("total_lbl", fontName=FONT_BOLD, fontSize=9, alignment=TA_RIGHT),
        "total_val" : s("total_val", fontName=FONT_BOLD, fontSize=9, textColor=BLUE_DARK,
                         alignment=TA_RIGHT),
        "grand"     : s("grand",    fontName=FONT_BOLD, fontSize=11, textColor=colors.white,
                         alignment=TA_RIGHT),
        "grand_val" : s("grand_val", fontName=FONT_BOLD, fontSize=11, textColor=GOLD,
                         alignment=TA_RIGHT),
        "footer"    : s("footer",   fontSize=7, textColor=colors.gray, alignment=TA_CENTER),
        "note"      : s("note",     fontSize=8, leading=11),
        "sign_name" : s("sign_name", fontName=FONT_BOLD, fontSize=9, alignment=TA_CENTER),
        "sign_title": s("sign_title", fontSize=8, textColor=colors.gray, alignment=TA_CENTER),
    }


def _build_story(q, st):
    story = []
    W = A4[0] - 3 * cm   # usable width

    # ── HEADER ────────────────────────────────────────────────────────────────
    logo_path = os.path.join(_BASE, "static", "logo.png")
    logo_cell = ""
    if os.path.exists(logo_path):
        try:
            logo_cell = Image(logo_path, width=3.5 * cm, height=2 * cm)
        except Exception:
            logo_cell = ""

    cty    = q.get("cong_ty", "")
    dc_ct  = q.get("dia_chi_ct", "")
    dt_ct  = q.get("dien_thoai_ct", "")
    em_ct  = q.get("email_ct", "")

    company_block = [
        _p(cty,   st["company"]),
        Spacer(1, 2),
        _p(f"Địa chỉ: {dc_ct}", st["company_sm"]),
        _p(f"ĐT: {dt_ct}  |  Email: {em_ct}", st["company_sm"]),
    ]

    title_block = [
        _p("BẢNG BÁO GIÁ", st["title"]),
        _p("CỬA & RÀO CNC", st["subtitle"]),
    ]

    so_bg  = q.get("so_bao_gia", "")
    ngay   = q.get("ngay", "")
    info_block = [
        _p(f"Số BG: <b>{so_bg}</b>", st["normal"]),
        _p(f"Ngày: {ngay}", st["normal"]),
    ]

    header_table = Table(
        [[logo_cell, company_block, title_block, info_block]],
        colWidths=[3.5 * cm, 7 * cm, 6.5 * cm, 4 * cm],
        hAlign="LEFT",
    )
    header_table.setStyle(TableStyle([
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",       (2, 0), (2, 0),   "CENTER"),
        ("ALIGN",       (3, 0), (3, 0),   "RIGHT"),
        ("LINEBELOW",   (0, 0), (-1, 0),  1.5, BLUE_DARK),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))

    # ── CUSTOMER INFO ─────────────────────────────────────────────────────────
    kh   = q.get("khach_hang", "")
    dt   = q.get("dien_thoai", "")
    dc   = q.get("dia_chi", "")

    info_rows = [
        [_p("THÔNG TIN KHÁCH HÀNG", st["section"]), "", "", ""],
        [_p(f"Khách hàng:", st["normal"]),
         _p(f"<b>{kh}</b>", st["normal"]),
         _p("Điện thoại:", st["normal"]),
         _p(f"<b>{dt}</b>", st["normal"])],
        [_p("Địa chỉ:", st["normal"]),
         _p(f"<b>{dc}</b>", st["normal"]),
         "", ""],
    ]

    info_t = Table(info_rows, colWidths=[2.5 * cm, 8 * cm, 2.5 * cm, 8 * cm])
    info_t.setStyle(TableStyle([
        ("SPAN",        (0, 0), (3, 0)),
        ("BACKGROUND",  (0, 0), (-1, 0), BLUE_LIGHT),
        ("SPAN",        (1, 2), (3, 2)),
        ("TOPPADDING",  (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("BOX",         (0, 0), (-1, -1), 0.5, GRAY_MID),
        ("INNERGRID",   (0, 1), (-1, -1), 0.3, GRAY_MID),
    ]))
    story.append(info_t)
    story.append(Spacer(1, 6))

    # ── ITEMS TABLE ───────────────────────────────────────────────────────────
    headers = ["STT", "Hạng mục / Mô tả", "Kích thước\n(m x m)", "SL", "ĐVT",
               "Diện tích\n(m²)", "Đơn giá\n(đ/m²)", "Thành tiền (đ)"]

    col_w = [0.7*cm, 5.8*cm, 2.2*cm, 0.8*cm, 0.8*cm, 1.6*cm, 2.0*cm, 2.9*cm]

    rows = [[_p(h, st["th"]) for h in headers]]

    items = q.get("items", [])
    for i, item in enumerate(items, 1):
        hm  = item.get("hang_muc", "")
        kd  = item.get("kich_thuoc", "")
        sl  = _fmt_num(item.get("so_luong", ""))
        dv  = item.get("don_vi", "m²")
        dt_ = _fmt_num(item.get("dien_tich", 0))
        dg  = _fmt_money(item.get("don_gia", 0))
        tt  = _fmt_money(item.get("thanh_tien", 0))

        rows.append([
            _p(str(i), st["td_c"]),
            _p(hm,     st["td"]),
            _p(kd,     st["td_c"]),
            _p(sl,     st["td_c"]),
            _p(dv,     st["td_c"]),
            _p(dt_,    st["td_c"]),
            _p(dg,     st["td_r"]),
            _p(tt,     st["td_r"]),
        ])

    items_t = Table(rows, colWidths=col_w, repeatRows=1)
    n = len(rows)
    item_style = [
        # Header row
        ("BACKGROUND",   (0, 0), (-1, 0), BLUE_DARK),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME",     (0, 0), (-1, 0), FONT_BOLD),
        ("FONTSIZE",     (0, 0), (-1, 0), 8),
        ("GRID",         (0, 0), (-1, -1), 0.4, GRAY_MID),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]
    # Alternating rows
    for r in range(1, n):
        if r % 2 == 0:
            item_style.append(("BACKGROUND", (0, r), (-1, r), GRAY_LIGHT))

    items_t.setStyle(TableStyle(item_style))
    story.append(items_t)
    story.append(Spacer(1, 4))

    # ── TOTALS ────────────────────────────────────────────────────────────────
    tong_dt     = _fmt_num(q.get("tong_dien_tich", 0))
    tong_chua   = _fmt_money(q.get("tong_chua_vat", 0))
    vat_rate    = q.get("vat", 10)
    tong_vat    = _fmt_money(q.get("tong_vat", 0))
    tong_cong   = _fmt_money(q.get("tong_cong", 0))

    totals_rows = [
        ["", _p("Tổng diện tích:", st["total_lbl"]),
              _p(f"{tong_dt} m²", st["total_val"])],
        ["", _p("Tổng công (chưa VAT):", st["total_lbl"]),
              _p(f"{tong_chua} đ", st["total_val"])],
        ["", _p(f"VAT ({vat_rate}%):", st["total_lbl"]),
              _p(f"{tong_vat} đ", st["total_val"])],
    ]

    totals_t = Table(totals_rows, colWidths=[W - 6.5 * cm, 4 * cm, 2.5 * cm])
    totals_t.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
    ]))
    story.append(totals_t)

    # Grand total bar
    grand_t = Table(
        [["", _p("TỔNG CỘNG THANH TOÁN:", st["grand"]),
              _p(f"{tong_cong} đ", st["grand_val"])]],
        colWidths=[W - 7.5 * cm, 4.5 * cm, 3 * cm],
    )
    grand_t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), BLUE_DARK),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(grand_t)
    story.append(Spacer(1, 8))

    # ── PAYMENT TERMS + NOTES ─────────────────────────────────────────────────
    dieu_khoan = q.get("dieu_khoan", "")
    ghi_chu    = q.get("ghi_chu", "")

    left_items = [_p("<b>ĐIỀU KHOẢN THANH TOÁN:</b>", st["section"])]
    for line in (dieu_khoan or "").split("\n"):
        if line.strip():
            left_items.append(_p(f"• {line.strip()}", st["note"]))

    right_items = []
    if ghi_chu:
        right_items.append(_p("<b>GHI CHÚ:</b>", st["section"]))
        for line in ghi_chu.split("\n"):
            if line.strip():
                right_items.append(_p(f"• {line.strip()}", st["note"]))

    terms_t = Table(
        [[left_items, right_items or ""]],
        colWidths=[W * 0.6, W * 0.4],
    )
    terms_t.setStyle(TableStyle([
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",(0, 0), (-1, -1), 4),
    ]))
    story.append(terms_t)
    story.append(Spacer(1, 10))

    # ── SIGNATURE ─────────────────────────────────────────────────────────────
    nguoi_lap = q.get("nguoi_lap", "")
    ngay_sign = q.get("ngay", "")

    sign_t = Table(
        [[
            [_p("Khách hàng xác nhận", st["sign_name"]),
             Spacer(1, 30),
             _p("(Ký và ghi rõ họ tên)", st["sign_title"])],
            "",
            [_p(f"TP.HCM, ngày {ngay_sign}", st["sign_title"]),
             _p("Người lập báo giá", st["sign_name"]),
             Spacer(1, 30),
             _p(nguoi_lap, st["sign_name"]),
             _p("(Ký và ghi rõ họ tên)", st["sign_title"])],
        ]],
        colWidths=[W / 3, W / 3, W / 3],
    )
    sign_t.setStyle(TableStyle([
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",  (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
    ]))
    story.append(sign_t)

    # ── FOOTER ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_MID))
    story.append(Spacer(1, 2))
    story.append(_p(
        "Báo giá này có hiệu lực trong vòng 30 ngày kể từ ngày lập. "
        "Mọi thắc mắc xin liên hệ số điện thoại trên.",
        st["footer"]
    ))

    return story
