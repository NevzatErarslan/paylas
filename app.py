# ============================================================
#  PAYLAŞ — Dayanışma & Bağış Platformu
#  Firebase (Firestore) sürümü — profesyonel arayüz
# ============================================================
#  GEREKLİ:
#    pip install streamlit firebase-admin
#  firebase_key.json dosyası app.py ile aynı klasörde olmalı.
# ============================================================

from datetime import date, datetime
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# --- Sabitler -------------------------------------------------
CATEGORIES = ["Giyim", "Mobilya", "Elektronik", "Eğitim / Kırtasiye",
              "Ev Eşyası", "Çocuk / Oyuncak"]
CITIES = ["Ankara", "İstanbul", "İzmir", "Bursa", "Antalya"]


# --- Firebase bağlantısı -------------------------------------
@st.cache_resource
def get_db():
    """Firebase'e tek sefer bağlanır (JSON dosyasıyla)."""
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
    return firestore.client()


db = get_db()


# --- Veri fonksiyonları (Firestore) --------------------------
def add_item(d):
    db.collection("items").add({**d, "date": date.today().isoformat(),
                                "created": datetime.utcnow().isoformat()})


def add_need(d):
    db.collection("needs").add({**d, "date": date.today().isoformat(),
                                "created": datetime.utcnow().isoformat()})


def get_items():
    rows = [{**doc.to_dict(), "id": doc.id} for doc in db.collection("items").stream()]
    rows.sort(key=lambda r: r.get("created", ""), reverse=True)
    return rows


def get_needs():
    rows = [{**doc.to_dict(), "id": doc.id} for doc in db.collection("needs").stream()]
    rows.sort(key=lambda r: r.get("created", ""), reverse=True)
    return rows


