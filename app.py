# ============================================================
#  PAYLAŞ — Dayanışma & Bağış Platformu
#  Firebase (Firestore) sürümü — profesyonel arayüz + harita
# ============================================================
#  GEREKLİ:
#    pip install streamlit firebase-admin pandas
# ============================================================

from datetime import date, datetime
from urllib.parse import quote
import random
import pandas as pd
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

# --- Sabitler -------------------------------------------------
CATEGORIES = ["Giyim", "Mobilya", "Elektronik", "Eğitim / Kırtasiye",
              "Ev Eşyası", "Çocuk / Oyuncak"]
from il_ilce import PROVINCES, DISTRICTS  # 81 il + ilçeleri
MANUEL = "✏️ Diğer (elle yaz)"

# Türkiye 81 İl Koordinatları (Harita için)
COORDS = {
    "Adana": [37.0, 35.32], "Adıyaman": [37.76, 38.27], "Afyonkarahisar": [38.75, 30.55],
    "Ağrı": [39.72, 43.05], "Aksaray": [38.36, 34.02], "Amasya": [40.65, 35.83],
    "Ankara": [39.92, 32.85], "Antalya": [36.88, 30.70], "Ardahan": [41.11, 42.70],
    "Artvin": [41.18, 41.81], "Aydın": [37.83, 27.84], "Balıkesir": [39.64, 27.88],
    "Bartın": [41.63, 32.33], "Batman": [37.88, 41.13], "Bayburt": [40.25, 40.22],
    "Bilecik": [40.14, 29.97], "Bingöl": [38.88, 40.49], "Bitlis": [38.40, 42.10],
    "Bolu": [40.73, 31.60], "Burdur": [37.71, 30.28], "Bursa": [40.18, 29.06],
    "Çanakkale": [40.15, 26.40], "Çankırı": [40.60, 33.61], "Çorum": [40.54, 34.95],
    "Denizli": [37.77, 29.08], "Diyarbakır": [37.91, 40.23], "Düzce": [40.83, 31.15],
    "Edirne": [41.67, 26.55], "Elazığ": [38.68, 39.22], "Erzincan": [39.75, 39.49],
    "Erzurum": [39.90, 41.27], "Eskişehir": [39.77, 30.52], "Gaziantep": [37.06, 37.38],
    "Giresun": [40.91, 38.39], "Gümüşhane": [40.46, 39.48], "Hakkari": [37.57, 43.74],
    "Hatay": [36.20, 36.15], "Iğdır": [39.92, 44.04], "Isparta": [37.76, 30.55],
    "İstanbul": [41.00, 28.97], "İzmir": [38.41, 27.13], "Kahramanmaraş": [37.57, 36.92],
    "Karabük": [41.20, 32.62], "Karaman": [37.18, 33.22], "Kars": [40.60, 43.09],
    "Kastamonu": [41.37, 33.77], "Kayseri": [38.72, 35.48], "Kırıkkale": [39.84, 33.51],
    "Kırklareli": [41.73, 27.22], "Kırşehir": [39.14, 34.16], "Kilis": [36.71, 37.11],
    "Kocaeli": [40.85, 29.88], "Konya": [37.86, 32.48], "Kütahya": [39.42, 29.98],
    "Malatya": [38.35, 38.32], "Manisa": [38.61, 27.42], "Mardin": [37.31, 40.73],
    "Mersin": [36.80, 34.61], "Muğla": [37.21, 28.36], "Muş": [38.73, 41.49],
    "Nevşehir": [38.62, 34.71], "Niğde": [37.96, 34.67], "Ordu": [40.98, 37.87],
    "Osmaniye": [37.07, 36.24], "Rize": [41.02, 40.52], "Sakarya": [40.77, 30.39],
    "Samsun": [41.28, 36.33], "Siirt": [37.93, 41.94], "Sinop": [42.02, 35.15],
    "Sivas": [39.74, 37.01], "Şanlıurfa": [37.15, 38.79], "Şırnak": [37.52, 42.45],
    "Tekirdağ": [40.97, 27.51], "Tokat": [40.31, 36.55], "Trabzon": [41.00, 39.72],
    "Tunceli": [39.10, 39.54], "Uşak": [38.67, 29.40], "Van": [38.50, 43.38],
    "Yalova": [40.65, 29.27], "Yozgat": [39.81, 34.80], "Zonguldak": [41.45, 31.79]
}

