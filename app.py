import streamlit as st
import json
import zipfile
import io

# 1. Настройка страницы
st.set_page_config(page_title="Mod Configurator", layout="centered")

# 2. ПОДКЛЮЧЕНИЕ ШРИФТОВ И ГЛОБАЛЬНЫЙ CSS С АНИМАЦИЯМИ
st.markdown(
    """
    <style>
    /* Подключаем шрифты из Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Lilita+One&family=Montserrat:wght@400;900&display=swap');
    
    /* 1. ГЛОБАЛЬНЫЙ ЖЕСТКИЙ ШРИФТ (Montserrat/Pusia для RU, Lilita для EN)
       Применяем ко ВСЕМ элементам: кнопкам, инпутам, текстам */
    html, body, [class*="css"], stMarkdown, p, h1, h2, h3, label, 
    .stWidgetLabel, .stButton>button, .stselectbox, .stToggle, 
    [data-testid="stMarkdownContainer"] p, [data-testid="stText"] {
        /* Этот шрифт будет базовым, ниже мы переопределим его для RU */
        font-family: 'Lilita One', cursive !important;
        font-weight: 400 !important;
    }

    /* 2. ПЛАВНЫЕ АНИМАЦИИ (CSS Transitions)
       Применяем ко всем элементам, которые меняют состояние */
    * {
        transition: all 0.3s ease-in-out !important;
    }

    /* Специальные настройки для элементов, чтобы они плавно загорались */
    .stToggle>div { transition: background-color 0.3s ease !important; }
    .stButton>button { transition: transform 0.2s ease, background-color 0.3s ease !important; }
    .stButton>button:hover { transform: scale(1.02); }

    /* 3. СТИЛИ ДЛЯ ОПИСАНИЙ В RADIO_GROUP С АНИМАЦИЕЙ СМЕНЫ */
    [data-testid="column"] {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* Обычное описание (полупрозрачное) */
    .desc-normal {
        font-size: 0.85rem;
        color: #888;
        font-weight: 400 !important;
        margin-bottom: 8px;
        opacity: 0.5; /* Изначально скрыто/бледное */
        padding-left: 8px;
        border-left: 3px solid transparent;
        /* Плавное изменение прозрачности и границы */
        transition: opacity 0.3s ease, color 0.3s ease, border-left 0.3s ease !important;
    }

    /* Жирное описание для выбранного пункта (плавно загорается) */
    .desc-active {
        font-size: 0.9rem;
        color: #000;
        font-weight: 900 !important;
        margin-bottom: 8px;
        padding-left: 8px;
        border-left: 3px solid #FF4B4B; /* Акцентная полоска */
        opacity: 1 !important; /* Полностью видимое */
        /* Плавное появление */
        animation: fadeIn 0.4s ease-in-out;
    }

    /* Анимация появления для активного описания */
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(5px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    /* Убираем лишние отступы */
    .stRadio > label {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def load_mod_data(uploaded_file):
    try:
        with zipfile.ZipFile(uploaded_file, 'r') as z:
            if 'content.json' not in z.namelist():
                st.error("content.json not found")
                return None
            with z.open('content.json') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error: {e}")
        return None

file = st.file_uploader("Выберите файл .NullsBrawlAssets", type=["NullsBrawlAssets", "zip"])

if file:
    data = load_mod_data(file)
    
    if data:
        # 3. ОПРЕДЕЛЕНИЕ ЯЗЫКА И ГЛОБАЛЬНАЯ СМЕНА ШРИФТА (ЖЕСТКО)
        sample_feat = next(iter(data.get("@features", {}).values()))
        available_langs = list(sample_feat.get("@name", {"EN": "EN"}).keys())
        lang = st.selectbox("Language", available_langs)

        # Выбираем шрифт (Montserrat ExtraBold/Black для RU)
        font_family = "'Montserrat', sans-serif" if lang == "RU" else "'Lilita One', cursive"
        font_weight = "900" if lang == "RU" else "400"
        
        # Этот блок принудительно ставит нужный шрифт для выбранного языка ко ВСЕМУ
        st.markdown(
            f"""
            <style>
            html, body, [class*="css"], stMarkdown, p, h1, h2, h3, label, .stWidgetLabel,
            .stButton>button, .stselectbox, .stToggle, [data-testid="stMarkdownContainer"] p,
            [data-testid="stText"], input, select, textarea, span {{
                font-family: {font_family} !important;
                font-weight: {font_weight} !important;
            }}
            /* Дополнительно для описаний в RADIO, чтобы вес шрифта не сбрасывался */
            .desc-active {{
                font-weight: 900 !important;
            }}
            .desc-normal {{
                font-weight: 400 !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

        new_states = {}
        features = data.get("@features", {})
        groups = data.get("@feature_groups", {})

        grouped_f_ids = []
        for g_info in groups.values():
            grouped_f_ids.extend(g_info.get("@features", []))

        # --- 1. ОТДЕЛЬНЫЕ ВОЗМОЖНОСТИ ---
        st.header("Отдельные возможности" if lang == "RU" else "Individual Features")
        
        for f_id, f_info in features.items():
            if f_id not in grouped_f_ids and "@type" not in f_info:
                f_name = f_info.get("@name", {}).get(lang, f_id)
                f_desc = f_info.get("@description", {}).get(lang, "")
                is_enabled = f_info.get("@enabled", True)

                col_text, col_toggle = st.columns([0.85, 0.15])
                with col_text:
                    st.markdown(f"**{f_name}**")
                    if f_desc:
                        # Описание для тумблеров — всегда полупрозрачное, но шрифт жесткий
                        st.markdown(f"<div class='desc-normal' style='opacity:0.8; border-left:transparent; padding-left:0;'>{f_desc}</div>", unsafe_allow_html=True)
                with col_toggle:
                    new_states[f_id] = st.toggle("", value=is_enabled, key=f_id, label_visibility="collapsed")

        # --- 2. ГРУППЫ ФУНКЦИЙ ---
        if groups:
            for g_id, g_info in groups.items():
                st.markdown("---")
                g_name = g_info.get("@name", {}).get(lang, g_id)
                st.header(g_name)
                
                f_ids_in_group = g_info.get("@features", [])
                
                if g_info.get("@type") == "RADIO_GROUP":
                    options_names = []
                    id_map = {}
                    default_idx = 0
                    
                    for i, f_id in enumerate(f_ids_in_group):
                        name = features[f_id].get("@name", {}).get(lang, f_id)
                        options_names.append(name)
                        id_map[name] = f_id
                        if features[f_id].get("@enabled", True):
                            default_idx = i

                    # Блок выбора (кнопка, которая запускает анимацию описаний снизу)
                    choice = st.radio(g_name, options_names, index=default_idx, key=g_id)
                    selected_id = id_map[choice]

                    # Блок описаний под выбором (С АНИМАЦИЕЙ)
                    st.write("") # Отступ
                    for f_id in f_ids_in_group:
                        f_info = features.get(f_id, {})
                        desc = f_info.get("@description", {}).get(lang, "")
                        if desc:
                            # ПЛАВНАЯ СМЕНА КЛАССОВ: если этот ID выбран — применяется .desc-active
                            # CSS transition в начале кода заставляет эту смену происходить плавно
                            style_class = "desc-active" if f_id == selected_id else "desc-normal"
                            st.markdown(f"<div class='{style_class}'>{desc}</div>", unsafe_allow_html=True)

                    for f_id in f_ids_in_group:
                        new_states[f_id] = (f_id == selected_id)
                
                else:
                    for f_id in f_ids_in_group:
                        f_info = features.get(f_id, {})
                        f_name = f_info.get("@name", {}).get(lang, f_id)
                        f_desc = f_info.get("@description", {}).get(lang, "")
                        
                        col_t, col_b = st.columns([0.85, 0.15])
                        with col_t:
                            st.markdown(f"**{f_name}**")
                            if f_desc:
                                st.markdown(f"<div class='desc-normal' style='opacity:0.8; border-left:transparent; padding-left:0;'>{f_desc}</div>", unsafe_allow_html=True)
                        with col_b:
                            new_states[f_id] = st.toggle("", value=f_info.get("@enabled", True), key=f_id, label_visibility="collapsed")

        # --- КНОПКА СКАЧИВАНИЯ ---
        st.divider()
        if st.button("Применить и скачать" if lang == "RU" else "Apply and Download", type="primary"):
            for f_id, val in new_states.items():
                if f_id in data["@features"]:
                    data["@features"][f_id]["@enabled"] = val

            output = io.BytesIO()
            file.seek(0)
            with zipfile.ZipFile(file, 'r') as old_zip:
                with zipfile.ZipFile(output, 'w') as new_zip:
                    for item in old_zip.infolist():
                        if item.filename == 'content.json':
                            new_zip.writestr('content.json', json.dumps(data, indent=4, ensure_ascii=False))
                        else:
                            new_zip.writestr(item, old_zip.read(item.filename))
            
            st.success("Готово" if lang == "RU" else "Ready")
            st.download_button(
                label="Скачать файл" if lang == "RU" else "Download File",
                data=output.getvalue(),
                file_name="mod.NullsBrawlAssets",
                mime="application/octet-stream"
            )
