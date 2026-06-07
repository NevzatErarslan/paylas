# ============================================================
#  PAYLAŞ — Dayanışma & Bağış Platformu
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


# ============================================================
#  ARAYÜZ VE GÖRSEL TASARIM (CSS Geliştirmeleri Yapıldı)
# ============================================================
st.set_page_config(page_title="Paylaş", page_icon="🤝", layout="wide")

# Uygulamanın modern görünmesi için özel CSS enjeksiyonu
st.markdown("""
    <style>
    /* Genel Arka Plan ve Kart Güzelleştirmeleri */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        background-color: #F3F4F6;
        border-radius: 8px 8px 0px 0px;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #4F46E5 !important; 
        color: white !important;
    }
    
    /* Detay Kutusu Özelleştirmeleri */
    .detail-box {
        padding: 12px;
        border-left: 4px solid #4F46E5;
        background-color: #F9FAFB;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #4F46E5; margin-bottom: 0px;'>🤝 PAYLAŞ</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6B7280; font-size: 1.1rem;'>İhtiyaç fazlasını, ihtiyaç sahibiyle buluşturan ücretsiz dayanışma platformu.</p>", unsafe_allow_html=True)
st.markdown("---")

tab_home, tab_items, tab_needs = st.tabs(["🏠 Ana Sayfa (Canlı Akış)", "🎁 Bağış Havuzu", "📦 Talep Havuzu"])

# --- Sekme 1: YENİ ANA SAYFA (Büyük Yan Yana Liste) ------------
with tab_home:
    st.markdown("<p style='text-align: center; color: #9CA3AF;'>Sistemdeki tüm aktif ilanların anlık akışı. Detaylar ve iletişim için ilanlara tıklayın.</p>", unsafe_allow_html=True)
    
    # Sayfayı iki büyük kolona bölüyoruz: Bağışlar (Yeşil) - Talepler (Kırmızı)
    col_bagis, col_talep = st.columns(2)
    
    # SOL TARAF: BAĞIŞLAR (YEŞİL)
    with col_bagis:
        st.markdown("<div style='background-color: #10B981; padding: 12px; border-radius: 8px; margin-bottom: 15px;'><h2 style='color: white; text-align: center; margin: 0;'>🟢 BAĞIŞLAR</h2></div>", unsafe_allow_html=True)
        
        items = get_items()
        if not items:
            st.info("Henüz bağışlanan bir eşya yok.")
        else:
            for it in items:
                telefon_no = it.get("phone", "Belirtilmemiş")
                ek_aciklama = it.get("description", "Açıklama belirtilmemiş.")
                
                # Tıklanabilir Bağış Kartı
                with st.expander(f"🎁 {it['title']} ({it['district']}, {it['city']})"):
                    st.markdown(f"<div class='detail-box'><b>Kategori:</b> {it['category']}<br><b>Eşya Durumu:</b> {it['condition']}<br><b>Bağışçı:</b> {it['donor']}</div>", unsafe_allow_html=True)
                    st.write(f"📝 **Ek Bilgi:** {ek_aciklama}")
                    st.success(f"📞 **Bağışçı Telefonu:** [{telefon_no}](tel:{telefon_no})")

    # SAĞ TARAF: TALEPLER (KIRMIZI)
    with col_talep:
        st.markdown("<div style='background-color: #EF4444; padding: 12px; border-radius: 8px; margin-bottom: 15px;'><h2 style='color: white; text-align: center; margin: 0;'>🔴 TALEPLER</h2></div>", unsafe_allow_html=True)
        
        needs = get_needs()
        if not needs:
            st.info("Henüz oluşturulmuş bir ihtiyaç talebi yok.")
        else:
            for n in needs:
                t_telefon = n.get("phone", "Belirtilmemiş")
                t_aciklama = n.get("description", "Açıklama belirtilmemiş.")
                t_adet = n.get("quantity", 1)
                
                # Tıklanabilir Talep Kartı
                with st.expander(f"📦 {n['title']} — Adet: {t_adet} ({n['district']}, {n['city']})"):
                    st.markdown(f"<div class='detail-box'><b>Kategori:</b> {n['category']}<br><b>Talep Eden:</b> {n['requester']}</div>", unsafe_allow_html=True)
                    st.write(f"📝 **İhtiyaç Gerekçesi:** {t_aciklama}")
                    st.error(f"📞 **İhtiyaç Sahibi Telefonu:** [{t_telefon}](tel:{t_telefon})")

# --- Sekme 2: BAĞIŞ HAVUZU (Ekleme ve Filtreleme) --------------
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

# --- Sekme 3: TALEP HAVUZU (Ekleme ve Filtreleme) --------------
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