# --- Firebase bağlantısı -------------------------------------
@st.cache_resource
def get_db():
    """Firebase'e tek sefer bağlanır (Bulut ve Yerel uyumlu)."""
    if not firebase_admin._apps:
        if "firebase_json" in st.secrets:
            key_dict = json.loads(st.secrets["firebase_json"])
            cred = credentials.Certificate(key_dict)
        else:
            cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = get_db()

# --- Veri fonksiyonları (Firestore) --------------------------
def add_item(d):
    db.collection("items").add({**d, "date": date.today().isoformat(), "created": datetime.utcnow().isoformat()})

def add_need(d):
    db.collection("needs").add({**d, "date": date.today().isoformat(), "created": datetime.utcnow().isoformat()})

def get_items():
    rows = [{**doc.to_dict(), "id": doc.id} for doc in db.collection("items").stream()]
    rows.sort(key=lambda r: r.get("created", ""), reverse=True)
    return rows

def get_needs():
    rows = [{**doc.to_dict(), "id": doc.id} for doc in db.collection("needs").stream()]
    rows.sort(key=lambda r: r.get("created", ""), reverse=True)
    return rows

def whatsapp_url(phone):
    """Telefonu WhatsApp linkine çevirir."""
    d = "".join(ch for ch in str(phone) if ch.isdigit())
    if d.startswith("0"): d = "90" + d[1:]
    elif len(d) == 10: d = "90" + d
    return f"https://wa.me/{d}"

