# ============================================================
#  PAYLAŞ — Dayanışma & Bağış Eşleştirme Uygulaması
#  Firebase (Firestore) sürümü — veri bulutta, herkes ortak görür
# ============================================================
#  GEREKLİ:
#    pip install streamlit firebase-admin
# ============================================================

from datetime import date, datetime
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# --- Sabitler (Alt kategoriler kaldırılarak sadeleştirildi) -------
CATEGORIES = ["Giyim", "Mobilya", "Elektronik", "Eğitim / Kırtasiye", "Ev Eşyası", "Çocuk / Oyuncak"]
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


# --- EŞLEŞTİRME ALGORİTMASI (Kategori eşleşmesi sadeleştirildi) -
def score_match(need, item):
    """Bir talep ile bir eşya arasında 0-100 uygunluk puanı + gerekçe üretir."""
    W = {"category": 50, "location": 40, "wait": 10}  
    reasons = []

    # 1) Kategori uyumu (%50) - Doğrudan ana kategori kontrol edilir
    if need["category"] == item["category"]:
        cat = 1.0
        reasons.append("✓ Kategori eşleşmesi")
    else:
        cat = 0.0
        reasons.append("• Kategori uyuşmuyor")

    # 2) Konum yakınlığı (%40)
    if need["city"] == item["city"] and need["district"] == item["district"]:
        loc = 1.0
        reasons.append("✓ Aynı ilçe (Elden teslim edilebilir)")
    elif need["city"] == item["city"]:
        loc = 0.7
        reasons.append("✓ Aynı şehir")
    else:
        loc = 0.2
        reasons.append("• Farklı şehir (Kargo gerekli)")

    # 3) Bekleme süresi (%10)
    days = (date.today() - date.fromisoformat(need["date"])).days
    wait = min(days / 14, 1.0)
    if days >= 5:
        reasons.append(f"✓ {days} gündür bekleyen öncelikli talep")

    score = cat * W["category"] + loc * W["location"] + wait * W["wait"]
    return round(score), reasons


# ============================================================
#  ARAYÜZ
# ============================================================
st.set_page_config(page_title="Paylaş", page_icon="🤝", layout="centered")

st.title("🤝 Paylaş")
st.caption("İhtiyaç fazlasını, ihtiyaç sahibiyle buluşturan ücretsiz dayanışma platformu.")

tab_match, tab_items, tab_needs = st.tabs(["✨ Eşleştirme Motoru", "🎁 Bağış Havuzu", "📦 Talep Havuzu"])

# --- Sekme 1: EŞLEŞTİRME MOTORU ----------------               ---
with tab_match:
    needs = get_needs()
    items = get_items()
    if not needs:
        st.info("Henüz sistemde aktif talep yok. Önce 'Talep Havuzu' sekmesinden bir talep ekleyin.")
    else:
        labels = [f"{n['title']} ({n['city']} · Adet: {n.get('quantity', 1)})" for n in needs]
        idx = st.selectbox("Eşleştirme yapılacak talebi seçin:", range(len(needs)), format_func=lambda i: labels[i])
        secili = needs[idx]
        
        st.write("---")
        st.markdown(f"### Seçilen İhtiyaç: **{secili['title']}**")
        st.markdown(f"👤 **Talep Eden:** {secili['requester']} | 📞 **İletişim:** [{secili.get('phone', '---')}](tel:{secili.get('phone', '')})")
        st.caption(f"📝 **Talep Açıklaması:** {secili.get('description', 'Açıklama belirtilmemiş.')}")
        st.write("---")
        
        st.subheader("Bu Talebe En Uygun Bağış İlanları (Önerilenler):")

        if not items:
            st.info("Henüz bağış yok. 'Bağış Havuzu' sekmesinden eşya ekle.")
        else:
            eslesmeler = sorted(
                [(it, *score_match(secili, it)) for it in items],
                key=lambda x: x[1], reverse=True
            )
            
            for it, puan, gerekceler in eslesmeler:
                telefon_no = it.get("phone", "Belirtilmemiş")
                ek_aciklama = it.get("description", "Açıklama belirtilmemiş.")
                
                kart_basligi = f"🎯 Uygunluk Skoru: %{puan} — {it['title']} ({it['district']}, {it['city']})"
                
                with st.expander(kart_basligi):
                    st.markdown(f"**Kategori:** {it['category']}  |  **Eşya Durumu:** {it['condition']}")
                    st.markdown(f"**Bağışçı:** {it['donor']}")
                    st.info(f"**Bağışçı Açıklaması:** {ek_aciklama}")
                    st.success(f"📞 **Bağışçıya Ulaş:** [{telefon_no}](tel:{telefon_no})")
                    st.caption("  |  ".join(gerekceler))

