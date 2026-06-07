# ============================================================
#  PAYLAŞ — Dayanışma & Bağış Platformu
#  Firebase (Firestore) sürümü — profesyonel arayüz + iletişim
# ============================================================
#  GEREKLİ:
#    pip install streamlit firebase-admin
#  firebase_key.json dosyası app.py ile aynı klasörde olmalı.
# ============================================================

from datetime import date, datetime
from urllib.parse import quote
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# --- Sabitler -------------------------------------------------
CATEGORIES = ["Giyim", "Mobilya", "Elektronik", "Eğitim / Kırtasiye",
              "Ev Eşyası", "Çocuk / Oyuncak"]
from il_ilce import PROVINCES, DISTRICTS  # 81 il + ilçeleri
MANUEL = "✏️ Diğer (elle yaz)"


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
/* yazdığın metin koyu renk olsun (koyu temada beyaz kalmasın) */
.stTextInput input,.stTextArea textarea,.stNumberInput input{ color:var(--ink)!important; }
.stTextInput input::placeholder,.stTextArea textarea::placeholder{ color:#A89F92!important; }
div[data-baseweb="select"] div{ color:var(--ink)!important; }
ul[role="listbox"]{ background:#fff!important; }
ul[role="listbox"] *{ color:var(--ink)!important; }
/* seçim kutusu (selectbox) hem kapalı hem açık halde AÇIK renk */
div[data-baseweb="select"] > div{ background:#fff!important; }
div[data-baseweb="select"] *{ color:var(--ink)!important; }
[data-baseweb="menu"], [data-baseweb="menu"] ul{ background:#fff!important; }
[data-baseweb="menu"] li, [data-baseweb="menu"] li *{ color:var(--ink)!important; background:#fff!important; }
li[role="option"]{ background:#fff!important; color:var(--ink)!important; }
/* popover'ı mobil dahil her durumda AÇIK renk yap */
div[data-baseweb="popover"] > div{ background:#fff!important; }
.stFormSubmitButton button{ background:var(--green); color:#fff; border:none;
  border-radius:10px; padding:9px 22px; font-weight:700; }
.stFormSubmitButton button:hover{ background:var(--green-2); color:#fff; }
.stButton button{ background:var(--green); color:#fff; border:none;
  border-radius:10px; padding:9px 22px; font-weight:700; }
.stButton button:hover{ background:var(--green-2); color:#fff; }

/* "İletişime Geç" popover düğmesi */
div[data-testid="stPopover"] button{ background:var(--green)!important; color:#fff!important;
  border:none!important; border-radius:10px!important; font-weight:700!important; }
div[data-testid="stPopover"] button:hover{ background:var(--green-2)!important; }
/* WhatsApp link düğmesi */
[data-testid="stLinkButton"] a{ background:#25D366!important; color:#fff!important;
  border:none!important; border-radius:10px!important; font-weight:700!important; }

/* açılır kutuyu (popover) tema ne olursa olsun AÇIK renk yap */
div[data-baseweb="popover"] [data-testid="stPopoverBody"],
[data-testid="stPopoverBody"]{ background:#FFFFFF!important; border-radius:12px!important; }
[data-testid="stPopoverBody"] *{ color:var(--ink)!important; }
/* numara kutusu (st.code) açık renk */
[data-testid="stCode"]{ background:#F0EBE0!important; border:1px solid var(--line)!important; border-radius:10px!important; }
[data-testid="stCode"] code, [data-testid="stCode"] pre, [data-testid="stCode"] span{
  color:var(--ink)!important; background:transparent!important; }
/* WhatsApp düğmesi yazısı beyaz kalsın */
[data-testid="stPopoverBody"] [data-testid="stLinkButton"] a{ color:#fff!important; }

.sechead{ font-family:'Fraunces',serif; font-size:1.5rem; font-weight:600; color:var(--green); margin:4px 0 2px; }
hr{ border-color:var(--line); }

/* iletişim düğmeleri (popover içinde, HTML link) */
a.contactbtn{ display:block; text-align:center; text-decoration:none; color:#fff!important;
  border-radius:10px; padding:10px 14px; font-weight:700; margin-top:6px; }
a.contactbtn.wa{ background:#25D366; }
a.contactbtn.mail{ background:#2C6BB0; }
a.contactbtn:hover{ filter:brightness(.94); color:#fff!important; }
</style>
""", unsafe_allow_html=True)


# --- ŞEHİR + İLÇE seçici (ilçeler şehre göre, elle yazma seçenekli) ---
def sehir_ilce_sec(prefix):
    """Önce Şehir, hemen altında İlçe. İkisinde de 'elle yaz' seçeneği var."""
    sehir_sel = st.selectbox("Şehir", PROVINCES + [MANUEL], key=f"{prefix}_city")
    # şehir değişince ilçe seçimini sıfırla (eski ilçe yeni ilde olmayabilir)
    if st.session_state.get(f"{prefix}_lastcity") != sehir_sel:
        st.session_state[f"{prefix}_lastcity"] = sehir_sel
        st.session_state.pop(f"{prefix}_dist", None)

    if sehir_sel == MANUEL:
        sehir = st.text_input("Şehir (elle yaz)", key=f"{prefix}_city_manual", placeholder="Şehir adı")
        ilce_opts = [MANUEL]
    else:
        sehir = sehir_sel
        ilce_opts = DISTRICTS.get(sehir_sel, []) + [MANUEL]

    ilce_sel = st.selectbox("İlçe", ilce_opts, key=f"{prefix}_dist")
    if ilce_sel == MANUEL:
        ilce = st.text_input("İlçe (elle yaz)", key=f"{prefix}_dist_manual", placeholder="İlçe adı")
    else:
        ilce = ilce_sel
    return sehir, ilce


# --- TEK BİR KART ÇİZER (içerik + iletişim popover) -----------
def render_card(d, kind):
    cat = d.get("category", "—")
    loc = f"{d.get('district', '—')}, {d.get('city', '—')}"
    title = d.get("title", "")
    desc = (d.get("description", "") or "").strip()
    desc = (desc[:120] + "…") if len(desc) > 120 else (desc or "Açıklama eklenmemiş.")
    phone = d.get("phone", "")
    email = d.get("email", "")
    has_phone = phone and str(phone) not in ("", "Belirtilmemiş", "Açıklama yok.")
    has_email = email and str(email) not in ("", "Belirtilmemiş", "Açıklama yok.")
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

        btn_label = "📞 İletişime Geç" if has_phone else ("✉️ İletişime Geç" if has_email else "İletişim")
        with st.popover(btn_label, use_container_width=True):
            if has_phone:
                st.markdown(f"**{person}** ile iletişim:")
                st.code(phone, language=None)          # kopyalama düğmesi hazır gelir
                st.caption("Sağ üstteki simgeyle kopyalayabilirsin.")
                st.markdown(
                    f'<a class="contactbtn wa" href="{whatsapp_url(phone)}" target="_blank">'
                    f'💬 WhatsApp\'tan Yaz</a>', unsafe_allow_html=True)
            elif has_email:
                konu = quote(f"Paylaş ilanı: {title}")
                st.markdown(f"**{person}** ile iletişim:")
                st.code(email, language=None)          # kopyalama düğmesi hazır gelir
                st.caption("Sağ üstteki simgeyle kopyalayabilirsin.")
                st.markdown(
                    f'<a class="contactbtn mail" href="mailto:{email}?subject={konu}">'
                    f'📧 E-posta Gönder</a>', unsafe_allow_html=True)
            else:
                st.caption("Bu ilanda iletişim bilgisi belirtilmemiş.")


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
    if st.session_state.pop("i_done", False):
        for _k in ["i_title", "i_bagisci", "i_phone", "i_email", "i_desc",
                   "i_city", "i_city_manual", "i_dist", "i_dist_manual", "i_lastcity"]:
            st.session_state.pop(_k, None)
        st.success("Bağış ilanın başarıyla yayınlandı! 🎉")

    c1, c2 = st.columns(2)
    title = c1.text_input("Eşya Başlığı", key="i_title", placeholder="ör. Kışlık çocuk montu")
    kategori = c2.selectbox("Kategori", CATEGORIES, key="i_kat")
    durum = c1.selectbox("Eşyanın Durumu", ["Yeni Gibi", "Çok İyi", "İyi", "Orta"], key="i_durum")
    bagisci = c2.text_input("İsim Soyisim", key="i_bagisci", placeholder="ör. Elif K.")
    sehir, ilce = sehir_ilce_sec("i")
    yontem_i = st.selectbox("İletişim", ["📞 Telefon", "✉️ E-posta"], key="i_yontem")
    if yontem_i.startswith("📞"):
        phone = st.text_input("Telefon numaranız", key="i_phone", placeholder="ör. 05551234567")
        email = ""
    else:
        phone = ""
        email = st.text_input("E-posta adresiniz", key="i_email", placeholder="ör. ornek@mail.com")
    description = st.text_area("Açıklama", key="i_desc", placeholder="ör. Yırtığı yoktur, temiz durumdadır.")
    if st.button("Bağış İlanını Yayınla", key="i_submit"):
        if title and (phone or email):
            add_item({"title": title, "category": kategori, "condition": durum, "city": sehir or "—",
                      "district": ilce or "—", "donor": bagisci or "Anonim",
                      "phone": phone, "email": email, "description": description or "Açıklama yok."})
            st.session_state["i_done"] = True
            st.rerun()
        else:
            st.error("Lütfen başlık ve iletişim (telefon ya da e-posta) bilgisi gir.")

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
    if st.session_state.pop("n_done", False):
        for _k in ["n_title", "n_eden", "n_phone", "n_email", "n_desc", "n_adet",
                   "n_city", "n_city_manual", "n_dist", "n_dist_manual", "n_lastcity"]:
            st.session_state.pop(_k, None)
        st.success("Talebin başarıyla yayınlandı! 🎉")

    c1, c2 = st.columns(2)
    title = c1.text_input("İhtiyaç Başlığı", key="n_title", placeholder="ör. Üniversite hazırlık kitapları")
    kategori = c2.selectbox("Kategori", CATEGORIES, key="n_kat")
    adet = c1.number_input("Gerekli Adet", min_value=1, value=1, step=1, key="n_adet")
    eden = c2.text_input("İsim Soyisim", key="n_eden", placeholder="ör. Ayşe Y.")
    sehir, ilce = sehir_ilce_sec("n")
    yontem_n = st.selectbox("İletişim", ["📞 Telefon", "✉️ E-posta"], key="n_yontem")
    if yontem_n.startswith("📞"):
        phone = st.text_input("Telefon numaranız", key="n_phone", placeholder="ör. 05321234567")
        email = ""
    else:
        phone = ""
        email = st.text_input("E-posta adresiniz", key="n_email", placeholder="ör. ornek@mail.com")
    description = st.text_area("Açıklama", key="n_desc", placeholder="ör. Öğrenci yurdunda kalıyorum, kitap setine ihtiyacım var.")
    if st.button("Talebi Yayınla", key="n_submit"):
        if title and (phone or email):
            add_need({"title": title, "category": kategori, "quantity": int(adet), "city": sehir or "—",
                      "district": ilce or "—", "requester": eden or "Anonim",
                      "phone": phone, "email": email, "description": description or "Açıklama yok."})
            st.session_state["n_done"] = True
            st.rerun()
        else:
            st.error("Lütfen başlık ve iletişim (telefon ya da e-posta) bilgisi gir.")

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