# ============================================================
#  SAYFA AYARI + TASARIM (CSS)
# ============================================================
st.set_page_config(page_title="Paylaş — Dayanışma Platformu", page_icon="🤝", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root{
  --green:#1A5D4E; --green-2:#2C8A6E; --coral:#E07A5F;
  --paper:#F6F3EC; --card:#FFFFFF; --ink:#241F1A; --muted:#857B6E; --line:#E7DFD2;
}
.stApp{ background:var(--paper); }
html,body,[class*="css"],.stApp,p,span,div,label,input,textarea,select{ font-family:'Plus Jakarta Sans',sans-serif; color:var(--ink); }
.block-container{ padding-top:1.2rem; max-width:1180px; }
#MainMenu, footer, header[data-testid="stHeader"]{ visibility:hidden; height:0; }

/* HERO */
.hero{ text-align:center; padding:8px 0 4px; }
.hero .logo{ font-family:'Fraunces',serif; font-weight:700; font-size:3.1rem; letter-spacing:-1px; color:var(--green); line-height:1; margin:0; }
.hero .logo .dot{ color:var(--coral); }
.hero .tag{ color:var(--muted); font-size:1.05rem; margin-top:6px; }

/* istatistik şeridi */
.stats{ display:flex; gap:14px; justify-content:center; margin:18px 0 6px; flex-wrap:wrap; }
.stat{ background:var(--card); border:1px solid var(--line); border-radius:16px; padding:14px 26px; text-align:center; min-width:150px; box-shadow:0 1px 2px rgba(36,31,26,.04); }
.stat .num{ font-family:'Fraunces',serif; font-size:1.9rem; font-weight:700; color:var(--green); line-height:1; }
.stat .lbl{ font-size:.82rem; color:var(--muted); margin-top:4px; text-transform:uppercase; letter-spacing:.5px; }

/* sütun başlıkları */
.colhead{ padding:12px 16px; border-radius:14px; margin:8px 0 16px; font-weight:700; font-size:1.15rem; color:#fff; text-align:center; }
.colhead.give{ background:linear-gradient(135deg,#1A5D4E,#2C8A6E); }
.colhead.need{ background:linear-gradient(135deg,#B85C38,#E07A5F); }

/* native kart */
div[data-testid="stVerticalBlockBorderWrapper"]{ border:1px solid var(--line)!important; border-radius:16px!important; background:var(--card); box-shadow:0 1px 2px rgba(36,31,26,.04); transition:.18s ease; }
div[data-testid="stVerticalBlockBorderWrapper"]:hover{ box-shadow:0 8px 22px rgba(36,31,26,.10); transform:translateY(-2px); }

/* kart içeriği */
.lhead{ display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:6px; }
.badge{ font-size:.72rem; font-weight:700; padding:4px 10px; border-radius:999px; letter-spacing:.3px; }
.donation-b{ background:#E4F1EC; color:#1A5D4E; }
.request-b{ background:#FBE9E2; color:#B85C38; }
.lloc{ font-size:.8rem; color:var(--muted); }
.ltitle{ font-family:'Fraunces',serif; font-size:1.2rem; font-weight:600; color:var(--ink); margin:2px 0 6px; }
.qty{ font-size:.72rem; background:#F0EBE0; color:var(--muted); padding:2px 8px; border-radius:8px; vertical-align:middle; }
.ldesc{ font-size:.9rem; color:var(--muted); line-height:1.45; margin-bottom:8px; }
.lperson{ font-size:.85rem; color:var(--ink); margin-bottom:8px; }
.empty{ text-align:center; color:var(--muted); padding:30px; border:1px dashed var(--line); border-radius:16px; background:var(--card); }

/* sekmeler ve form bileşenleri (Kısaltılmış CSS) */
.stTabs [data-baseweb="tab-list"]{ gap:8px; border-bottom:none; }
.stTabs [data-baseweb="tab"]{ background:#EFEADF; border-radius:12px; padding:10px 18px; font-weight:600; color:var(--muted); }
.stTabs [aria-selected="true"]{ background:var(--green)!important; color:#fff!important; }
.stTextInput input,.stTextArea textarea,.stNumberInput input, div[data-baseweb="select"]>div{ border-radius:10px!important; border:1.5px solid var(--line)!important; background:#fff!important; color:var(--ink)!important; }
.stFormSubmitButton button, .stButton button{ background:var(--green); color:#fff; border:none; border-radius:10px; padding:9px 22px; font-weight:700; }
div[data-testid="stPopover"] button{ background:var(--green)!important; color:#fff!important; border-radius:10px!important; }
[data-testid="stLinkButton"] a{ background:#25D366!important; color:#fff!important; border-radius:10px!important; }
div[data-baseweb="popover"] [data-testid="stPopoverBody"]{ background:#FFFFFF!important; border-radius:12px!important; }
[data-testid="stCode"]{ background:#F0EBE0!important; border-radius:10px!important; }
.sechead{ font-family:'Fraunces',serif; font-size:1.5rem; font-weight:600; color:var(--green); margin:4px 0 2px; }
a.contactbtn{ display:block; text-align:center; text-decoration:none; color:#fff!important; border-radius:10px; padding:10px 14px; font-weight:700; margin-top:6px; }
a.contactbtn.wa{ background:#25D366; }
a.contactbtn.mail{ background:#2C6BB0; }
</style>
""", unsafe_allow_html=True)

def sehir_ilce_sec(prefix):
    sehir_sel = st.selectbox("Şehir", PROVINCES + [MANUEL], key=f"{prefix}_city")
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
    ilce = st.text_input("İlçe (elle yaz)", key=f"{prefix}_dist_manual", placeholder="İlçe adı") if ilce_sel == MANUEL else ilce_sel
    return sehir, ilce

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
        person_label, person, q = "Bağışçı", d.get("donor", "Anonim"), ""
    else:
        person_label, person = "Talep eden", d.get("requester", "Anonim")
        q = f' <span class="qty">×{d.get("quantity", 1)}</span>'

    with st.container(border=True):
        st.markdown(
            f'<div class="lhead"><span class="badge {bcls}-b">{cat}</span><span class="lloc">📍 {loc}</span></div>'
            f'<div class="ltitle">{title}{q}</div><div class="ldesc">{desc}</div>'
            f'<div class="lperson">{person_label}: <b>{person}</b></div>', unsafe_allow_html=True)

        btn_label = "📞 İletişime Geç" if has_phone else ("✉️ İletişime Geç" if has_email else "İletişim")
        with st.popover(btn_label, use_container_width=True):
            if has_phone:
                st.markdown(f"**{person}** ile iletişim:")
                st.code(phone, language=None)
                st.markdown(f'<a class="contactbtn wa" href="{whatsapp_url(phone)}" target="_blank">💬 WhatsApp\'tan Yaz</a>', unsafe_allow_html=True)
            elif has_email:
                konu = quote(f"Paylaş ilanı: {title}")
                st.markdown(f"**{person}** ile iletişim:")
                st.code(email, language=None)
                st.markdown(f'<a class="contactbtn mail" href="mailto:{email}?subject={konu}">📧 E-posta Gönder</a>', unsafe_allow_html=True)
            else:
                st.caption("Bu ilanda iletişim bilgisi belirtilmemiş.")

# --- HERO + İSTATİSTİK ---------------------------------------
items_all = get_items()
needs_all = get_needs()
sehir_sayisi = len({*[i.get("city", "") for i in items_all], *[n.get("city", "") for n in needs_all]} - {""})

st.markdown('<div class="hero"><div class="logo">Payla<span class="dot">ş</span></div><div class="tag">İhtiyaç fazlasını, ihtiyaç sahibiyle buluşturan ücretsiz dayanışma platformu.</div></div>', unsafe_allow_html=True)

st.markdown(
    f'<div class="stats">'
    f'<div class="stat"><div class="num">{len(items_all)}</div><div class="lbl">Aktif Bağış</div></div>'
    f'<div class="stat"><div class="num">{len(needs_all)}</div><div class="lbl">Açık Talep</div></div>'
    f'<div class="stat"><div class="num">{sehir_sayisi}</div><div class="lbl">Şehir</div></div>'
    f'</div>', unsafe_allow_html=True)

st.write("")
tab_home, tab_items, tab_needs = st.tabs(["🏠  Canlı Akış", "🎁  Bağış Ekle", "📦  Talep Ekle"])

# --- Sekme 1: CANLI AKIŞ + İNTERAKTİF HARİTA -----------------
with tab_home:
    # 📍 HARİTA GÖRSELLEŞTİRME (Kümelenme Efekti İçin Rastgele Sapma Eklenmiştir)
    map_data = []
    
    # Yeşil noktalar (Bağışlar)
    for it in items_all:
        city = it.get("city")
        if city in COORDS:
            map_data.append({
                "lat": COORDS[city][0] + random.uniform(-0.04, 0.04), 
                "lon": COORDS[city][1] + random.uniform(-0.04, 0.04),
                "color": "#1A5D4E", # Koyu Yeşil
                "size": 4000
            })
            
    # Kırmızı noktalar (Talepler)
    for n in needs_all:
        city = n.get("city")
        if city in COORDS:
            map_data.append({
                "lat": COORDS[city][0] + random.uniform(-0.04, 0.04),
                "lon": COORDS[city][1] + random.uniform(-0.04, 0.04),
                "color": "#E07A5F", # Mercan / Kırmızı
                "size": 4000
            })
            
    if map_data:
        df_map = pd.DataFrame(map_data)
        
        # Haritayı küçültmek ve ortalamak için sayfayı 3 kolona bölüyoruz
        bos_sol, harita_kolonu, bos_sag = st.columns([1, 2, 1])
        
        with harita_kolonu:
            st.markdown("<p style='text-align:center; color:#857B6E; font-size:0.9rem; margin-bottom:5px;'>📍 Türkiye Geneli İlan Dağılımı</p>", unsafe_allow_html=True)
            # zoom=5 parametresi ile haritayı doğrudan Türkiye'ye sabitliyoruz
            st.map(df_map, latitude="lat", longitude="lon", color="color", size="size", zoom=5)
            
        st.write("---")

    # Arama / filtre çubuğu
    fc1, fc2, fc3 = st.columns([1, 1, 2])
    f_kat = fc1.selectbox("Kategori", ["Tüm Kategoriler"] + CATEGORIES, key="home_kat")
    f_sehir = fc2.selectbox("Şehir", ["Tüm Şehirler"] + PROVINCES, key="home_city")
    f_ara = fc3.text_input("İlanlarda ara", placeholder="ör. mont, kitap, battaniye...", key="home_search")

    def _uyar(d):
        if f_kat != "Tüm Kategoriler" and d.get("category") != f_kat: return False
        if f_sehir != "Tüm Şehirler" and d.get("city") != f_sehir: return False
        if f_ara and f_ara.lower() not in (d.get("title", "") + " " + d.get("description", "")).lower(): return False
        return True

    items_f = [it for it in items_all if _uyar(it)]
    needs_f = [n for n in needs_all if _uyar(n)]

    col_g, col_n = st.columns(2, gap="large")
    with col_g:
        st.markdown('<div class="colhead give">🟢 Bağışlanan Eşyalar</div>', unsafe_allow_html=True)
        if not items_f: st.markdown('<div class="empty">Uygun bağış bulunamadı.</div>', unsafe_allow_html=True)
        for it in items_f: render_card(it, "donation")
    with col_n:
        st.markdown('<div class="colhead need">🔴 İhtiyaç Talepleri</div>', unsafe_allow_html=True)
        if not needs_f: st.markdown('<div class="empty">Uygun talep bulunamadı.</div>', unsafe_allow_html=True)
        for n in needs_f: render_card(n, "request")

# --- Sekme 2: BAĞIŞ EKLE -------------------------------------
with tab_items:
    st.markdown('<div class="sechead">Eşya Paylaş</div>', unsafe_allow_html=True)
    st.caption("İhtiyaç fazlası eşyanı paylaş, ihtiyaç sahibine ulaşsın.")
    if st.session_state.pop("i_done", False):
        for _k in ["i_title", "i_bagisci", "i_phone", "i_email", "i_desc", "i_city", "i_city_manual", "i_dist", "i_dist_manual", "i_lastcity"]:
            st.session_state.pop(_k, None)
        st.success("Bağış ilanın başarıyla yayınlandı! 🎉")

    c1, c2 = st.columns(2)
    title = c1.text_input("Eşya Başlığı", key="i_title", placeholder="ör. Kışlık çocuk montu")
    kategori = c2.selectbox("Kategori", CATEGORIES, key="i_kat")
    durum = c1.selectbox("Eşyanın Durumu", ["Yeni Gibi", "Çok İyi", "İyi", "Orta"], key="i_durum")
    bagisci = c2.text_input("İsim Soyisim", key="i_bagisci", placeholder="ör. Elif K.")
    sehir, ilce = sehir_ilce_sec("i")
    yontem_i = st.selectbox("İletişim", ["📞 Telefon", "✉️ E-posta"], key="i_yontem")
    phone = st.text_input("Telefon numaranız", key="i_phone", placeholder="ör. 05551234567") if yontem_i.startswith("📞") else ""
    email = "" if yontem_i.startswith("📞") else st.text_input("E-posta adresiniz", key="i_email", placeholder="ör. ornek@mail.com")
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

# --- Sekme 3: TALEP EKLE -------------------------------------
with tab_needs:
    st.markdown('<div class="sechead">İhtiyaç Talebi Oluştur</div>', unsafe_allow_html=True)
    st.caption("İhtiyacını paylaş, bağışçılar sana ulaşsın.")
    if st.session_state.pop("n_done", False):
        for _k in ["n_title", "n_eden", "n_phone", "n_email", "n_desc", "n_adet", "n_city", "n_city_manual", "n_dist", "n_dist_manual", "n_lastcity"]:
            st.session_state.pop(_k, None)
        st.success("Talebin başarıyla yayınlandı! 🎉")

    c1, c2 = st.columns(2)
    title = c1.text_input("İhtiyaç Başlığı", key="n_title", placeholder="ör. Üniversite hazırlık kitapları")
    kategori = c2.selectbox("Kategori", CATEGORIES, key="n_kat")
    adet = c1.number_input("Gerekli Adet", min_value=1, value=1, step=1, key="n_adet")
    eden = c2.text_input("İsim Soyisim", key="n_eden", placeholder="ör. Ayşe Y.")
    sehir, ilce = sehir_ilce_sec("n")
    yontem_n = st.selectbox("İletişim", ["📞 Telefon", "✉️ E-posta"], key="n_yontem")
    phone = st.text_input("Telefon numaranız", key="n_phone", placeholder="ör. 05321234567") if yontem_n.startswith("📞") else ""
    email = "" if yontem_n.startswith("📞") else st.text_input("E-posta adresiniz", key="n_email", placeholder="ör. ornek@mail.com")
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
