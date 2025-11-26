import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import base64
import os
import json
import datetime
import random
import hashlib

PATIENTS_FILE = "patients.json"
USERS_FILE = "users.json"
SESSION_FILE = "session.json"

# --- 1. AYARLAR ---
st.set_page_config(
    page_title="ICFevalu8", 
    layout="wide", 
    initial_sidebar_state="collapsed", 
    page_icon="logo.png"
)

# --- CSS (SADECE TASARIM MAKYAJI - INPUTLARA DOKUNMUYORUZ) ---
st.markdown("""
    <style>
        /* HASTA KARTI GÖRÜNÜMÜ */
        html, body, .stApp {
            background: #0d1b2a;
            color: #e5e7eb;
        }
        div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
            border: 1px solid rgba(0,0,0, 0.05);
            border-radius: 8px;
            padding: 15px;
            background-color: white;
        }
        
        /* HEADER DÜZENİ */
        .header-container {
            display: flex;
            align-items: center;
            gap: 15px;
            padding-bottom: 10px;
        }
        .clinic-title { font-size: 22px; font-weight: 800; color: #333; margin: 0; }
        .user-greeting { font-size: 14px; color: #0056b3; margin: 0; font-weight: 600; }

        /* BUTONLAR (YEŞİL TEMA) */
        div.stButton > button:first-child {
            background-color: #28a745;
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
        }
        div.stButton > button:first-child:hover {
            background-color: #218838;
            color: white;
        }
        /* FORM VE PRIMARY BUTONLAR */
        button[kind="primary"], button[data-testid="baseButton-primary"] {
            background-color: #28a745 !important;
            color: white !important;
            border: 1px solid #218838 !important;
            border-radius: 6px !important;
            font-weight: 700 !important;
        }
        button[kind="primary"]:hover, button[data-testid="baseButton-primary"]:hover {
            background-color: #218838 !important;
            color: white !important;
        }
        
        /* İKİNCİL BUTONLAR (GRİ) */
        button[kind="secondary"] {
            background-color: #f8f9fa !important;
            color: #333 !important;
            border: 1px solid #ccc !important;
        }

        /* HASTA HEADER KARTI */
        .patient-card {
            display: flex;
            align-items: center;
            gap: 16px;
            background: linear-gradient(135deg, #1f2937 0%, #111827 60%, #0b1220 100%);
            border: 1px solid #111827;
            border-radius: 14px;
            padding: 14px 16px;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.28);
        }
        .photo-frame {
            width: 96px; height: 96px;
            border-radius: 16px;
            background: #0f172a;
            border: 1px solid #1f2937;
            display: flex; align-items: center; justify-content: center;
            color: #e2e8f0; font-weight: 800; letter-spacing: 1px;
            background-size: cover; background-position: center;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
        }
        .photo-frame.placeholder { background-image: linear-gradient(135deg, #111827, #0f172a); }
        .patient-meta { display: flex; flex-direction: column; gap: 6px; }
        .patient-name { font-size: 20px; font-weight: 800; color: #f8fafc; margin: 0; }
        .patient-id { font-size: 11px; letter-spacing: 0.6px; color: #cbd5e1; text-transform: uppercase; }
        .badge-row { display: flex; flex-wrap: wrap; gap: 8px; }
        .badge {
            background: #0b1220;
            color: #e5e7eb;
            padding: 6px 10px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 700;
            border: 1px solid #1f2937;
        }
        .badge.gray { background: #0f172a; color: #e5e7eb; border-color: #1f2937; }
        .diag-box {
            font-size: 12px; color: #e2e8f0;
            border: 1px dashed #334155;
            background: #0f172a;
            padding: 10px;
            border-radius: 10px;
        }
        .meta-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; }
        .meta-chip {
            display: flex; align-items: center; justify-content: space-between;
            background: linear-gradient(135deg, #111827, #0b1220);
            border: 1px solid #1f2937;
            border-radius: 10px;
            padding: 8px 10px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.8);
            font-size: 11px; color: #e5e7eb; font-weight: 700;
        }
        .meta-label { font-weight: 800; color: #cbd5e1; text-transform: uppercase; letter-spacing: 0.6px; }
        .meta-value { font-weight: 700; color: #f8fafc; }
        .edit-title { font-size: 20px; font-weight: 800; color: #e5e7eb; margin: 0; display: flex; align-items: center; gap: 6px; }
        .edit-name { font-style: italic; color: #f1f5f9; }
    </style>
""", unsafe_allow_html=True)

# --- YARDIMCI FONKSİYONLAR ---
def get_img_as_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

def get_bytes_as_base64(uploaded_file):
    if uploaded_file: return base64.b64encode(uploaded_file.getvalue()).decode()
    return None

PATIENTS_FILE = "patients.json"
USERS_FILE = "users.json"

def generate_patient_id():
    """Boş bırakılırsa hasta için rastgele dosya/TC kodu üretir."""
    return f"P{random.randint(100000, 999999)}"

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def patient_file_for_user(email: str | None):
    """Kullanıcıya özel hasta dosya adı üretir."""
    if not email: return PATIENTS_FILE
    h = hashlib.sha256(email.lower().encode("utf-8")).hexdigest()[:10]
    return f"patients_{h}.json"

