import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import base64
import os
import datetime

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
        
        /* İKİNCİL BUTONLAR (GRİ) */
        button[kind="secondary"] {
            background-color: #f8f9fa !important;
            color: #333 !important;
            border: 1px solid #ccc !important;
        }
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
if 'show_add_patient' not in st.session_state: st.session_state['show_add_patient'] = False
if 'patient_db_list' not in st.session_state:
    st.session_state['patient_db_list'] = [
        {"ID": "101", "Hasta Adı": "Adam Sandler", "Tanı": "G20 (Parkinson)", "Tarih": "25.11.2025", "Age": 56, "Gender": "Erkek", "Foto": None},
        {"ID": "102", "Ad": "Cem Yılmaz", "Tanı": "M54 (Bel Ağrısı)", "Tarih": "24.11.2025", "Age": 51, "Gender": "Erkek", "Foto": None}
    ]

defaults = {'page': 'login', 'auth_mode': 'login', 'selected_patient': None, 'print_mode': False,
            'sel_struct': [], 'sel_func': [], 'sel_act': [], 'sel_part': [], 'sel_env': [], 'sel_pers': [],
            'notes_db': {}, 'current_icd': None, 'qualifiers_db': {}}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

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
            <h2 style='color:#28a745; margin:10px 0; font-weight:800;'>ICFevalu8</h2>
            <p style='color:#666; font-size:14px;'>Klinik Değerlendirme Sistemi</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        
        if st.session_state['auth_mode'] == 'login':
            with st.form("l"):
                st.text_input("E-posta", value="demo@icf.com")
                st.text_input("Şifre", type="password", value="1234")
                if st.form_submit_button("Giriş Yap", type="primary", use_container_width=True):
                    if not st.session_state['user_info'].get('clinician_name'):
                        st.session_state['user_info'] = {'clinic_name': 'ICFevalu8 Demo', 'clinician_name': 'Fzt. Kullanıcı'}
                    st.session_state['logged_in']=True; st.session_state['page']='dashboard'; st.rerun()
            st.write("")
            if st.button("Yeni Klinik Kaydı", type="secondary", use_container_width=True):
                st.session_state['auth_mode']='register'; st.rerun()
        else:
            with st.form("r"):
                st.markdown("##### Yeni Kayıt")
                c_n = st.text_input("Klinik İsmi")
                u_n = st.text_input("Klinisyen Adı")
                st.text_input("E-posta"); st.text_input("Şifre", type="password")
                if st.form_submit_button("Kaydol", type="primary", use_container_width=True):
                    st.session_state['user_info']={'clinic_name': c_n, 'clinician_name': u_n}
                    st.session_state['logged_in']=True; st.session_state['page']='dashboard'; st.rerun()
            if st.button("Geri", type="secondary", use_container_width=True):
                st.session_state['auth_mode']='login'; st.rerun()

