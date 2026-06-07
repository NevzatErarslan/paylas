# ============================================================
#  PAYLAŞ — Dayanışma & Bağış Eşleştirme Uygulaması
#  Firebase (Firestore) sürümü — veri bulutta, herkes ortak görür
# ============================================================
#  GEREKLİ:
#    pip install streamlit firebase-admin
#  Firebase kurulumu ve secrets ayarı için yanındaki rehbere bak.
# ============================================================

from datetime import date, datetime
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# --- Sabitler -------------------------------------------------
CATEGORIES = {
    "Giyim": ["Mont", "Ayakkabı", "Tişört", "Pantolon", "Bebek Giyim"],
    "Mobilya": ["Masa", "Sandalye", "Dolap", "Yatak"],
    "Elektronik": ["Telefon", "Laptop", "Buzdolabı", "Isıtıcı"],
    "Kırtasiye": ["Kitap", "Defter", "Çanta"],
    "Ev Eşyası": ["Battaniye", "Tencere", "Halı"],
}
CITIES = ["Ankara", "İstanbul", "İzmir", "Bursa", "Antalya"]
URGENCY = {"Düşük": 1, "Orta": 2, "Yüksek": 3, "Acil": 4}


# --- Firebase bağlantısı -------------------------------------
@st.cache_resource
def get_db():
    """Firebase'e tek sefer bağlanır (secrets içindeki bilgilerle)."""
    if not firebase_admin._apps:
        info = dict(st.secrets["firebase"])
        # private_key bazen tek satıra sıkışır; satır sonlarını düzelt
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(info)
        firebase_admin.initialize_app(cred)
    return firestore.client()


db = get_db()


# --- Veri fonksiyonları (Firestore) --------------------------
def add_item(d):
    db.collection("items").add({
        **d,
        "date": date.today().isoformat(),
        "created": datetime.utcnow().isoformat(),
    })


def add_need(d):
    db.collection("needs").add({
        **d,
        "date": date.today().isoformat(),
        "created": datetime.utcnow().isoformat(),
    })


def get_items():
    rows = [{**doc.to_dict(), "id": doc.id} for doc in db.collection("items").stream()]
    rows.sort(key=lambda r: r.get("created", ""), reverse=True)
    return rows


def get_needs():
    rows = [{**doc.to_dict(), "id": doc.id} for doc in db.collection("needs").stream()]
    rows.sort(key=lambda r: r.get("created", ""), reverse=True)
    return rows


# --- EŞLEŞTİRME ALGORİTMASI (projenin kalbi) -----------------
def score_match(need, item):
    """Bir talep ile bir eşya arasında 0-100 uygunluk puanı + gerekçe üretir."""
    W = {"category": 40, "location": 30, "urgency": 20, "wait": 10}  # ağırlıklar
    reasons = []

    # 1) Kategori uyumu
    if need["category"] == item["category"] and need["sub"] == item["sub"]:
        cat = 1.0
        reasons.append("✓ Tam kategori eşleşmesi")
    elif need["category"] == item["category"]:
        cat = 0.6
        reasons.append("✓ Aynı kategori, farklı alt tür")
    else:
        cat = 0.0
        reasons.append("• Kategori uyuşmuyor")

    # 2) Konum yakınlığı
    if need["city"] == item["city"] and need["district"] == item["district"]:
        loc = 1.0
        reasons.append("✓ Aynı ilçe")
    elif need["city"] == item["city"]:
        loc = 0.7
        reasons.append("✓ Aynı şehir")
    else:
        loc = 0.2
        reasons.append("• Farklı şehir (kargo gerek)")

    # 3) Aciliyet (talebin önceliği)
    urg = URGENCY.get(need["urgency"], 1) / 4
    if URGENCY.get(need["urgency"], 1) >= 3:
        reasons.append(f"✓ Yüksek öncelik: {need['urgency']}")

    # 4) Bekleme süresi (eski talep yukarı çıkar)
    days = (date.today() - date.fromisoformat(need["date"])).days
    wait = min(days / 14, 1.0)  # 14 günde tavan
    if days >= 5:
        reasons.append(f"✓ {days} gündür bekliyor")

    score = cat * W["category"] + loc * W["location"] + urg * W["urgency"] + wait * W["wait"]
    return round(score), reasons


# ============================================================
#  ARAYÜZ
# ============================================================
st.set_page_config(page_title="Paylaş", page_icon="🤝", layout="centered")