def load_users():
    """Kullanıcı listesini oku, yoksa demo kullanıcı oluştur."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:  # noqa: BLE001
            st.warning(f"Kullanıcılar okunamadı: {e}")
    demo = [{"email": "demo@icf.com", "password": hash_pw("1234"), "clinic_name": "ICFevalu8 Demo", "clinician_name": "Fzt. Kullanıcı"}]
    save_users(demo)
    return demo

def save_users(users):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
    except Exception as e:  # noqa: BLE001
        st.warning(f"Kullanıcı kaydı yapılamadı: {e}")

def find_user(email, users):
    for u in users:
        if u.get("email","").lower() == email.lower(): return u
    return None

def load_session_state():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:  # noqa: BLE001
            st.warning(f"Oturum okunamadı: {e}")
    return None

def save_session_state():
    """Oturum bilgisini diske yaz (refresh sonrası açık kalmak için)."""
    data = {
        "logged_in": st.session_state.get("logged_in", False),
        "user_info": st.session_state.get("user_info", {}),
        "page": st.session_state.get("page"),
        "selected_patient_id": st.session_state.get("selected_patient", {}).get("ID") if st.session_state.get("selected_patient") else None,
        "print_mode": st.session_state.get("print_mode", False)
    }
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:  # noqa: BLE001
        st.warning(f"Oturum kaydı yapılamadı: {e}")

def clear_session_state():
    if os.path.exists(SESSION_FILE):
        try: os.remove(SESSION_FILE)
        except Exception as e:  # noqa: BLE001
            st.warning(f"Oturum dosyası silinemedi: {e}")

def load_patient_db(user_email=None, include_demo=True):
    """Kalıcı hasta listesini oku; yeni kullanıcıda demo eklemeyebiliriz."""
    demo_data = [
        {
            "ID": "PDEM01",
            "Hasta Adı": "Ayşe Yılmaz",
            "Tanı": "I63 (İnme/Serebral enfarktüs)",
            "Tarih": "15.02.2026",
            "Age": 62,
            "Gender": "Kadın",
            "Foto": None,
            "icf": {
                "sel_struct": ["s110 - Beyin", "s730 - Üst ekstremite yapıları"],
                "sel_func": ["b730 - Kas gücü fonksiyonları", "b760 - Kas kontrol fonksiyonları", "b710 - Eklem mobilite fonksiyonları"],
                "sel_act": ["d410 - Duruşu değiştirme", "d450 - Yürüme", "d510 - Yıkanma"],
                "sel_part": ["d540 - Kişisel bakım", "d920 - Eğlence ve boş zaman"],
                "sel_env": ["e115 - Kişisel kullanım için ürün ve teknoloji", "e310 - Yakın aile", "e355 - Sağlık profesyonelleri"],
                "sel_pers": ["pf - Kişisel faktörler"],
                "notes_db": {
                    "note_s110 - Beyin": "İskemik lezyon MCA sağ; görüntülemede doğrulandı.",
                    "note_s730 - Üst ekstremite yapıları": "Sol omuz/dirsek çevresinde ödem ve hareket kısıtı.",
                    "note_b730 - Kas gücü fonksiyonları": "Sol üst ve alt ekstremitede 3/5.",
                    "note_b760 - Kas kontrol fonksiyonları": "Ton değişimleri; spastisite hafif.",
                    "note_b710 - Eklem mobilite fonksiyonları": "Sol omuz abdüksiyon kısıtlı, ağrısız.",
                    "note_d410 - Duruşu değiştirme": "Destekle yatak içi dönme yapabiliyor.",
                    "note_d450 - Yürüme": "Yürüme mesafesi 20 m; baston ile.",
                    "note_d510 - Yıkanma": "Gözetimle duş alıyor.",
                    "note_d540 - Kişisel bakım": "Giyinme altına yardıma ihtiyaç duyuyor.",
                    "note_d920 - Eğlence ve boş zaman": "Sosyal katılım kısıtlı; aile desteği var.",
                    "note_e115 - Kişisel kullanım için ürün ve teknoloji": "Baston ve ayak bileği ortezi mevcut.",
                    "note_e310 - Yakın aile": "Aile motivasyonu yüksek.",
                    "note_e355 - Sağlık profesyonelleri": "Fizyoterapi ekibi haftada 3 gün.",
                    "note_pf - Kişisel faktörler": "Motivasyonu yüksek, hedef odaklı."
                },
                "qualifiers_db": {
                    "qual_s110 - Beyin": "3 - Ciddi",
                    "qual_s730 - Üst ekstremite yapıları": "2 - Orta",
                    "qual_b730 - Kas gücü fonksiyonları": "2 - Orta",
                    "qual_b760 - Kas kontrol fonksiyonları": "2 - Orta",
                    "qual_b710 - Eklem mobilite fonksiyonları": "2 - Orta",
                    "qual_d410 - Duruşu değiştirme": "2 - Orta",
                    "qual_d450 - Yürüme": "3 - Ciddi",
                    "qual_d510 - Yıkanma": "2 - Orta",
                    "qual_d540 - Kişisel bakım": "3 - Ciddi",
                    "qual_d920 - Eğlence ve boş zaman": "2 - Orta",
                    "type_e115 - Kişisel kullanım için ürün ve teknoloji": "Fasilitatör",
                    "score_e115 - Kişisel kullanım için ürün ve teknoloji": "2 (Orta)",
                    "type_e310 - Yakın aile": "Fasilitatör",
                    "score_e310 - Yakın aile": "3 (Ciddi)",
                    "type_e355 - Sağlık profesyonelleri": "Fasilitatör",
                    "score_e355 - Sağlık profesyonelleri": "2 (Orta)"
                },
                "current_icd": "I63 Cerebral infarction"
            }
        },
        {"ID": "101", "Hasta Adı": "Adam Sandler", "Tanı": "G20 (Parkinson)", "Tarih": "25.11.2025", "Age": 56, "Gender": "Erkek", "Foto": None},
        {"ID": "102", "Hasta Adı": "Cem Yılmaz", "Tanı": "M54 (Bel Ağrısı)", "Tarih": "24.11.2025", "Age": 51, "Gender": "Erkek", "Foto": None}
    ]
    file = patient_file_for_user(user_email)
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list): data = []
                if include_demo:
                    id_index = {p.get("ID"): i for i, p in enumerate(data)}
                    for demo in demo_data:
                        if demo["ID"] in id_index:
                            data[id_index[demo["ID"]]].update(demo)
                        else:
                            data.insert(0, demo)
                if include_demo and not data: return demo_data
                return data
        except Exception as e:  # noqa: BLE001 - kullanıcıya bilgi göstermek yeterli
            st.warning(f"Hasta verileri okunamadı: {e}")
    if include_demo: return demo_data
    return []

def save_patient_db(patients, user_email=None):
    """Hasta listesini json'a yaz; fotoğraf varsa base64 olarak sakla."""
    safe = []
    for p in patients:
        copy = dict(p)
        foto = copy.get("Foto")
        if foto and not isinstance(foto, str):
            try: copy["Foto"] = get_bytes_as_base64(foto)
            except: copy["Foto"] = None
        safe.append(copy)
    try:
        file = patient_file_for_user(user_email)
        with open(file, "w", encoding="utf-8") as f:
            json.dump(safe, f, ensure_ascii=False, indent=4)
    except Exception as e:  # noqa: BLE001
        st.warning(f"Hasta verileri kaydedilemedi: {e}")