# --- 5. DASHBOARD ---
def show_dashboard():
    info = st.session_state['user_info']
    
    # HEADER (LOGO | TEXT | ÇIKIŞ)
    with st.container():
        c1, c2, c3 = st.columns([1, 6, 1.5], vertical_alignment="center")
        
        with c1:
            if os.path.exists("logo.png"): st.image("logo.png", width=80)
            else: st.header("🏥")
        
        with c2:
            st.markdown(f"""
            <div style='line-height:1.2; margin-left: -10px;'>
                <div style="font-size:14px; color:#0056b3; font-weight:bold;">Merhaba, {info.get('clinician_name', 'Klinisyen')}</div>
                <div style="font-size:20px; font-weight:800; color:#333;">{info.get('clinic_name', 'Panel')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with c3:
            if st.button("Çıkış Yap", type="secondary", use_container_width=True):
                st.session_state['logged_in'] = False; st.session_state['page'] = 'login'; st.rerun()
    
    st.divider()

    if not st.session_state['show_add_patient']:
        c_search, c_add = st.columns([5, 2], vertical_alignment="bottom")
        search_q = c_search.text_input("Ara", placeholder="Hasta adı veya protokol no...", label_visibility="collapsed")
        
        with c_add:
            if st.button("➕ Yeni Hasta Ekle", type="primary", use_container_width=True):
                st.session_state['show_add_patient'] = True; st.rerun()
        
        st.write("")
        st.markdown("### Hasta Listesi")
        
        patients = st.session_state['patient_db_list']
        if search_q: patients = [p for p in patients if search_q.lower() in p.get('Hasta Adı','').lower()]

        for p in patients:
            with st.container(border=True):
                c_det, c_act = st.columns([6, 1.5], vertical_alignment="center")
                with c_det:
                    tani = p.get('Tanı') if p.get('Tanı') else "Tanı Yok"
                    st.markdown(f"**{p.get('Hasta Adı')}**")
                    st.caption(f"Dosya: {p.get('ID')} | {tani} | {p.get('Tarih')}")
                with c_act:
                    if st.button("Dosyayı Aç", key=p['ID'], use_container_width=True):
                        st.session_state['selected_patient'] = p; st.session_state['page'] = 'framework'; st.rerun()
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
                    new_p = {"ID": prot, "Hasta Adı": name, "Age": age, "Gender": gender, "Tanı": "", "Tarih": pd.Timestamp.now().strftime('%d.%m.%Y'), "Foto": None}
                    st.session_state['patient_db_list'].insert(0, new_p)
                    st.session_state['selected_patient'] = new_p
                    for k in ['sel_struct','sel_func','sel_act','sel_part','sel_env','sel_pers']: st.session_state[k]=[]
                    st.session_state['notes_db']={}; st.session_state['qualifiers_db']={}; st.session_state['current_icd']=None
                    st.session_state['show_add_patient'] = False; st.session_state['page']='framework'; st.rerun()

# --- 6. ICF EDİTÖR ---
def render_edit_mode(hasta):
    c1, c2 = st.columns([1, 8], vertical_alignment="center")
    with c1: 
        if st.button("←", type="secondary"): st.session_state['page']='dashboard'; st.rerun()
    with c2: st.subheader(hasta.get('Hasta Adı', 'Yeni Hasta'))
    
    st.write("")

    # HASTA KARTI
    with st.container(border=True):
        c_img, c_info = st.columns([1, 5], vertical_alignment="center")
        with c_img:
            if hasta.get('Foto'): st.image(hasta['Foto'], width=80)
            else: 
                st.markdown("""<div style="width:80px; height:80px; background-color:#f1f3f5; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#adb5bd; font-weight:bold; border:1px solid #ddd;">FOTO</div>""", unsafe_allow_html=True)
            with st.expander("Yükle"):
                up = st.file_uploader("Seç", type=['png','jpg'], label_visibility="collapsed")
                if up: hasta['Foto'] = up; st.rerun()
        with c_info:
            st.markdown(f"**Dosya No:** {hasta.get('ID')}")
            st.caption(f"Yaş: {hasta.get('Age')} | Cinsiyet: {hasta.get('Gender')} | Tarih: {hasta.get('Tarih')}")

    st.write("")

    # ICD
    with st.container(border=True):
        st.caption("SAĞLIK DURUMU (ICD)")
        cur_idx = 0
        if st.session_state['current_icd'] in DB['ICD']: cur_idx = DB['ICD'].index(st.session_state['current_icd'])
        st.session_state['current_icd'] = st.selectbox("Tanı", DB['ICD'], index=cur_idx, label_visibility="collapsed")

    st.markdown("<div style='text-align:center; color:#ccc; font-size:14px; margin:10px 0;'>⬇</div>", unsafe_allow_html=True)

    # ORTA KATMAN
    c_s, c_b, c_d1, c_d2 = st.columns(4)
    with c_s: render_input_box("Vücut Yapısı (s)", "sel_struct", DB['body_struct'], "#0056b3", "standard")
    with c_b: render_input_box("Vücut Fonk. (b)", "sel_func", DB['body_func'], "#d63384", "standard")
    with c_d1: render_input_box("Aktivite (d)", "sel_act", DB['activity'], "#d39e00", "standard")
    with c_d2: render_input_box("Katılım (d)", "sel_part", DB['participation'], "#c82333", "standard")

    st.markdown("<div style='text-align:center; color:#ccc; font-size:14px; margin:10px 0;'>⬇</div>", unsafe_allow_html=True)

    # ALT KATMAN
    c_e, c_pf = st.columns(2)
    with c_e: render_input_box("Çevresel (e)", "sel_env", DB['env'], "#28a745", "env")
    with c_pf: render_input_box("Kişisel (pf)", "sel_pers", DB['personal'], "#6f42c1", "env")

    st.divider()
    c_x, c_btn, c_y = st.columns([1, 2, 1])
    with c_btn:
        if st.button("🖨️ RAPORU OLUŞTUR & YAZDIR", type="primary", use_container_width=True):
            st.session_state['print_mode'] = True; st.rerun()

def render_input_box(title, state_key, options, color, mode):
    # KUTU RENGİ VE ÇERÇEVESİ
    with st.container(border=True):
        st.markdown(f"<div style='text-align:center; font-weight:700; color:{color}; font-size:14px; margin-bottom:10px;'>{title}</div>", unsafe_allow_html=True)
        
        # NATIVE MULTISELECT (SORUNSUZ ÇALIŞIR)
        sel = st.multiselect("Ekle", options, default=st.session_state[state_key], key=f"ms_{state_key}", label_visibility="collapsed")
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
    if st.button("❌ Kapat", type="secondary"):
        st.session_state['print_mode'] = False; st.rerun()

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
        body {{ font-family: 'Inter', sans-serif; padding: 30px; background: white; color: #333; max-width: 210mm; margin: auto; }}
        .head {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #000; padding-bottom: 20px; margin-bottom: 30px; }}
        .title {{ font-size: 28px; font-weight: 800; color: #000; line-height:1; }}
        .sub {{ font-size: 14px; color: #0056b3; font-weight: 700; margin-top: 5px; }}
        .clinic {{ font-size: 12px; color: #666; text-transform: uppercase; font-weight: 600; letter-spacing: 1px; }}
        .meta {{ font-size:12px; color:#555; margin-top:5px; }}
        .box {{ border: 1px solid #ddd; border-radius: 8px; padding: 12px; background: #fff; height: 100%; box-sizing: border-box; }}
        .bx-t {{ font-size: 12px; font-weight: 700; text-transform: uppercase; border-bottom: 2px solid #eee; padding-bottom: 5px; margin-bottom: 10px; text-align: center; }}
        .hlth {{ border: 2px solid #333; background: #f8f9fa; text-align: center; padding: 10px; border-radius: 8px; width: 50%; margin: 0 auto; }}
        .grid-m {{ display: grid; grid-template-columns: 2fr 0.2fr 1.5fr 0.2fr 1.5fr; gap: 5px; }}
        .grid-b {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 10px; }}
        .grp {{ border: 1px solid #ccc; border-radius: 8px; padding: 5px; background: #fcfcfc; display:flex; flex-direction:column; gap:5px; }}
        .item {{ font-size: 12px; margin-bottom: 6px; }}
        .code {{ font-weight: 700; margin-right: 4px; }}
        .note {{ font-size: 10px; color: #666; background: #f0f0f0; padding: 2px 4px; margin-top: 2px; border-left: 2px solid #ccc; font-style:italic; }}
        .empty {{ font-size: 10px; color: #ccc; text-align: center; }}
        .sub-h {{ font-size: 9px; font-weight: 700; margin-bottom: 3px; }}
        .c-bl {{ color:#0056b3; border-color:#0056b3; }} .c-pk {{ color:#d63384; border-color:#d63384; }}
        .c-or {{ color:#d39e00; border-color:#d39e00; }} .c-rd {{ color:#c82333; border-color:#c82333; }}
        .c-gr {{ color:#28a745; border-color:#28a745; }} .c-pr {{ color:#6f42c1; border-color:#6f42c1; }}
        .legend {{ margin-top: 30px; font-size: 11px; color: #666; text-align: center; border-top: 1px solid #eee; padding-top: 10px; }}
        @media print {{ button {{ display: none; }} body {{ padding: 0; }} }}
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