# ============================================================
#  SAYFA AYARI + TASARIM (CSS)
# ============================================================
st.set_page_config(page_title="Paylaş — Dayanışma Platformu",
                   page_icon="🤝", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root{
  --green:#1A5D4E; --green-2:#2C8A6E; --coral:#E07A5F;
  --amber:#C77D3A; --paper:#F6F3EC; --card:#FFFFFF;
  --ink:#241F1A; --muted:#857B6E; --line:#E7DFD2;
}

/* genel */
.stApp{ background:var(--paper); }
html,body,[class*="css"],.stApp,p,span,div,label,input,textarea,select{
  font-family:'Plus Jakarta Sans',sans-serif; color:var(--ink);
}
.block-container{ padding-top:1.2rem; max-width:1180px; }
#MainMenu, footer, header[data-testid="stHeader"]{ visibility:hidden; height:0; }

/* HERO */
.hero{ text-align:center; padding:8px 0 4px; }
.hero .logo{
  font-family:'Fraunces',serif; font-weight:700; font-size:3.1rem;
  letter-spacing:-1px; color:var(--green); line-height:1; margin:0;
}
.hero .logo .dot{ color:var(--coral); }
.hero .tag{ color:var(--muted); font-size:1.05rem; margin-top:6px; }

/* istatistik şeridi */
.stats{ display:flex; gap:14px; justify-content:center; margin:18px 0 6px; flex-wrap:wrap; }
.stat{
  background:var(--card); border:1px solid var(--line); border-radius:16px;
  padding:14px 26px; text-align:center; min-width:150px;
  box-shadow:0 1px 2px rgba(36,31,26,.04);
}
.stat .num{ font-family:'Fraunces',serif; font-size:1.9rem; font-weight:700; color:var(--green); line-height:1; }
.stat .lbl{ font-size:.82rem; color:var(--muted); margin-top:4px; text-transform:uppercase; letter-spacing:.5px; }

/* sütun başlıkları */
.colhead{ display:flex; align-items:center; gap:10px; padding:12px 16px;
  border-radius:14px; margin:8px 0 16px; font-weight:700; font-size:1.15rem; color:#fff; }
.colhead.give{ background:linear-gradient(135deg,#1A5D4E,#2C8A6E); }
.colhead.need{ background:linear-gradient(135deg,#B85C38,#E07A5F); }

/* ilan kartı */
.lcard{
  background:var(--card); border:1px solid var(--line); border-radius:16px;
  padding:16px 18px; margin-bottom:14px; transition:.18s ease;
  box-shadow:0 1px 2px rgba(36,31,26,.04);
}
.lcard:hover{ transform:translateY(-2px); box-shadow:0 8px 22px rgba(36,31,26,.10); }
.lcard.donation{ border-left:4px solid var(--green-2); }
.lcard.request{ border-left:4px solid var(--coral); }
.lhead{ display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:8px; }
.badge{ font-size:.72rem; font-weight:700; padding:4px 10px; border-radius:999px; letter-spacing:.3px; }
.donation-b{ background:#E4F1EC; color:#1A5D4E; }
.request-b{ background:#FBE9E2; color:#B85C38; }
.lloc{ font-size:.8rem; color:var(--muted); }
.ltitle{ font-family:'Fraunces',serif; font-size:1.22rem; font-weight:600; color:var(--ink); margin:2px 0 6px; }
.qty{ font-size:.72rem; background:#F0EBE0; color:var(--muted); padding:2px 8px; border-radius:8px; font-family:'Plus Jakarta Sans'; vertical-align:middle; }
.ldesc{ font-size:.9rem; color:var(--muted); line-height:1.45; margin-bottom:12px; }
.lfoot{ display:flex; justify-content:space-between; align-items:center; gap:8px;
  border-top:1px solid var(--line); padding-top:10px; flex-wrap:wrap; }
.lperson{ font-size:.85rem; color:var(--ink); }
.lphone{ font-size:.83rem; font-weight:700; text-decoration:none; color:#fff !important;
  background:var(--green); padding:6px 14px; border-radius:999px; }
.lphone:hover{ background:var(--green-2); }
.lphone-muted{ font-size:.8rem; color:var(--muted); }
.empty{ text-align:center; color:var(--muted); padding:30px; border:1px dashed var(--line);
  border-radius:16px; background:var(--card); }

/* grid (havuz sekmeleri) */
.grid{ display:grid; grid-template-columns:repeat(auto-fill,minmax(290px,1fr)); gap:14px; }

/* sekmeler */
.stTabs [data-baseweb="tab-list"]{ gap:8px; border-bottom:none; }
.stTabs [data-baseweb="tab"]{
  background:#EFEADF; border-radius:12px; padding:10px 18px; font-weight:600; color:var(--muted);
}
.stTabs [aria-selected="true"]{ background:var(--green) !important; color:#fff !important; }
.stTabs [data-baseweb="tab-highlight"]{ display:none; }

/* form bileşenleri */
.stTextInput input,.stTextArea textarea,.stNumberInput input,
div[data-baseweb="select"]>div{
  border-radius:10px !important; border:1.5px solid var(--line) !important; background:#fff !important;
}
.stTextInput input:focus,.stTextArea textarea:focus{ border-color:var(--green-2) !important; }
.stButton button,.stFormSubmitButton button{
  background:var(--green); color:#fff; border:none; border-radius:10px;
  padding:9px 22px; font-weight:700; transition:.15s;
}
.stButton button:hover,.stFormSubmitButton button:hover{ background:var(--green-2); color:#fff; }
.sechead{ font-family:'Fraunces',serif; font-size:1.5rem; font-weight:600; color:var(--green); margin:4px 0 2px; }
hr{ border-color:var(--line); }
</style>
""", unsafe_allow_html=True)


# --- Kart üretici (tek satır HTML, markdown bozulmasın diye) ---
def card_html(title, cat, kind, loc, desc, person_label, person, phone, qty=None):
    d = (desc or "").strip()
    d = (d[:120] + "…") if len(d) > 120 else (d or "Açıklama eklenmemiş.")
    if phone and phone not in ("", "Belirtilmemiş"):
        ph = f'<a class="lphone" href="tel:{phone}">📞 İletişime Geç</a>'
    else:
        ph = '<span class="lphone-muted">📞 Telefon yok</span>'
    q = f' <span class="qty">×{qty}</span>' if qty else ""
    bcls = "donation" if kind == "donation" else "request"
    return (
        f'<div class="lcard {bcls}">'
        f'<div class="lhead"><span class="badge {bcls}-b">{cat}</span>'
        f'<span class="lloc">📍 {loc}</span></div>'
        f'<div class="ltitle">{title}{q}</div>'
        f'<div class="ldesc">{d}</div>'
        f'<div class="lfoot"><span class="lperson">{person_label}: <b>{person}</b></span>{ph}</div>'
        f'</div>'
    )


# --- HERO + İSTATİSTİK ---------------------------------------
items_all = get_items()
needs_all = get_needs()
sehir_sayisi = len({*[i.get("city", "") for i in items_all],
                    *[n.get("city", "") for n in needs_all]} - {""})

st.markdown(
    '<div class="hero"><div class="logo">Payla<span class="dot">ş</span></div>'
    '<div class="tag">İhtiyaç fazlasını, ihtiyaç sahibiyle buluşturan ücretsiz dayanışma platformu.</div></div>',
    unsafe_allow_html=True)

st.markdown(
    f'<div class="stats">'
    f'<div class="stat"><div class="num">{len(items_all)}</div><div class="lbl">Aktif Bağış</div></div>'
    f'<div class="stat"><div class="num">{len(needs_all)}</div><div class="lbl">Açık Talep</div></div>'
    f'<div class="stat"><div class="num">{sehir_sayisi}</div><div class="lbl">Şehir</div></div>'
    f'</div>', unsafe_allow_html=True)

st.write("")
tab_home, tab_items, tab_needs = st.tabs(
    ["🏠  Canlı Akış", "🎁  Bağış Ekle", "📦  Talep Ekle"])

# --- Sekme 1: CANLI AKIŞ -------------------------------------
with tab_home:
    col_g, col_n = st.columns(2, gap="large")

    with col_g:
        st.markdown('<div class="colhead give">🟢 Bağışlanan Eşyalar</div>', unsafe_allow_html=True)
        if not items_all:
            st.markdown('<div class="empty">Henüz bağışlanan bir eşya yok.<br>İlk paylaşan sen ol! 🎁</div>', unsafe_allow_html=True)
        else:
            html = "".join(card_html(it["title"], it["category"], "donation",
                                     f"{it['district']}, {it['city']}",
                                     it.get("description", ""), "Bağışçı", it.get("donor", "Anonim"),
                                     it.get("phone", "")) for it in items_all)
            st.markdown(html, unsafe_allow_html=True)

    with col_n:
        st.markdown('<div class="colhead need">🔴 İhtiyaç Talepleri</div>', unsafe_allow_html=True)
        if not needs_all:
            st.markdown('<div class="empty">Henüz oluşturulmuş bir talep yok.</div>', unsafe_allow_html=True)
        else:
            html = "".join(card_html(n["title"], n["category"], "request",
                                     f"{n['district']}, {n['city']}",
                                     n.get("description", ""), "Talep eden", n.get("requester", "Anonim"),
                                     n.get("phone", ""), n.get("quantity", 1)) for n in needs_all)
            st.markdown(html, unsafe_allow_html=True)

# --- Sekme 2: BAĞIŞ EKLE -------------------------------------
with tab_items:
    st.markdown('<div class="sechead">Eşya Paylaş</div>', unsafe_allow_html=True)
    st.caption("İhtiyaç fazlası eşyanı birkaç bilgiyle paylaş, ihtiyaç sahibine ulaşsın.")
    with st.form("item_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        title = c1.text_input("Eşya Başlığı", placeholder="ör. Kışlık çocuk montu")
        kategori = c2.selectbox("Kategori", CATEGORIES)
        durum = c1.selectbox("Eşyanın Durumu", ["Yeni Gibi", "Çok İyi", "İyi", "Orta"])
        sehir = c2.selectbox("Bulunduğu Şehir", CITIES)
        ilce = c1.text_input("İlçe", placeholder="ör. Çankaya")
        bagisci = c2.text_input("İsim Soyisim", placeholder="ör. Elif K.")
        phone = st.text_input("İletişim Telefonu", placeholder="ör. 05551234567")
        description = st.text_area("Açıklama", placeholder="ör. Yırtığı yoktur, temiz durumdadır.")
        gonder = st.form_submit_button("Bağış İlanını Yayınla")
        if gonder and title and phone:
            add_item({"title": title, "category": kategori, "condition": durum, "city": sehir,
                      "district": ilce or "—", "donor": bagisci or "Anonim",
                      "phone": phone, "description": description or "Açıklama yok."})
            st.success("Bağış ilanın başarıyla yayınlandı!")
            st.rerun()
        elif gonder and not phone:
            st.error("Lütfen iletişim için telefon numaranı gir.")

    st.markdown("---")
    st.markdown('<div class="sechead">Tüm Bağış İlanları</div>', unsafe_allow_html=True)
    f1, f2 = st.columns([1, 2])
    fk = f1.selectbox("Kategori", ["Hepsi"] + CATEGORIES, key="fi")
    fs = f2.text_input("İlanlarda ara", placeholder="ör. mont, koltuk, kitap...", key="si")

    sonuc = []
    for it in items_all:
        if fk != "Hepsi" and it["category"] != fk:
            continue
        if fs and fs.lower() not in (it["title"] + " " + it.get("description", "")).lower():
            continue
        sonuc.append(it)
    if sonuc:
        html = "".join(card_html(it["title"], it["category"], "donation",
                                 f"{it['district']}, {it['city']}", it.get("description", ""),
                                 "Bağışçı", it.get("donor", "Anonim"), it.get("phone", "")) for it in sonuc)
        st.markdown(f'<div class="grid">{html}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty">Aramana uyan bağış bulunamadı.</div>', unsafe_allow_html=True)

# --- Sekme 3: TALEP EKLE -------------------------------------
with tab_needs:
    st.markdown('<div class="sechead">İhtiyaç Talebi Oluştur</div>', unsafe_allow_html=True)
    st.caption("İhtiyacını paylaş, bağışçılar sana ulaşsın.")
    with st.form("need_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        title = c1.text_input("İhtiyaç Başlığı", placeholder="ör. Üniversite hazırlık kitapları")
        kategori = c2.selectbox("Kategori", CATEGORIES, key="nk")
        adet = c1.number_input("Gerekli Adet", min_value=1, value=1, step=1)
        sehir = c2.selectbox("Yaşadığın Şehir", CITIES, key="nc")
        ilce = c1.text_input("İlçe", placeholder="ör. Mamak", key="nd")
        eden = c2.text_input("İsim Soyisim", placeholder="ör. Ayşe Y.")
        phone = st.text_input("İletişim Telefonu", placeholder="ör. 05321234567", key="np")
        description = st.text_area("Açıklama", placeholder="ör. Öğrenci yurdunda kalıyorum, kitap setine ihtiyacım var.", key="ndsc")
        gonder = st.form_submit_button("Talebi Yayınla")
        if gonder and title and phone:
            add_need({"title": title, "category": kategori, "quantity": int(adet), "city": sehir,
                      "district": ilce or "—", "requester": eden or "Anonim",
                      "phone": phone, "description": description or "Açıklama yok."})
            st.success("Talebin başarıyla yayınlandı!")
            st.rerun()
        elif gonder and not phone:
            st.error("Lütfen iletişim için telefon numaranı gir.")

    st.markdown("---")
    st.markdown('<div class="sechead">Tüm İhtiyaç Talepleri</div>', unsafe_allow_html=True)
    f1, f2 = st.columns([1, 2])
    fk = f1.selectbox("Kategori", ["Hepsi"] + CATEGORIES, key="fn")
    fs = f2.text_input("İlanlarda ara", placeholder="ör. tablet, battaniye, çanta...", key="sn")

    sonuc = []
    for n in needs_all:
        if fk != "Hepsi" and n["category"] != fk:
            continue
        if fs and fs.lower() not in (n["title"] + " " + n.get("description", "")).lower():
            continue
        sonuc.append(n)
    if sonuc:
        html = "".join(card_html(n["title"], n["category"], "request",
                                 f"{n['district']}, {n['city']}", n.get("description", ""),
                                 "Talep eden", n.get("requester", "Anonim"),
                                 n.get("phone", ""), n.get("quantity", 1)) for n in sonuc)
        st.markdown(f'<div class="grid">{html}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty">Aramana uyan talep bulunamadı.</div>', unsafe_allow_html=True)
