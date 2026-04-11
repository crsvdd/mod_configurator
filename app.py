import streamlit as st
import json
import zipfile
import io

# 1. Настройка страницы
st.set_page_config(page_title="Mod Configurator", layout="centered")

# 2. Шрифты и расширенный CSS
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lilita+One&family=Montserrat:wght@900&display=swap');
    
    /* Вертикальное выравнивание для тумблеров */
    [data-testid="column"] {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* Стиль описания для тумблеров */
    .feature-desc {
        font-size: 0.85rem;
        color: #888;
        margin-bottom: 12px;
        margin-top: -8px;
    }

    /* Стиль для описания внутри RADIO_GROUP */
    .radio-desc {
        font-size: 0.8rem;
        color: #888;
        font-weight: 400 !important;
        display: block;
        margin-bottom: 5px;
    }

    /* Убираем стандартный заголовок радио, так как у нас есть свой h2 */
    [data-testid="stWidgetLabel"] {
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
        sample_feat = next(iter(data.get("@features", {}).values()))
        available_langs = list(sample_feat.get("@name", {"EN": "EN"}).keys())
        lang = st.selectbox("Language", available_langs)

        font_family = "'Montserrat', sans-serif" if lang == "RU" else "'Lilita One', cursive"
        font_weight = "900" if lang == "RU" else "400"

        st.markdown(
            f"""
            <style>
            html, body, [class*="css"], stMarkdown, p, h1, h2, h3, label, .stWidgetLabel, [data-testid="stMarkdownContainer"] p {{
                font-family: {font_family} !important;
                font-weight: {font_weight} !important;
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
                        st.markdown(f"<div class='feature-desc'>{f_desc}</div>", unsafe_allow_html=True)
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
                    options_display = []
                    id_to_display = {}
                    default_idx = 0
                    
                    for i, f_id in enumerate(f_ids_in_group):
                        f_info = features.get(f_id, {})
                        name = f_info.get("@name", {}).get(lang, f_id)
                        desc = f_info.get("@description", {}).get(lang, "")
                        
                        # Формируем текст: Название + Описание на новой строке через HTML
                        display_html = f"{name}\n{desc}" if desc else name
                        options_display.append(display_html)
                        id_to_display[display_html] = f_id
                        
                        if f_info.get("@enabled", True):
                            default_idx = i

                    # Радио-кнопка с кастомным рендерингом описания
                    choice = st.radio(
                        g_name,
                        options_display,
                        index=default_idx,
                        key=g_id,
                        # Позволяет использовать \n для переноса в некоторых версиях
                        # Если \n не сработает в браузере, мы добавили стили font-weight
                    )
                    selected_id = id_to_display[choice]

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
                                st.markdown(f"<div class='feature-desc'>{f_desc}</div>", unsafe_allow_html=True)
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