st.title("🤝 Paylaş")
st.caption("İhtiyaç fazlasını, ihtiyaç sahibiyle buluşturan ücretsiz dayanışma platformu.")

tab_match, tab_items, tab_needs = st.tabs(["✨ Eşleştirme", "🎁 Bağışlar", "📦 Talepler"])

# --- Sekme 1: EŞLEŞTİRME -------------------------------------
with tab_match:
    needs = get_needs()
    items = get_items()
    if not needs:
        st.info("Henüz talep yok. Önce 'Talepler' sekmesinden bir talep ekle.")
    else:
        labels = [f"{n['title']} ({n['sub']} · {n['city']} · {n['urgency']})" for n in needs]
        idx = st.selectbox("Bir talep seç:", range(len(needs)), format_func=lambda i: labels[i])
        secili = needs[idx]
        st.write("Bu talebe en uygun eşyalar (puana göre sıralı):")

        if not items:
            st.info("Henüz bağış yok. 'Bağışlar' sekmesinden eşya ekle.")
        else:
            eslesmeler = sorted(
                [(it, *score_match(secili, it)) for it in items],
                key=lambda x: x[1], reverse=True
            )
            for it, puan, gerekceler in eslesmeler:
                with st.container(border=True):
                    c1, c2 = st.columns([1, 4])
                    c1.metric("Uygunluk", puan)
                    c2.markdown(f"**{it['title']}**  \n{it['sub']} · {it['condition']} · {it['district']}, {it['city']}")
                    c2.caption("  ".join(gerekceler))

# --- Sekme 2: BAĞIŞLAR ---------------------------------------
with tab_items:
    st.subheader("Eşya yükle")
    with st.form("item_form", clear_on_submit=True):
        title = st.text_input("Başlık", placeholder="ör. Kışlık çocuk montu")
        kategori = st.selectbox("Kategori", list(CATEGORIES.keys()))
        alt = st.selectbox("Alt tür", CATEGORIES[kategori])
        durum = st.selectbox("Durum", ["Yeni Gibi", "Çok İyi", "İyi", "Orta"])
        sehir = st.selectbox("Şehir", CITIES)
        ilce = st.text_input("İlçe", placeholder="ör. Çankaya")
        bagisci = st.text_input("Bağışçı adı", placeholder="ör. Elif K.")
        if st.form_submit_button("Bağışı yayınla") and title:
            add_item({"title": title, "category": kategori, "sub": alt,
                      "condition": durum, "city": sehir,
                      "district": ilce or "—", "donor": bagisci or "Anonim"})
            st.success("Bağış eklendi!")
            st.rerun()

    st.subheader("Yüklenen bağışlar")
    for it in get_items():
        with st.container(border=True):
            st.markdown(f"**{it['title']}** — {it['category']} / {it['sub']} · durum: {it['condition']}")
            st.caption(f"📍 {it['district']}, {it['city']}  ·  Bağışçı: {it['donor']}")

# --- Sekme 3: TALEPLER ---------------------------------------
with tab_needs:
    st.subheader("Talep oluştur")
    with st.form("need_form", clear_on_submit=True):
        title = st.text_input("Başlık", placeholder="ör. Çocuğum için mont")
        kategori = st.selectbox("Kategori", list(CATEGORIES.keys()), key="nk")
        alt = st.selectbox("Alt tür", CATEGORIES[kategori], key="ns")
        aciliyet = st.selectbox("Aciliyet", list(URGENCY.keys()))
        hane = st.number_input("Hane (kişi)", min_value=1, value=1)
        sehir = st.selectbox("Şehir", CITIES, key="nc")
        ilce = st.text_input("İlçe", placeholder="ör. Mamak", key="nd")
        eden = st.text_input("Talep eden adı", placeholder="ör. Ayşe Y.")
        if st.form_submit_button("Talebi gönder") and title:
            add_need({"title": title, "category": kategori, "sub": alt,
                      "urgency": aciliyet, "household": int(hane), "city": sehir,
                      "district": ilce or "—", "requester": eden or "Anonim"})
            st.success("Talep eklendi!")
            st.rerun()

    st.subheader("İhtiyaç talepleri")
    for n in get_needs():
        with st.container(border=True):
            st.markdown(f"**{n['title']}** — {n['category']} / {n['sub']} · hane: {n['household']} kişi")
            st.caption(f"📍 {n['district']}, {n['city']}  ·  Aciliyet: {n['urgency']}  ·  Talep eden: {n['requester']}")
