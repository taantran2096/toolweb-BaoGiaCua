/* script.js – client-side logic for the quote editor */

"use strict";

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtMoney(val) {
  const n = parseFloat(val) || 0;
  return n.toLocaleString("vi-VN");
}

function parseMoney(str) {
  return parseFloat((str || "").replace(/\./g, "").replace(/,/g, ".")) || 0;
}

function parseNum(str) {
  return parseFloat((str || "").replace(/,/g, ".")) || 0;
}

// ── Row sequencing ────────────────────────────────────────────────────────────

function resequence() {
  document.querySelectorAll("#itemsBody .item-row").forEach((row, i) => {
    const stt = row.querySelector(".td-stt");
    if (stt) stt.textContent = i + 1;
  });
}

// ── Per-row calculation ───────────────────────────────────────────────────────

function calcRow(row) {
  const kd   = (row.querySelector(".ipt-kichthuoc")?.value || "").trim();
  const sl   = parseNum(row.querySelector(".ipt-soluong")?.value);
  const dv   = row.querySelector(".ipt-donvi")?.value || "m²";
  const dtEl = row.querySelector(".ipt-dientich");
  const dgEl = row.querySelector(".ipt-dongia");
  const ttEl = row.querySelector(".ipt-thanhtien");

  let dientich = parseNum(dtEl?.value);

  // Auto-calc area from dimension string (e.g. 1.2x2.4)
  if (!dientich && kd && /\d/.test(kd)) {
    const parts = kd.toLowerCase().replace(/\s/g, "").split("x");
    if (parts.length === 2) {
      const w = parseNum(parts[0]);
      const h = parseNum(parts[1]);
      if (w > 0 && h > 0) {
        dientich = Math.round(w * h * sl * 1000) / 1000;
        if (dtEl) dtEl.value = dientich;
      }
    }
  }

  const dongia = parseNum(dgEl?.value);
  let thanhtien;
  if (dv === "m²" && dientich > 0) {
    thanhtien = Math.round(dientich * dongia);
  } else {
    thanhtien = Math.round(sl * dongia);
  }
  if (ttEl) ttEl.value = thanhtien;

  return { dientich, thanhtien };
}

// ── Full recalculation ────────────────────────────────────────────────────────

function recalc() {
  let totalDt = 0;
  let totalChuaVat = 0;

  document.querySelectorAll("#itemsBody .item-row").forEach(row => {
    const { dientich, thanhtien } = calcRow(row);
    totalDt      += dientich || 0;
    totalChuaVat += thanhtien || 0;
  });

  const vatRate = parseNum(document.getElementById("vat")?.value) / 100;
  const tong_vat  = Math.round(totalChuaVat * vatRate);
  const tongCong  = totalChuaVat + tong_vat;

  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val;
  };

  set("tong_dien_tich", Math.round(totalDt * 1000) / 1000);
  set("tong_chua_vat",  fmtMoney(totalChuaVat));
  set("tong_vat",       fmtMoney(tong_vat));
  set("tong_cong",      fmtMoney(tongCong));
}

// ── Add / delete rows ─────────────────────────────────────────────────────────

function addRow() {
  const tbody = document.getElementById("itemsBody");
  const row = document.createElement("tr");
  row.className = "item-row";
  row.innerHTML = `
    <td class="td-stt"></td>
    <td><input type="text"   class="ipt ipt-hangmuc"   placeholder="Tên hạng mục"></td>
    <td><input type="text"   class="ipt ipt-kichthuoc" placeholder="1.2x2.4"></td>
    <td><input type="number" class="ipt ipt-soluong"   value="1" min="0" step="0.01"></td>
    <td>
      <select class="ipt ipt-donvi">
        <option>m²</option>
        <option>bộ</option>
        <option>cái</option>
        <option>mét</option>
        <option>cây</option>
      </select>
    </td>
    <td><input type="number" class="ipt ipt-dientich" value="0" min="0" step="0.001" placeholder="Tự tính"></td>
    <td><input type="number" class="ipt ipt-dongia"   value="0" min="0" step="1000"></td>
    <td><input type="number" class="ipt ipt-thanhtien" value="0" min="0" readonly></td>
    <td><button type="button" class="btn-del-row" onclick="deleteRow(this)" title="Xóa">✕</button></td>
  `;
  tbody.appendChild(row);
  attachRowListeners(row);
  resequence();
}

function deleteRow(btn) {
  const row = btn.closest(".item-row");
  if (row) {
    row.remove();
    resequence();
    recalc();
  }
}

// ── Event listeners ───────────────────────────────────────────────────────────

function attachRowListeners(row) {
  row.querySelectorAll(".ipt:not(.ipt-thanhtien)").forEach(el => {
    el.addEventListener("input", () => { calcRow(row); recalc(); });
    el.addEventListener("change", () => { calcRow(row); recalc(); });
  });
}

// Attach listeners to all existing rows on page load
document.querySelectorAll("#itemsBody .item-row").forEach(attachRowListeners);

// ── Save quote ────────────────────────────────────────────────────────────────

function collectQuoteData() {
  const g = id => (document.getElementById(id)?.value || "").trim();

  const items = [];
  document.querySelectorAll("#itemsBody .item-row").forEach(row => {
    items.push({
      hang_muc  : row.querySelector(".ipt-hangmuc")?.value.trim()  || "",
      kich_thuoc: row.querySelector(".ipt-kichthuoc")?.value.trim() || "",
      so_luong  : parseNum(row.querySelector(".ipt-soluong")?.value),
      don_vi    : row.querySelector(".ipt-donvi")?.value || "m²",
      dien_tich : parseNum(row.querySelector(".ipt-dientich")?.value),
      don_gia   : parseNum(row.querySelector(".ipt-dongia")?.value),
      thanh_tien: parseNum(row.querySelector(".ipt-thanhtien")?.value),
    });
  });

  return {
    id          : g("quoteId"),
    so_bao_gia  : g("so_bao_gia"),
    ngay        : g("ngay"),
    cong_ty     : g("cong_ty"),
    dia_chi_ct  : g("dia_chi_ct"),
    dien_thoai_ct: g("dien_thoai_ct"),
    email_ct    : g("email_ct"),
    khach_hang  : g("khach_hang"),
    dien_thoai  : g("dien_thoai"),
    dia_chi     : g("dia_chi"),
    vat         : parseNum(g("vat")),
    dieu_khoan  : document.getElementById("dieu_khoan")?.value || "",
    ghi_chu     : document.getElementById("ghi_chu")?.value    || "",
    nguoi_lap   : g("nguoi_lap"),
    items,
  };
}

async function saveQuote() {
  const data = collectQuoteData();
  try {
    const res  = await fetch("/save", {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify(data),
    });
    const json = await res.json();
    if (json.success) {
      showToast("✅ Đã lưu báo giá!", "success");
      // Update hidden id field so subsequent saves update instead of create
      const idEl = document.getElementById("quoteId");
      if (idEl && !idEl.value) idEl.value = json.id;
      // Redirect to edit page with proper id after a moment
      setTimeout(() => {
        if (!data.id) window.location.href = `/edit/${json.id}`;
      }, 900);
    } else {
      showToast("❌ Lỗi khi lưu", "error");
    }
  } catch (e) {
    showToast("❌ Lỗi kết nối", "error");
  }
}

// ── Toast ─────────────────────────────────────────────────────────────────────

function showToast(msg, type = "") {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = msg;
  el.className = `toast ${type}`;
  clearTimeout(el._timer);
  el._timer = setTimeout(() => { el.className = "toast hidden"; }, 3000);
}