def get_patient_by_id(pid):
    for p in st.session_state.get('patient_db_list', []):
        if p.get('ID') == pid:
            return p
    return None

def render_patient_avatar(hasta):
    """Hasta fotoğrafını veya baş harflerini şık bir çerçevede döndürür."""
    if hasta.get('Foto'):
        try:
            b64 = hasta['Foto'] if isinstance(hasta['Foto'], str) else get_bytes_as_base64(hasta['Foto'])
            return f"<div class='photo-frame' style=\"background-image:url('data:image/png;base64,{b64}');\"></div>"
        except:  # noqa: E722 - streamlit yüklemelerinde küçük dönüştürme hataları yaşanabiliyor
            pass
    initials = "".join([part[0] for part in hasta.get('Hasta Adı', 'Hasta').split() if part])[:2].upper() or "?"
    return f"<div class='photo-frame placeholder'>{initials}</div>"

@st.cache_data
def load_data():
    try:
        df_icd = pd.read_csv("ICD Kodu.csv")
        icd_list = df_icd["Display"].dropna().unique().tolist(); icd_list.sort()
        df_icf = pd.read_csv("ICF TabloVerileri.csv")
        df_icf['Kısa'] = df_icf['Kod'].astype(str) + " - " + df_icf['Tr Açıklama'].astype(str)
        get_list = lambda cat: df_icf[df_icf['Kategori'] == cat]['Kısa'].unique().tolist()
        d_codes = df_icf[df_icf['Kategori'] == 'd']
        return {
            "ICD": icd_list, "body_struct": get_list('s'), "body_func": get_list('b'),
            "activity": d_codes[d_codes['Kod'].astype(str).str.match(r'^d[1-5]')]['Kısa'].unique().tolist(),
            "participation": d_codes[d_codes['Kod'].astype(str).str.match(r'^d[6-9]')]['Kısa'].unique().tolist(),
            "env": get_list('e'), "personal": get_list('pf')
        }
    except: return None

DB = load_data()

# --- STATE ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_info' not in st.session_state: st.session_state['user_info'] = {'clinic_name': 'ICFevalu8'}
if 'users_db' not in st.session_state: st.session_state['users_db'] = load_users()
if 'show_add_patient' not in st.session_state: st.session_state['show_add_patient'] = False
if 'patient_db_list' not in st.session_state:
    st.session_state['patient_db_list'] = load_patient_db()

defaults = {'page': 'login', 'auth_mode': 'login', 'selected_patient': None, 'print_mode': False,
            'sel_struct': [], 'sel_func': [], 'sel_act': [], 'sel_part': [], 'sel_env': [], 'sel_pers': [],
            'notes_db': {}, 'current_icd': None, 'qualifiers_db': {}, 'active_patient_id': None,
            'edit_patient_id': None, 'delete_confirm_id': None}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

ICF_KEYS = ['sel_struct', 'sel_func', 'sel_act', 'sel_part', 'sel_env', 'sel_pers', 'notes_db', 'qualifiers_db', 'current_icd']

def empty_icf_state():
    return {k: ([] if 'sel_' in k else {} if k.endswith('_db') else None) for k in ICF_KEYS}

def load_icf_state_from_patient(hasta):
    """Seçili hastanın ICF verilerini session_state'e aktar."""
    icf = hasta.get('icf') or {}
    for k in ICF_KEYS:
        default_val = [] if 'sel_' in k else {} if k.endswith('_db') else None
        st.session_state[k] = icf.get(k, default_val)

def persist_icf_state(hasta):
    """Güncel ICF durumunu hasta kaydına ve dosyaya yaz."""
    if not hasta or not hasta.get('ID'): return
    icf_data = {k: st.session_state.get(k, [] if 'sel_' in k else {} if k.endswith('_db') else None) for k in ICF_KEYS}
    hasta['icf'] = icf_data
    # patient_db_list'i güncelle
    pid = hasta.get('ID')
    updated = False
    for i, p in enumerate(st.session_state.get('patient_db_list', [])):
        if p.get('ID') == pid:
            st.session_state['patient_db_list'][i] = hasta
            updated = True
            break
    if not updated:
        st.session_state.setdefault('patient_db_list', []).append(hasta)
    user_email = st.session_state.get('user_info', {}).get('email')
    save_patient_db(st.session_state['patient_db_list'], user_email)

# Oturum dosyasından geri gel (refresh sonrası devam)
session_snapshot = load_session_state()
if session_snapshot and session_snapshot.get('logged_in') and not st.session_state['logged_in']:
    st.session_state['user_info'] = session_snapshot.get('user_info', st.session_state['user_info'])
    st.session_state['logged_in'] = True
    st.session_state['page'] = session_snapshot.get('page', 'dashboard')
    st.session_state['print_mode'] = session_snapshot.get('print_mode', False)
    email = st.session_state['user_info'].get('email')
    is_demo = email and email.lower() == "demo@icf.com"
    st.session_state['patient_db_list'] = load_patient_db(email, include_demo=is_demo)
    sel_pid = session_snapshot.get('selected_patient_id')
    if sel_pid:
        p = get_patient_by_id(sel_pid)
        if p:
            st.session_state['selected_patient'] = p
            st.session_state['active_patient_id'] = sel_pid
            load_icf_state_from_patient(p)