# --- Sekme 2: BAĞIŞ HAVUZU -------------------------------------
with tab_items:
    st.subheader("Eşya Paylaş")
    with st.form("item_form", clear_on_submit=True):
        title = st.text_input("Eşya Başlığı", placeholder="ör. Kışlık çocuk montu")
        kategori = st.selectbox("Kategori", CATEGORIES)
        durum = st.selectbox("Eşyanın Durumu", ["Yeni Gibi", "Çok İyi", "İyi", "Orta"])
        sehir = st.selectbox("Bulunduğu Şehir", CITIES)
        ilce = st.text_input("İlçe", placeholder="ör. Çankaya")
        bagisci = st.text_input("İsim Soyisim / Adınız", placeholder="ör. Elif K.")
        phone = st.text_input("İletişim Telefon Numarası", placeholder="ör. 05551234567")
        description = st.text_area("Eşya Hakkında Ek Bilgiler / Açıklama", placeholder="ör. Herhangi bir yırtığı yoktur, temiz durumdadır.")
        
        if st.form_submit_button("Bağış İlanı Yayınla") and title and phone:
            add_item({"title": title, "category": kategori, "condition": durum, "city": sehir, 
                      "district": ilce or "—", "donor": bagisci or "Anonim", "phone": phone, 
                      "description": description or "Açıklama yok."})
            st.success("Bağış ilanınız başarıyla sisteme yüklendi!")
            st.rerun()
        elif title and not phone:
            st.error("Lütfen iletişim için telefon numaranızı giriniz.")

    st.write("---")
    st.subheader("Yüklenen Bağış İlanları")
    
    # Kategori Filtresi + Metin Arama Kutusu (Bağışlar)
    filtre_kat = st.selectbox("🔍 Kategoriye Göre Filtrele (Bağışlar):", ["Hepsi"] + CATEGORIES, key="filter_items")
    arama_kelimesi_kat = st.text_input("📝 Kelime ile Ara (Bağış İlanlarında):", placeholder="ör. bot, koltuk, kitap...", key="search_items_text")
    
    tum_bagislar = get_items()
    for it in tum_bagislar:
        # Kategoriye göre filtreleme
        if filtre_kat != "Hepsi" and it["category"] != filtre_kat:
            continue
            
        # Kelimeye göre filtreleme (Başlık veya açıklamada geçiyor mu kontrolü)
        if arama_kelimesi_kat:
            ilan_metni = (it["title"] + " " + it.get("description", "")).lower()
            if arama_kelimesi_kat.lower() not in ilan_metni:
                continue
                
        telefon_no = it.get("phone", "Belirtilmemiş")
        ek_aciklama = it.get("description", "Açıklama belirtilmemiş.")
        
        with st.expander(f"🎁 {it['title']} — {it['district']}, {it['city']}"):
            st.markdown(f"**Kategori:** {it['category']} | **Durum:** {it['condition']}")
            st.markdown(f"**Bağışçı:** {it['donor']}")
            st.info(f"**Ek Ürün Bilgisi:** {ek_aciklama}")
            st.success(f"📞 **İletişim Numarası:** [{telefon_no}](tel:{telefon_no})")

# --- Sekme 3: TALEP HAVUZU -------------------------------------
with tab_needs:
    st.subheader("İhtiyaç Talebi Oluştur")
    with st.form("need_form", clear_on_submit=True):
        title = st.text_input("İhtiyaç Başlığı", placeholder="ör. Üniversite hazırlık kitapları")
        kategori = st.selectbox("Kategori", CATEGORIES, key="nk")
        adet = st.number_input("Gerekli Adet / Miktar", min_value=1, value=1, step=1)
        sehir = st.selectbox("Yaşadığınız Şehir", CITIES, key="nc")
        ilce = st.text_input("İlçe", placeholder="ör. Mamak", key="nd")
        eden = st.text_input("İsim Soyisim / Adınız", placeholder="ör. Ayşe Y.")
        phone = st.text_input("İletişim Telefon Numarası", placeholder="ör. 05321234567", key="n_phone")
        description = st.text_area("İhtiyaç Durumu Hakkında Ek Açıklama", placeholder="ör. Öğrenci yurdunda kalıyorum, eğitim setine ihtiyacım var.", key="n_desc")
        
        if st.form_submit_button("Talebi Gönder ve Yayınla") and title and phone:
            add_need({"title": title, "category": kategori, "quantity": int(adet), "city": sehir, 
                      "district": ilce or "—", "requester": eden or "Anonim", "phone": phone, 
                      "description": description or "Açıklama yok."})
            st.success("İhtiyaç talebiniz başarıyla sisteme yüklendi!")
            st.rerun()
        elif title and not phone:
            st.error("Lütfen iletişim sağlanabilmesi için telefon numaranızı giriniz.")

    st.write("---")
    st.subheader("Güncel İhtiyaç Talepleri")
    
    # Kategori Filtresi + Metin Arama Kutusu (Talepler)
    filtre_talep = st.selectbox("🔍 Kategoriye Göre Filtrele (Talepler):", ["Hepsi"] + CATEGORIES, key="filter_needs")
    arama_kelimesi_talep = st.text_input
