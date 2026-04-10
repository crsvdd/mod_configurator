import streamlit as st
import json
import zipfile
import io

st.set_page_config(page_title="Mod Configurator")

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
        # Определение языка
        sample_feat = next(iter(data.get("@features", {}).values()))
        available_langs = list(sample_feat.get("@name", {"EN": "EN"}).keys())
        lang = st.selectbox("Language", available_langs)

        new_states = {}
        features = data.get("@features", {})
        groups = data.get("@feature_groups", {})

        # Собираем список всех фич, которые входят в группы
        grouped_f_ids = []
        for g_info in groups.values():
            grouped_f_ids.extend(g_info.get("@features", []))

        # --- 1. ОТДЕЛЬНЫЕ ВОЗМОЖНОСТИ (ВСЕГДА ВВЕРХУ) ---
        st.header("Отдельные возможности")
        for f_id, f_info in features.items():
            # Если у фичи нет @type и она не в группе — это отдельный тумблер
            if f_id not in grouped_f_ids and "@type" not in f_info:
                f_name = f_info.get("@name", {}).get(lang, f_id)
                f_desc = f_info.get("@description", {}).get(lang, "")
                is_enabled = f_info.get("@enabled", False)

                # Создаем две колонки: для текста и для тумблера справа
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.write(f"**{f_name}**")
                    if f_desc:
                        st.caption(f_desc)
                with col2:
                    new_states[f_id] = st.toggle("", value=is_enabled, key=f_id, label_visibility="collapsed")

        # --- 2. ГРУППЫ ФУНКЦИЙ (НИЖЕ) ---
        if groups:
            st.markdown("---")
            for g_id, g_info in groups.items():
                g_name = g_info.get("@name", {}).get(lang, g_id)
                st.header(g_name)
                
                f_ids_in_group = g_info.get("@features", [])
                options_map = {}
                default_idx = 0
                
                for i, f_id in enumerate(f_ids_in_group):
                    f_info = features.get(f_id, {})
                    f_display = f_info.get("@name", {}).get(lang, f_id)
                    options_map[f_display] = f_id
                    if f_info.get("@enabled") is True:
                        default_idx = i
                
                if g_info.get("@type") == "RADIO_GROUP":
                    choice = st.radio(f"Выбор для {g_name}:", list(options_map.keys()), index=default_idx, key=g_id)
                    selected_id = options_map[choice]
                    for f_id in f_ids_in_group:
                        new_states[f_id] = (f_id == selected_id)
                else:
                    # Если вдруг в группе не RADIO_GROUP, выводим тумблерами
                    for f_id in f_ids_in_group:
                        f_info = features.get(f_id, {})
                        f_name = f_info.get("@name", {}).get(lang, f_id)
                        new_states[f_id] = st.toggle(f_name, value=f_info.get("@enabled", False), key=f_id)

        # --- СБОРКА ---
        st.divider()
        if st.button("Применить и скачать"):
            # Обновляем JSON
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
            
            st.download_button(
                label="Скачать настроенный мод",
                data=output.getvalue(),
                file_name="mod.NullsBrawlAssets",
                mime="application/octet-stream"
            )
