# ============================================================
#  PAYLAŞ — Dayanışma & Bağış Platformu
#  Firebase (Firestore) sürümü — profesyonel arayüz + iletişim
# ============================================================
#  GEREKLİ:
#    pip install streamlit firebase-admin
#  firebase_key.json dosyası app.py ile aynı klasörde olmalı.
# ============================================================

from datetime import date, datetime
import streamlit as st
import firebase_admin
import json
from firebase_admin import credentials, firestore

# --- Sabitler -------------------------------------------------
CATEGORIES = ["Giyim", "Mobilya", "Elektronik", "Eğitim / Kırtasiye",
              "Ev Eşyası", "Çocuk / Oyuncak"]
CITIES = ["Ankara", "İstanbul", "İzmir", "Bursa", "Antalya"]


# --- Firebase bağlantısı -------------------------------------
@st.cache_resource
def get_db():
    """Firebase'e tek sefer bağlanır (Gelişmiş bulut uyumlu sürüm)."""
    if not firebase_admin._apps:
        # Eğer site Streamlit Cloud'da çalışıyorsa şifreyi Secrets'tan oku
        if "firebase_json" in st.secrets:
            key_dict = json.loads(st.secrets["firebase_json"])
            cred = credentials.Certificate(key_dict)
        # Eğer kendi bilgisayarında çalışıyorsa yerel dosyadan oku
        else:
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


def whatsapp_url(phone):
    """Telefonu WhatsApp linkine çevirir (TR formatı: 90...)."""
    d = "".join(ch for ch in str(phone) if ch.isdigit())
    if d.startswith("0"):
        d = "90" + d[1:]
    elif len(d) == 10:
        d = "90" + d
    return f"https://wa.me/{d}"


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
  --paper:#F6F3EC; --card:#FFFFFF; --ink:#241F1A; --muted:#857B6E; --line:#E7DFD2;
}
.stApp{ background:var(--paper); }
html,body,[class*="css"],.stApp,p,span,div,label,input,textarea,select{
  font-family:'Plus Jakarta Sans',sans-serif; color:var(--ink);
}
.block-container{ padding-top:1.2rem; max-width:1180px; }
#MainMenu, footer, header[data-testid="stHeader"]{ visibility:hidden; height:0; }

/* HERO */
.hero{ text-align:center; padding:8px 0 4px; }
.hero .logo{ font-family:'Fraunces',serif; font-weight:700; font-size:3.1rem;
  letter-spacing:-1px; color:var(--green); line-height:1; margin:0; }
.hero .logo .dot{ color:var(--coral); }
.hero .tag{ color:var(--muted); font-size:1.05rem; margin-top:6px; }

/* istatistik şeridi */
.stats{ display:flex; gap:14px; justify-content:center; margin:18px 0 6px; flex-wrap:wrap; }
.stat{ background:var(--card); border:1px solid var(--line); border-radius:16px;
  padding:14px 26px; text-align:center; min-width:150px; box-shadow:0 1px 2px rgba(36,31,26,.04); }
.stat .num{ font-family:'Fraunces',serif; font-size:1.9rem; font-weight:700; color:var(--green); line-height:1; }
.stat .lbl{ font-size:.82rem; color:var(--muted); margin-top:4px; text-transform:uppercase; letter-spacing:.5px; }