# --- 4. GİRİŞ ---
def show_login_register():
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.write(""); st.write("")
        
        # Logo HTML
        logo_b64 = get_img_as_base64("logo.png")
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="120">' if logo_b64 else ''
        
        st.markdown(f"""
        <div style="text-align:center; background:white; padding:40px; border-radius:12px; border:1px solid #eee; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
            {logo_html}
            <h2 style='color:#28a745; margin:10px 0; font-weight:800;'>ICFevalu<span style="color:#0d1b2a;">8</span></h2>
            <p style='color:#666; font-size:14px;'>Klinik Değerlendirme Sistemi</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        
        if st.session_state['auth_mode'] == 'login':
            with st.form("l"):
                email = st.text_input("E-posta", value="demo@icf.com")
                pw = st.text_input("Şifre", type="password", value="1234")
                if st.form_submit_button("Giriş Yap", type="primary", use_container_width=True):
                    user = find_user(email, st.session_state['users_db'])
                    if not user or user.get("password") != hash_pw(pw):
                        st.error("E-posta veya şifre hatalı.")
                    else:
                        st.session_state['user_info'] = {
                            'clinic_name': user.get('clinic_name', 'ICFevalu8'),
                            'clinician_name': user.get('clinician_name', 'Klinisyen'),
                            'email': user.get('email')
                        }
                        is_demo = user.get('email',"").lower() == "demo@icf.com"
                        st.session_state['patient_db_list'] = load_patient_db(user.get('email'), include_demo=is_demo)
                        st.session_state['active_patient_id'] = None
                        st.session_state['logged_in']=True; st.session_state['page']='dashboard'
                        save_session_state()
                        st.rerun()
            st.write("")
            if st.button("Yeni Klinik Kaydı", type="secondary", use_container_width=True):
                st.session_state['auth_mode']='register'; st.rerun()
            st.markdown("<hr>", unsafe_allow_html=True)
            st.caption("Harici giriş seçenekleri (demo):")
            cga, caa = st.columns(2)
            with cga:
                if st.button("🔵 Google", key="btn_google", use_container_width=True):
                    mock_email = "google_user@demo.icf"
                    st.session_state['user_info'] = {
                        'clinic_name': 'ICFevalu8 (Google)',
                        'clinician_name': 'Google Kullanıcısı',
                        'email': mock_email
                    }
                    st.session_state['patient_db_list'] = load_patient_db(mock_email, include_demo=False)
                    st.session_state['active_patient_id'] = None
                    st.session_state['logged_in']=True; st.session_state['page']='dashboard'
                    save_session_state()
                    st.rerun()
            with caa:
                if st.button(" Apple", key="btn_apple", use_container_width=True):
                    mock_email = "apple_user@demo.icf"
                    st.session_state['user_info'] = {
                        'clinic_name': 'ICFevalu8 (Apple)',
                        'clinician_name': 'Apple Kullanıcısı',
                        'email': mock_email
                    }
                    st.session_state['patient_db_list'] = load_patient_db(mock_email, include_demo=False)
                    st.session_state['active_patient_id'] = None
                    st.session_state['logged_in']=True; st.session_state['page']='dashboard'
                    save_session_state()
                    st.rerun()
        else:
            with st.form("r"):
                st.markdown("##### Yeni Kayıt")
                c_n = st.text_input("Klinik İsmi")
                u_n = st.text_input("Klinisyen Adı")
                email = st.text_input("E-posta")
                pw = st.text_input("Şifre", type="password")
                if st.form_submit_button("Kaydol", type="primary", use_container_width=True):
                    if not (c_n and u_n and email and pw):
                        st.error("Lütfen tüm alanları doldurun.")
                    elif find_user(email, st.session_state['users_db']):
                        st.error("Bu e-posta ile kayıt zaten var.")
                    else:
                        new_user = {"clinic_name": c_n, "clinician_name": u_n, "email": email, "password": hash_pw(pw)}
                        st.session_state['users_db'].append(new_user)
                        save_users(st.session_state['users_db'])
                        st.session_state['user_info']={'clinic_name': c_n, 'clinician_name': u_n, 'email': email}
                        st.session_state['patient_db_list'] = []
                        save_patient_db(st.session_state['patient_db_list'], email)
                        st.session_state['active_patient_id'] = None
                        st.session_state['logged_in']=True; st.session_state['page']='dashboard'
                        save_session_state()
                        st.rerun()
            if st.button("Geri", type="secondary", use_container_width=True):
                st.session_state['auth_mode']='login'; st.rerun()

# --- 5. DASHBOARD ---
def show_dashboard():
    info = st.session_state['user_info']
    user_email = info.get('email')
    
    # HEADER (LOGO | TEXT | ÇIKIŞ)
    with st.container():
        c_left, c_logo, c_logout = st.columns([3.2, 2.8, 2], vertical_alignment="center")

        with c_left:
            st.markdown(f"""
            <div style='line-height:1.2;'>
                <div style="font-size:14px; color:#0056b3; font-weight:bold;">Merhaba, {info.get('clinician_name', 'Klinisyen')}</div>
                <div style="font-size:20px; font-weight:800; color:#333;">{info.get('clinic_name', 'Panel')}</div>
            </div>
            """, unsafe_allow_html=True)

        with c_logo:
            center_style = "display:flex; justify-content:flex-start; align-items:center;"
            logo_b64 = get_img_as_base64("logo.png")
            if logo_b64:
                st.markdown(f"<div style='{center_style}'><img src='data:image/png;base64,{logo_b64}' width='110'></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='{center_style}; font-size:32px;'>🏥</div>", unsafe_allow_html=True)

        with c_logout:
            if st.button("Çıkış Yap", type="secondary", use_container_width=True):
                st.session_state['logged_in'] = False
                st.session_state['page'] = 'login'
                st.session_state['patient_db_list'] = load_patient_db()  # varsayılan/demosu
                st.session_state['active_patient_id'] = None
                clear_session_state()
                st.rerun()
    
    st.divider()

    if not st.session_state['show_add_patient']:
        c_search, c_add = st.columns([5, 2], vertical_alignment="bottom")
        search_q = c_search.text_input("Ara", placeholder="Hasta adı veya protokol no...", label_visibility="collapsed")
        
        with c_add:
            btn_label = "➕ İlk hastanızı ekleyin!" if not st.session_state['patient_db_list'] else "➕ Yeni Hasta Ekle"
            if st.button(btn_label, type="primary", use_container_width=True):
                st.session_state['show_add_patient'] = True; st.rerun()
        
        st.write("")
        st.markdown("### Hasta Listesi")
        
        patients = st.session_state['patient_db_list']
        if search_q: patients = [p for p in patients if search_q.lower() in p.get('Hasta Adı','').lower()]

        if not patients:
            st.info("Henüz hasta bulunmuyor. 'İlk hastanızı ekleyin!' butonuyla başlayabilirsiniz.")
        else:
            for p in patients:
                with st.container(border=True):
                    c_det, c_open, c_edit, c_del = st.columns([6, 1.4, 0.8, 0.8], vertical_alignment="center")
                    with c_det:
                        tani = p.get('Tanı') if p.get('Tanı') else "Tanı Yok"
                        st.markdown(f"**{p.get('Hasta Adı')}**")
                        st.caption(f"Dosya: {p.get('ID')} | {tani} | {p.get('Tarih')}")
                    with c_open:
                        if st.button("Dosyayı Aç", key=f"open_{p['ID']}", use_container_width=True):
                            st.session_state['selected_patient'] = p
                            st.session_state['active_patient_id'] = None  # ICF state yeniden yüklensin
                            st.session_state['page'] = 'framework'
                            st.session_state['edit_patient_id'] = None
                            st.session_state['delete_confirm_id'] = None
                            save_session_state()
                            st.rerun()
                    with c_edit:
                        if st.button("✏️", key=f"editbtn_{p['ID']}", help="Düzenle", type="secondary"):
                            st.session_state['edit_patient_id'] = p['ID']
                            st.session_state['delete_confirm_id'] = None
                            st.rerun()
                    with c_del:
                        if st.button("🗑", key=f"delbtn_{p['ID']}", help="Sil", type="secondary"):
                            st.session_state['delete_confirm_id'] = p['ID']
                            st.session_state['edit_patient_id'] = None
                            st.rerun()

                if st.session_state.get('edit_patient_id') == p.get('ID'):
                    with st.container(border=True):
                        st.markdown("**Hasta Bilgilerini Düzenle**")
                        new_name = st.text_input("Ad Soyad", value=p.get('Hasta Adı', ''), key=f"edit_name_{p['ID']}")
                        new_tani = st.text_input("Tanı", value=p.get('Tanı',''), key=f"edit_tani_{p['ID']}")
                        c_ed1, c_ed2 = st.columns(2)
                        new_age = c_ed1.number_input("Yaş", 0, 120, value=int(p.get('Age',0) or 0), key=f"edit_age_{p['ID']}")
                        new_gender = c_ed2.selectbox("Cinsiyet", ["Kadın","Erkek"], index=0 if (p.get('Gender','Kadın')=="Kadın") else 1, key=f"edit_gender_{p['ID']}")
                        new_date = st.text_input("Tarih", value=p.get('Tarih',''), key=f"edit_date_{p['ID']}")
                        cc1, cc2 = st.columns(2)
                        if cc1.button("Kaydet", key=f"save_{p['ID']}", type="primary"):
                            p.update({"Hasta Adı": new_name, "Tanı": new_tani, "Age": new_age, "Gender": new_gender, "Tarih": new_date})
                            if st.session_state.get('selected_patient', {}).get('ID') == p.get('ID'):
                                st.session_state['selected_patient'] = p
                            save_patient_db(st.session_state['patient_db_list'], user_email)
                            save_session_state()
                            st.session_state['edit_patient_id'] = None
                            st.rerun()
                        if cc2.button("Vazgeç", key=f"cancel_edit_{p['ID']}", type="secondary"):
                            st.session_state['edit_patient_id'] = None
                            st.rerun()

                if st.session_state.get('delete_confirm_id') == p.get('ID'):
                    with st.container(border=True):
                        st.warning("Bu hastayı kalıcı olarak silmek üzeresiniz.")
                        cd1, cd2 = st.columns(2)
                        if cd1.button("Sil", key=f"confirm_del_{p['ID']}", type="secondary"):
                            st.session_state['patient_db_list'] = [x for x in st.session_state['patient_db_list'] if x.get('ID') != p.get('ID')]
                            if st.session_state.get('selected_patient', {}).get('ID') == p.get('ID'):
                                st.session_state['selected_patient'] = None
                                st.session_state['active_patient_id'] = None
                            save_patient_db(st.session_state['patient_db_list'], user_email)
                            save_session_state()
                            st.session_state['delete_confirm_id'] = None
                            st.rerun()
                        if cd2.button("Vazgeç", key=f"cancel_del_{p['ID']}", type="secondary"):
                            st.session_state['delete_confirm_id'] = None
                            st.rerun()
    else:
        with st.container(border=True):
            st.subheader("Yeni Hasta Kartı")
            c1, c2 = st.columns(2)
            name = c1.text_input("Ad Soyad")
            prot = c2.text_input("Dosya / TC No")
            age = c1.number_input("Yaş", 0, 120, 30)
            gender = c2.selectbox("Cinsiyet", ["Kadın", "Erkek"])
            
            st.write("")
            cb1, cb2 = st.columns(2)
            if cb1.button("İptal", type="secondary", use_container_width=True): st.session_state['show_add_patient']=False; st.rerun()
            if cb2.button("Dosyayı Oluştur", type="primary", use_container_width=True):
                if name:
                    prot_final = prot if prot else generate_patient_id()
                    new_p = {"ID": prot_final, "Hasta Adı": name, "Age": age, "Gender": gender, "Tanı": "", "Tarih": pd.Timestamp.now().strftime('%d.%m.%Y'), "Foto": None}
                    new_p['icf'] = empty_icf_state()
                    st.session_state['patient_db_list'].insert(0, new_p)
                    st.session_state['selected_patient'] = new_p
                    load_icf_state_from_patient(new_p)
                    st.session_state['active_patient_id'] = new_p.get('ID')
                    save_patient_db(st.session_state['patient_db_list'], st.session_state.get('user_info', {}).get('email'))
                    st.session_state['show_add_patient'] = False; st.session_state['page']='framework'
                    save_session_state()
                    st.rerun()

# --- 6. ICF EDİTÖR ---
def render_edit_mode(hasta):
    # Hasta değiştiyse ilgili ICF verilerini yükle
    pid = hasta.get('ID')
    if st.session_state.get('active_patient_id') != pid:
        load_icf_state_from_patient(hasta)
        st.session_state['active_patient_id'] = pid

    c1, c2 = st.columns([0.5, 8], vertical_alignment="center")
    with c1: 
        if st.button("←", type="secondary"):
            st.session_state['page']='dashboard'
            save_session_state()
            st.rerun()
    with c2:
        name = hasta.get('Hasta Adı') or hasta.get('Ad') or "Hasta İsmi"
        st.markdown(f"<div class='edit-title'><span class='edit-name'>{name}</span> ICF Editörü</div>", unsafe_allow_html=True)
    
    st.write("")

    # HASTA KARTI
    with st.container(border=True):
        name = hasta.get('Hasta Adı') or hasta.get('Ad') or "Yeni Hasta"
        age = hasta.get('Age', '-')
        gender = hasta.get('Gender', '-')
        date = hasta.get('Tarih', '-')
        diag = hasta.get('Tanı') or "Tanı bilgisi girilmedi"
        patient_card_html = f"""
        <div class="patient-card">
            <div>{render_patient_avatar(hasta)}</div>
            <div class="patient-meta">
                <div class="patient-id">Dosya No: {hasta.get('ID', '-')}</div>
                <div class="patient-name">{name}</div>
                <div class="badge-row">
                    <div class="badge">{age} Yaş</div>
                    <div class="badge gray">{gender}</div>
                    <div class="badge gray">{date}</div>
                </div>
                <div class="diag-box"><span class="meta-label">Tanı:</span> {diag}</div>
            </div>
            <div style="flex: 1; min-width: 160px;">
                <div class="meta-grid">
                    <div class="meta-chip"><span class="meta-label">ICD</span><span class="meta-value">{st.session_state.get('current_icd','-')}</span></div>
                    <div class="meta-chip"><span class="meta-label">Kayıt</span><span class="meta-value">{date}</span></div>
                    <div class="meta-chip"><span class="meta-label">Dosya</span><span class="meta-value">{hasta.get('ID','-')}</span></div>
                </div>
            </div>
        </div>
        """
        st.markdown(patient_card_html, unsafe_allow_html=True)
        c_up, _ = st.columns([1.2, 5])
        with c_up:
            with st.expander("Fotoğraf Güncelle", expanded=False):
                up = st.file_uploader("Fotoğraf Yükle", type=['png','jpg'], label_visibility="collapsed", key=f"photo_{hasta.get('ID','new')}")
                if up:
                    hasta['Foto'] = get_bytes_as_base64(up)
                    save_patient_db(st.session_state['patient_db_list'], st.session_state.get('user_info', {}).get('email'))
                    st.rerun()

    st.write("")

    # ICD
    with st.container(border=True):
        st.caption("SAĞLIK DURUMU (ICD)")
        cur_idx = 0
        if st.session_state['current_icd'] in DB['ICD']: cur_idx = DB['ICD'].index(st.session_state['current_icd'])
        st.session_state['current_icd'] = st.selectbox("Tanı", DB['ICD'], index=cur_idx, label_visibility="collapsed")

    st.markdown("<div style='text-align:center; color:#ccc; font-size:14px; margin:10px 0;'>⬇</div>", unsafe_allow_html=True)

    # ORTA KATMAN (PDF yerleşimine benzer oklarla)
    col_left, col_arr1, col_act, col_arr2, col_part = st.columns([2, 0.25, 1.5, 0.25, 1.5], vertical_alignment="center")
    with col_left:
        render_input_box("Vücut Yapısı (s)", "sel_struct", DB['body_struct'], "#0056b3", "standard")
        render_input_box("Vücut Fonk. (b)", "sel_func", DB['body_func'], "#d63384", "standard")
    with col_arr1:
        st.markdown("<div style='display:flex; align-items:center; justify-content:center; height:100%; color:#94a3b8; font-size:22px;'>↔</div>", unsafe_allow_html=True)
    with col_act: render_input_box("Aktivite (d)", "sel_act", DB['activity'], "#d39e00", "standard")
    with col_arr2:
        st.markdown("<div style='display:flex; align-items:center; justify-content:center; height:100%; color:#94a3b8; font-size:22px;'>↔</div>", unsafe_allow_html=True)
    with col_part: render_input_box("Katılım (d)", "sel_part", DB['participation'], "#c82333", "standard")

    st.markdown("<div style='text-align:center; color:#94a3b8; font-size:16px; margin:10px 0;'>⬇</div>", unsafe_allow_html=True)

    # ALT KATMAN
    c_e, c_pf = st.columns(2)
    with c_e: render_input_box("Çevresel (e)", "sel_env", DB['env'], "#28a745", "env")
    with c_pf: render_input_box("Kişisel (pf)", "sel_pers", DB['personal'], "#6f42c1", "env")

    st.divider()
    c_x, c_btn, c_y = st.columns([1, 2, 1])
    with c_btn:
        if st.button("🖨️ RAPORU OLUŞTUR & YAZDIR", type="primary", use_container_width=True):
            st.session_state['print_mode'] = True
            save_session_state()
            st.rerun()
    
    # Her etkileşim sonrası ICF durumunu kalıcı kaydet
    persist_icf_state(hasta)
    save_session_state()

def render_input_box(title, state_key, options, color, mode):
    # KUTU RENGİ VE ÇERÇEVESİ
    with st.container(border=True):
        st.markdown(f"<div style='text-align:center; font-weight:700; color:{color}; font-size:14px; margin-bottom:10px;'>{title}</div>", unsafe_allow_html=True)
        
        # NATIVE MULTISELECT (SORUNSUZ ÇALIŞIR)
        prev = st.session_state[state_key]
        # Seçili olup listede olmayan maddeleri de seçeneklere ekle ki demo kayıtlar kaybolmasın.
        merged_options = options + [x for x in prev if x not in options]
        sel = st.multiselect(
            "Ekle",
            merged_options,
            default=prev,
            key=f"ms_{state_key}",
            label_visibility="collapsed",
            placeholder="Seçim yapın veya aramak için yazın..."
        )
        st.session_state[state_key] = sel
        
        if sel:
            st.markdown("---")
            for item in sel:
                # NATIVE EXPANDER (SORUNSUZ ÇALIŞIR)
                with st.expander(item.split(' - ')[0], expanded=False):
                    st.caption(item)
                    q_key = f"qual_{item}"
                    if mode == "standard":
                        opts = ["0 - Sorun Yok", "1 - Hafif", "2 - Orta", "3 - Ciddi", "4 - Tam", "8 - Belirtilmemiş", "9 - Uygulanamaz"]
                        curr = st.session_state['qualifiers_db'].get(q_key, opts[0])
                        try: idx = opts.index(curr)
                        except: idx=0
                        st.session_state['qualifiers_db'][q_key] = st.selectbox("Derece:", opts, index=idx, key=f"sb_{q_key}")
                    elif mode == "env":
                        c1, c2 = st.columns(2)
                        t_key = f"type_{item}"; s_key = f"score_{item}"
                        st.session_state['qualifiers_db'][t_key] = c1.radio("Tip", ["Bariyer", "Fasilitatör"], key=f"rad_{item}")
                        s_opts = ["0", "1 (Hafif)", "2 (Orta)", "3 (Ciddi)", "4 (Tam)"]
                        curr_s = st.session_state['qualifiers_db'].get(s_key, "0")
                        st.session_state['qualifiers_db'][s_key] = c2.select_slider("Drc", options=s_opts, value=curr_s, key=f"sl_{item}")

                    n_key = f"note_{item}"
                    st.session_state['notes_db'][n_key] = st.text_area("Bulgu:", value=st.session_state['notes_db'].get(n_key,""), key=f"ta_{n_key}", height=60)

# --- 7. PRINT MODE ---
def render_print_mode(hasta):
    # Yazdırma öncesi mevcut durumu kaydet
    persist_icf_state(hasta)

    if st.button("❌ Kapat", type="secondary"):
        st.session_state['print_mode'] = False
        save_session_state()
        st.rerun()

    clinic = st.session_state['user_info'].get('clinic_name', 'ICFevalu8 Clinic')
    logo_b64 = get_img_as_base64("logo.png")
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:60px; margin-right:15px;">' if logo_b64 else ''
    
    p_img = ""
    if hasta.get('Foto'):
        try:
            b = get_bytes_as_base64(hasta['Foto'])
            p_img = f'<img src="data:image/png;base64,{b}" style="width:80px; height:80px; border-radius:50%; object-fit:cover; border:2px solid #eee;">'
        except: pass

    def format_item(txt, mode):
        parts = txt.split(" - ", 1)
        c, l = (parts[0], parts[1]) if len(parts)==2 else (txt.split()[0], txt)
        disp = c
        if mode == "standard":
            val = st.session_state['qualifiers_db'].get(f"qual_{txt}", "0").split()[0]
            disp = f"{c}.{val}"
        elif mode == "env":
            typ = st.session_state['qualifiers_db'].get(f"type_{txt}", "Bariyer")
            scr = st.session_state['qualifiers_db'].get(f"score_{txt}", "0")[0]
            sep = "." if typ == "Bariyer" else "+"
            disp = f"{c}{sep}{scr}"
        return disp, l

    def simple_list(items):
        if not items: return "<div class='empty'>-</div>"
        h = ""
        for i in items:
            c, l = format_item(i, "standard")
            n = st.session_state['notes_db'].get(f"note_{i}", "")
            nh = f"<div class='note'><b>Bulgu:</b> {n}</div>" if n else ""
            h += f"<div class='item'><span class='code'>{c}</span> <span class='lbl'>{l}</span>{nh}</div>"
        return h

    def split_list(items):
        if not items: return "<div class='empty'>-</div>"
        bar, fac = [], []
        for i in items:
            if st.session_state['qualifiers_db'].get(f"type_{i}", "Bariyer") == "Bariyer": bar.append(i)
            else: fac.append(i)
        
        def build(sub):
            h = ""
            for x in sub:
                c, l = format_item(x, "env")
                n = st.session_state['notes_db'].get(f"note_{x}", "")
                nh = f"<div class='note'><b>Bulgu:</b> {n}</div>" if n else ""
                h += f"<div class='item'><span class='code'>{c}</span> <span class='lbl'>{l}</span>{nh}</div>"
            return h if h else "<div class='empty'>-</div>"

        return f"""
        <div style="display:flex; gap:10px;">
            <div style="flex:1; border-right:1px dashed #ccc; padding-right:5px;">
                <div class="sub-h" style="color:#c62828;">BARİYERLER (.)</div>{build(bar)}
            </div>
            <div style="flex:1; padding-left:5px;">
                <div class="sub-h" style="color:#2e7d32;">FASİLİTATÖRLER (+)</div>{build(fac)}
            </div>
        </div>
        """

    arrow_v = '<div style="text-align:center; color:#999; margin:5px 0;">⬇</div>'
    arrow_h = '<div style="display:flex; align-items:center; color:#999;">↔</div>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        @page {{ size: A4; margin: 10mm; }}
        @media print {{
            @page {{ size: A4; margin: 10mm; }}
            body {{ padding: 8mm !important; max-width: 190mm !important; transform: scale(0.92); transform-origin: top left; }}
        }}
        body {{ font-family: 'Inter', sans-serif; padding: 14px; background: white; color: #333; max-width: 200mm; margin: auto; }}
        .head {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #000; padding-bottom: 12px; margin-bottom: 18px; page-break-inside: avoid; }}
        .title {{ font-size: 24px; font-weight: 800; color: #000; line-height:1; }}
        .sub {{ font-size: 12px; color: #0056b3; font-weight: 700; margin-top: 4px; }}
        .clinic {{ font-size: 11px; color: #666; text-transform: uppercase; font-weight: 600; letter-spacing: 1px; }}
        .meta {{ font-size:11px; color:#555; margin-top:4px; }}
        .box {{ border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: #fff; height: 100%; box-sizing: border-box; page-break-inside: avoid; break-inside: avoid; }}
        .bx-t {{ font-size: 11px; font-weight: 700; text-transform: uppercase; border-bottom: 1px solid #eee; padding-bottom: 4px; margin-bottom: 8px; text-align: center; }}
        .hlth {{ border: 2px solid #333; background: #f8f9fa; text-align: center; padding: 8px; border-radius: 8px; width: 60%; margin: 0 auto 8px auto; page-break-inside: avoid; }}
        .grid-m {{ display: grid; grid-template-columns: 2fr 0.2fr 1.5fr 0.2fr 1.5fr; gap: 4px; }}
        .grid-b {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 8px; }}
        .grp {{ border: 1px solid #ccc; border-radius: 8px; padding: 4px; background: #fcfcfc; display:flex; flex-direction:column; gap:4px; page-break-inside: avoid; break-inside: avoid; }}
        .item {{ font-size: 10px; margin-bottom: 5px; }}
        .code {{ font-weight: 700; margin-right: 4px; }}
        .note {{ font-size: 9px; color: #666; background: #f0f0f0; padding: 2px 4px; margin-top: 2px; border-left: 2px solid #ccc; font-style:italic; }}
        .empty {{ font-size: 9px; color: #ccc; text-align: center; }}
        .sub-h {{ font-size: 8px; font-weight: 700; margin-bottom: 3px; }}
        .c-bl {{ color:#0056b3; border-color:#0056b3; }} .c-pk {{ color:#d63384; border-color:#d63384; }}
        .c-or {{ color:#d39e00; border-color:#d39e00; }} .c-rd {{ color:#c82333; border-color:#c82333; }}
        .c-gr {{ color:#28a745; border-color:#28a745; }} .c-pr {{ color:#6f42c1; border-color:#6f42c1; }}
        .legend {{ margin-top: 16px; font-size: 10px; color: #666; text-align: center; border-top: 1px solid #eee; padding-top: 8px; }}
        @media print {{ button {{ display: none; }} }}
    </style>
    </head>
    <body>
        <div class="head">
            <div style="display:flex; align-items:center; gap:20px;">
                {logo_html}
                {p_img}
                <div>
                    <div class="clinic">{clinic}</div>
                    <div class="title">{hasta.get('Hasta Adı')}</div>
                    <div class="sub">ICF Değerlendirme Raporu</div>
                    <div class="meta">
                        Dosya No: {hasta.get('ID')} | Yaş: {hasta.get('Age','-')} | Cinsiyet: {hasta.get('Gender','-')}
                    </div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:11px; font-weight:700; color:#999;">RAPOR TARİHİ</div>
                <div style="font-size:16px; font-weight:600;">{pd.Timestamp.now().strftime('%d.%m.%Y')}</div>
            </div>
        </div>

        <div class="hlth">
            <div style="font-size:11px; font-weight:700; color:#666; text-transform:uppercase;">SAĞLIK DURUMU (ICD)</div>
            <div style="font-size:16px; font-weight:700;">{st.session_state.get('current_icd', '-')}</div>
        </div>

        {arrow_v}

        <div class="grid-m">
            <div class="grp">
                <div class="box" style="border-top:3px solid #0056b3;"><div class="bx-t c-bl">Vücut Yapısı (s)</div>{simple_list(st.session_state['sel_struct'])}</div>
                <div class="box" style="border-top:3px solid #d63384;"><div class="bx-t c-pk">Vücut Fonk. (b)</div>{simple_list(st.session_state['sel_func'])}</div>
            </div>
            {arrow_h}
            <div class="box" style="border-top:3px solid #d39e00;"><div class="bx-t c-or">Aktivite (d)</div>{simple_list(st.session_state['sel_act'])}</div>
            {arrow_h}
            <div class="box" style="border-top:3px solid #c82333;"><div class="bx-t c-rd">Katılım (d)</div>{simple_list(st.session_state['sel_part'])}</div>
        </div>

        {arrow_v}

        <div class="grid-b">
            <div class="box" style="border-top:3px solid #28a745;"><div class="bx-t c-gr">Çevresel Faktörler (e)</div>{split_list(st.session_state['sel_env'])}</div>
            <div class="box" style="border-top:3px solid #6f42c1;"><div class="bx-t c-pr">Kişisel Faktörler (pf)</div>{split_list(st.session_state['sel_pers'])}</div>
        </div>

        <div class="legend">Not: Niteleyicilerde nokta (<b>.</b>) Problemi/Bariyeri, artı (<b>+</b>) Fasilitatörü/Desteği ifade eder.</div>
        
        <div style="text-align:center; margin-top:30px;">
            <button onclick="window.print()" style="background:#28a745; color:#fff; padding:12px 24px; border:none; border-radius:6px; cursor:pointer; font-weight:600;">YAZDIR / PDF KAYDET</button>
        </div>
    </body>
    </html>
    """
    components.html(html, height=1200, scrolling=True)

# --- MAIN ---
if not st.session_state['logged_in']: show_login_register()
else:
    if st.session_state['page'] == 'dashboard': show_dashboard()
    elif st.session_state['page'] == 'framework':
        if st.session_state['print_mode']: render_print_mode(st.session_state.get('selected_patient', {}))
        else: render_edit_mode(st.session_state.get('selected_patient', {}))

if st.session_state.get('logged_in'):
    save_session_state()
