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

# --- Sabitler -------------------------------------------------
CATEGORIES = ["Giyim", "Mobilya", "Elektronik", "Eğitim / Kırtasiye", "Ev Eşyası", "Çocuk / Oyuncak"]
CITIES = ["Ankara", "İstanbul", "İzmir", "Bursa", "Antalya"]

# --- Firebase bağlantısı -------------------------------------
@st.cache_resource
def get_db():
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = get_db()

# --- Veri fonksiyonları --------------------------------------
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

# --- EŞLEŞTİRME ALGORİTMASI ----------------------------------
def score_match(need, item):
    W = {"category": 50, "location": 40, "wait": 10}  
    reasons = []

    if need["category"] == item["category"]:
        cat = 1.0
        reasons.append("✓ Kategori eşleşmesi")
    else:
        cat = 0.0
        reasons.append("• Kategori uyuşmuyor")

    if need["city"] == item["city"] and need["district"] == item["district"]:
        loc = 1.0
        reasons.append("✓ Aynı ilçe (Elden teslim)")
    elif need["city"] == item["city"]:
        loc = 0.7
        reasons.append("✓ Aynı şehir")
    else:
        loc = 0.2
        reasons.append("• Farklı şehir (Kargo gerekli)")

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

tab_match, tab_items, tab_needs = st.tabs(["⚡ Akıllı Eşleştirme Asistanı", "🎁 Bağış Havuzu", "📦 Talep Havuzu"])

# --- Sekme 1: YENİDEN TASARLANAN EŞLEŞTİRME MOTORU -------------
with tab_match:
    st.info("💡 **Sistem Analiz Paneli:** Bu ekran, arka planda çalışan eşleştirme algoritmasını test etmek için tasarlanmıştır. Sistem; seçilen talebi analiz eder, bağış havuzunu tarar ve lojistik/kategori uyumuna göre bir skorlama çıkararak en doğru eşleşmeleri önerir.")
    
    needs = get_needs()
    items = get_items()
    
    if not needs:
        st.warning("Eşleştirme yapabilmek için önce 'Talep Havuzu'ndan bir ihtiyaç eklemelisiniz.")
    elif not items:
        st.warning("Eşleştirme yapabilmek için önce 'Bağış Havuzu'na eşya eklemelisiniz.")
    else:
        st.write("---")
        labels = [f"{n['title']} (Şehir: {n['city']})" for n in needs]
        idx = st.selectbox("🎯 Algoritmanın analiz edeceği İhtiyaç Talebini seçin:", range(len(needs)), format_func=lambda i: labels[i])
        secili = needs[idx]
        
        # Seçilen Talebin Şık Metrik Kartları
        st.markdown("#### 📌 İncelenen Talebin Parametreleri")
        bekleme_suresi = (date.today() - date.fromisoformat(secili['date'])).days
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Aranan Kategori", secili['category'])
        col2.metric("Talep Konumu", f"{secili.get('district', '')}, {secili['city']}")
        col3.metric("Bekleme Süresi", f"{bekleme_suresi} Gün")
        
        st.write("---")
        st.markdown("#### 🔍 Algoritma Önerileri (En Yüksek Skordan Düşüğe)")

        eslesmeler = sorted(
            [(it, *score_match(secili, it)) for it in items],
            key=lambda x: x[1], reverse=True
        )
        
        # Eşleşmeleri görsel çubuklar ve skorlarla listeleme
        for it, puan, gerekceler in eslesmeler:
            with st.container(border=True):
                # Ekranı ikiye bölüyoruz (Sol: Skor, Sağ: Detaylar)
                score_col, detail_col = st.columns([1, 3])
                
                with score_col:
                    # Puana göre renk belirleme (Yeşil, Sarı, Kırmızı)
                    renk = "#10B981" if puan >= 70 else "#F59E0B" if puan >= 40 else "#EF4444"
                    st.markdown(f"<h2 style='text-align: center; color: {renk}; margin-bottom: 0px;'>%{puan}</h2>", unsafe_allow_html=True)
                    st.progress(puan / 100)
                
                with detail_col:
                    st.markdown(f"**🎁 İlan:** {it['title']}")
                    st.caption(f"**Kategori:** {it['category']} | **Konum:** {it['district']}, {it['city']} | **Durum:** {it['condition']}")
                    
                    # Gerekçeleri daha okunaklı formatta yazma
                    st.markdown(f"*{'  •  '.join(gerekceler)}*")
                    
                    telefon_no = it.get("phone", "Belirtilmemiş")
                    st.markdown(f"📞 [Bağışçıyla İletişime Geç ({it['donor']})](tel:{telefon_no})")

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
    
    filtre_kat = st.selectbox("🔍 Kategoriye Göre Filtrele (Bağışlar):", ["Hepsi"] + CATEGORIES, key="filter_items")
    arama_kelimesi_kat = st.text_input("📝 Kelime ile Ara (Bağış İlanlarında):", placeholder="ör. bot, koltuk, kitap...", key="search_items_text")
    
    tum_bagislar = get_items()
    for it in tum_bagislar:
        if filtre_kat != "Hepsi" and it["category"] != filtre_kat:
            continue
            
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
    
    filtre_talep = st.selectbox("🔍 Kategoriye Göre Filtrele (Talepler):", ["Hepsi"] + CATEGORIES, key="filter_needs")
    arama_kelimesi_talep = st.text_input("📝 Kelime ile Ara (Talep İlanlarında):", placeholder="ör. tablet, battaniye, çanta...", key="search_needs_text")
    
    tum_talepler = get_needs()
    for n in tum_talepler:
        if filtre_talep != "Hepsi" and n["category"] != filtre_talep:
            continue
            
        if arama_kelimesi_talep:
            talep_metni = (n["title"] + " " + n.get("description", "")).lower()
            if arama_kelimesi_talep.lower() not in talep_metni:
                continue
                
        t_telefon = n.get("phone", "Belirtilmemiş")
        t_aciklama = n.get("description", "Açıklama belirtilmemiş.")
        t_adet = n.get("quantity", 1)
        
        with st.expander(f"📦 {n['title']} — Adet: {t_adet} ({n['district']}, {n['city']})"):
            st.markdown(f"**Kategori:** {n['category']}")
            st.markdown(f"**Talep Eden:** {n['requester']}")
            st.info(f"**Talep Detayı / Gerekçe:** {t_aciklama}")
            st.success(f"📞 **İhtiyaç Sahibine Ulaş:** [{t_telefon}](tel:{t_telefon})")