/* sütun başlıkları */
.colhead{ padding:12px 16px; border-radius:14px; margin:8px 0 16px;
  font-weight:700; font-size:1.15rem; color:#fff; text-align:center; }
.colhead.give{ background:linear-gradient(135deg,#1A5D4E,#2C8A6E); }
.colhead.need{ background:linear-gradient(135deg,#B85C38,#E07A5F); }

/* native kart (st.container border) */
div[data-testid="stVerticalBlockBorderWrapper"]{
  border:1px solid var(--line)!important; border-radius:16px!important;
  background:var(--card); box-shadow:0 1px 2px rgba(36,31,26,.04); transition:.18s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover{
  box-shadow:0 8px 22px rgba(36,31,26,.10); transform:translateY(-2px);
}

/* kart içeriği */
.lhead{ display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:6px; }
.badge{ font-size:.72rem; font-weight:700; padding:4px 10px; border-radius:999px; letter-spacing:.3px; }
.donation-b{ background:#E4F1EC; color:#1A5D4E; }
.request-b{ background:#FBE9E2; color:#B85C38; }
.lloc{ font-size:.8rem; color:var(--muted); }
.ltitle{ font-family:'Fraunces',serif; font-size:1.2rem; font-weight:600; color:var(--ink); margin:2px 0 6px; }
.qty{ font-size:.72rem; background:#F0EBE0; color:var(--muted); padding:2px 8px;
  border-radius:8px; vertical-align:middle; }
.ldesc{ font-size:.9rem; color:var(--muted); line-height:1.45; margin-bottom:8px; }
.lperson{ font-size:.85rem; color:var(--ink); margin-bottom:8px; }
.empty{ text-align:center; color:var(--muted); padding:30px; border:1px dashed var(--line);
  border-radius:16px; background:var(--card); }

/* sekmeler */
.stTabs [data-baseweb="tab-list"]{ gap:8px; border-bottom:none; }
.stTabs [data-baseweb="tab"]{ background:#EFEADF; border-radius:12px; padding:10px 18px;
  font-weight:600; color:var(--muted); }
.stTabs [aria-selected="true"]{ background:var(--green)!important; color:#fff!important; }
.stTabs [data-baseweb="tab-highlight"]{ display:none; }

/* form bileşenleri */
.stTextInput input,.stTextArea textarea,.stNumberInput input,
div[data-baseweb="select"]>div{ border-radius:10px!important;
  border:1.5px solid var(--line)!important; background:#fff!important; }
.stTextInput input:focus,.stTextArea textarea:focus{ border-color:var(--green-2)!important; }
.stFormSubmitButton button{ background:var(--green); color:#fff; border:none;
  border-radius:10px; padding:9px 22px; font-weight:700; }
.stFormSubmitButton button:hover{ background:var(--green-2); color:#fff; }

/* "İletişime Geç" popover düğmesi */
div[data-testid="stPopover"] button{ background:var(--green)!important; color:#fff!important;
  border:none!important; border-radius:10px!important; font-weight:700!important; }
div[data-testid="stPopover"] button:hover{ background:var(--green-2)!important; }
/* WhatsApp link düğmesi */
[data-testid="stLinkButton"] a{ background:#25D366!important; color:#fff!important;
  border:none!important; border-radius:10px!important; font-weight:700!important; }

.sechead{ font-family:'Fraunces',serif; font-size:1.5rem; font-weight:600; color:var(--green); margin:4px 0 2px; }
hr{ border-color:var(--line); }
</style>
""", unsafe_allow_html=True)


# --- TEK BİR KART ÇİZER (içerik + iletişim popover) -----------
def render_card(d, kind):
    cat = d.get("category", "—")
    loc = f"{d.get('district', '—')}, {d.get('city', '—')}"
    title = d.get("title", "")
    desc = (d.get("description", "") or "").strip()
    desc = (desc[:120] + "…") if len(desc) > 120 else (desc or "Açıklama eklenmemiş.")
    phone = d.get("phone", "")
    bcls = "donation" if kind == "donation" else "request"
    if kind == "donation":
        person_label, person = "Bağışçı", d.get("donor", "Anonim")
        q = ""
    else:
        person_label, person = "Talep eden", d.get("requester", "Anonim")
        adet = d.get("quantity", 1)
        q = f' <span class="qty">×{adet}</span>'

    with st.container(border=True):
        st.markdown(
            f'<div class="lhead"><span class="badge {bcls}-b">{cat}</span>'
            f'<span class="lloc">📍 {loc}</span></div>'
            f'<div class="ltitle">{title}{q}</div>'
            f'<div class="ldesc">{desc}</div>'
            f'<div class="lperson">{person_label}: <b>{person}</b></div>',
            unsafe_allow_html=True)

        with st.popover("📞 İletişime Geç", use_container_width=True):
            if phone and str(phone) not in ("", "Belirtilmemiş", "Açıklama yok."):
                st.markdown(f"**{person}** ile iletişim:")
                st.code(phone, language=None)          # kopyalama düğmesi hazır gelir
                st.caption("Numaranın sağ üstündeki simgeyle kopyalayabilirsin.")
                st.link_button("💬 WhatsApp'tan Yaz", whatsapp_url(phone),
                               use_container_width=True)
            else:
                st.caption("Bu ilanda iletişim numarası belirtilmemiş.")


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
        for it in items_all:
            render_card(it, "donation")
    with col_n:
        st.markdown('<div class="colhead need">🔴 İhtiyaç Talepleri</div>', unsafe_allow_html=True)
        if not needs_all:
            st.markdown('<div class="empty">Henüz oluşturulmuş bir talep yok.</div>', unsafe_allow_html=True)
        for n in needs_all:
            render_card(n, "request")

# --- Sekme 2: BAĞIŞ EKLE -------------------------------------
with tab_items:
    st.markdown('<div class="sechead">Eşya Paylaş</div>', unsafe_allow_html=True)
    st.caption("İhtiyaç fazlası eşyanı paylaş, ihtiyaç sahibine ulaşsın.")
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
    sonuc = [it for it in items_all
             if (fk == "Hepsi" or it["category"] == fk)
             and (not fs or fs.lower() in (it["title"] + " " + it.get("description", "")).lower())]
    if sonuc:
        cols = st.columns(2, gap="medium")
        for i, it in enumerate(sonuc):
            with cols[i % 2]:
                render_card(it, "donation")
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
    sonuc = [n for n in needs_all
             if (fk == "Hepsi" or n["category"] == fk)
             and (not fs or fs.lower() in (n["title"] + " " + n.get("description", "")).lower())]
    if sonuc:
        cols = st.columns(2, gap="medium")
        for i, n in enumerate(sonuc):
            with cols[i % 2]:
                render_card(n, "request")
    else:
        st.markdown('<div class="empty">Aramana uyan talep bulunamadı.</div>', unsafe_allow_html=True)
