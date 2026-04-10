import streamlit as st
import json
import zipfile
import io

# Настройка страницы
st.set_page_config(page_title="Null's Brawl Mod Configurator", page_icon="🌵")

def load_mod_data(uploaded_file):
    """Распаковывает архив в памяти и читает content.json"""
    try:
        with zipfile.ZipFile(uploaded_file, 'r') as z:
            if 'content.json' not in z.namelist():
                st.error("Ошибка: В файле мода не найден content.json")
                return None, None
            with z.open('content.json') as f:
                return json.load(f), z.namelist()
    except Exception as e:
        st.error(f"Ошибка при чтении файла: {e}")
        return None, None

st.title("🛠 Настройка мода для iOS")
st.info("Загрузите .NullsBrawlAssets файл, выберите нужные функции и скачайте готовый результат.")

file = st.file_uploader("Выберите файл мода", type=["NullsBrawlAssets", "zip"])

if file:
    data, file_list = load_mod_data(file)
    
    if data:
        # --- 1. ВЫБОР ЯЗЫКА ---
        # Ищем языки в первой попавшейся фиче
        sample_feature = next(iter(data.get("@features", {}).values()))
        available_langs = list(sample_feature.get("@name", {"EN": "EN"}).keys())
        lang = st.selectbox("🌐 Выберите язык / Select language", available_langs)

        new_states = {} # Здесь будем хранить новые значения @enabled

        # --- 2. ГРУППЫ ФУНКЦИЙ (@feature_groups) ---
        if "@feature_groups" in data:
            st.divider()
            for group_id, g_info in data["@feature_groups"].items():
                g_name = g_info.get("@name", {}).get(lang, group_id)
                st.header(f"📦 {g_name}")
                
                f_ids = g_info.get("@features", [])
                options_map = {}
                default_idx = 0
                
                for i, f_id in enumerate(f_ids):
                    f_info = data["@features"].get(f_id, {})
                    f_display = f_info.get("@name", {}).get(lang, f_id)
                    options_map[f_display] = f_id
                    if f_info.get("@enabled") is True:
                        default_idx = i
                
                # Отображаем как Radio (выбор одного)
                choice = st.radio(f"Варианты для: {g_name}", list(options_map.keys()), index=default_idx, key=group_id)
                
                # Записываем состояние: выбранный true, остальные false
                selected_f_id = options_map[choice]
                for f_id in f_ids:
                    new_states[f_id] = (f_id == selected_f_id)

        # --- 3. ОТДЕЛЬНЫЕ ВОЗМОЖНОСТИ (@features) ---
        st.divider()
        st.header("✨ Отдельные возможности")
        
        # Определяем, какие фичи уже в группах, чтобы не дублировать
        grouped_ids = []
        for g in data.get("@feature_groups", {}).values():
            grouped_ids.extend(g.get("@features", []))

        for f_id, f_info in data["@features"].items():
            if f_id in grouped_ids:
                continue
                
            f_name = f_info.get("@name", {}).get(lang, f_id)
            f_desc = f_info.get("@description", {}).get(lang, "")
            is_enabled = f_info.get("@enabled", False)
            
            st.subheader(f_name)
            if f_desc:
                st.caption(f_desc)
            
            # Переключатель (Toggle)
            new_states[f_id] = st.toggle("Включить", value=is_enabled, key=f_id)

        # --- 4. СБОРКА И СКАЧИВАНИЕ ---
        st.divider()
        if st.button("🚀 Подготовить файл к скачиванию", type="primary"):
            # Обновляем JSON в памяти
            for f_id, val in new_states.items():
                if f_id in data["@features"]:
                    data["@features"][f_id]["@enabled"] = val

            # Создаем новый ZIP
            output = io.BytesIO()
            file.seek(0)
            with zipfile.ZipFile(file, 'r') as old_zip:
                with zipfile.ZipFile(output, 'w') as new_zip:
                    for item in old_zip.infolist():
                        if item.filename == 'content.json':
                            # Записываем наш новый JSON
                            new_zip.writestr('content.json', json.dumps(data, indent=4, ensure_ascii=False))
                        else:
                            # Копируем всё остальное без изменений
                            new_zip.writestr(item, old_zip.read(item.filename))
            
            st.success("Готово! Нажмите кнопку ниже для сохранения.")
            st.download_button(
                label="📥 Скачать настроенный мод",
                data=output.getvalue(),
                file_name="Mod_for_iOS.zip",
                mime="application/zip"
            )