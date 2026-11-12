import pandas as pd
import streamlit as st
from queries import (
    GET_GAP_ANALYSIS,
    GET_LEARNING_PATH,
    GET_MARKET_STATS,
    GET_MENTORS,
    GET_PEERS,
    GET_STUDENT_PROFILE,
    GET_STUDENTS,
)

from database import get_connection, test_connection

st.set_page_config(
    page_title="SkillMap — Карьерный трек",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("Подключение к Neo4j")

uri = st.sidebar.text_input("URI", value="bolt://localhost:7687")
user = st.sidebar.text_input("Пользователь", value="neo4j")
password = st.sidebar.text_input("Пароль", type="password", value="qwertyuiop")

if 'conn' not in st.session_state:
    st.session_state['conn'] = None

if st.sidebar.button("Подключиться"):
    try:
        conn = get_connection(uri, user, password)
        if test_connection(conn):
            st.session_state['conn'] = conn
            st.sidebar.success("Подключено!")
            st.rerun()
        else:
            st.sidebar.error("Не удалось подключиться к Neo4j")
            st.session_state['conn'] = None
    except Exception as e:
        st.sidebar.error(f"Ошибка подключения: {e}")
        st.session_state['conn'] = None

conn = st.session_state.get('conn')

if conn is None:
    st.title("SkillMap")
    st.info("Укажите параметры подключения к Neo4j в боковой панели и нажмите «Подключиться»")
    st.markdown("""
    Инструкция:
    1. Убедитесь, что Neo4j запущен
    2. Введите правильные параметры подключения (по умолчанию: `bolt://localhost:7687`, пользователь `neo4j`)
    3. Нажмите кнопку **«Подключиться»**
    """)
    st.stop()

st.title("SkillMap")
st.markdown("**Персональный карьерный трек на основе графа знаний**")

students = []
try:
    students = conn.query(GET_STUDENTS)
except Exception as e:
    st.error(f"Ошибка выполнения запроса: {e}")
    st.session_state['conn'] = None
    st.stop()

if not students:
    st.warning("В базе нет студентов. Запустите скрипт создания данных в Neo4j Browser.")
    st.stop()

student_names = {f"{s['name']} → {s['goal']}": s['id'] for s in students}
options = list(student_names.keys())

selected_label = st.selectbox("Выберите студента", options, index=0)

if selected_label is None:
    st.stop()

student_id = student_names[selected_label]

st.divider()


tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Профиль",
    "Gap Analysis",
    "План обучения",
    "Менторы",
    "Единомышленники",
    "Рынок"
])

with tab1:
    profile = []
    try:
        profile = conn.query(GET_STUDENT_PROFILE, {"student_id": student_id})
    except Exception as e:
        st.error(f"Ошибка загрузки профиля: {e}")

    if profile:
        p = profile[0]
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Студент", p['name'])
            st.metric("Цель", p['goal'])
        with col2:
            st.metric("Пройдено курсов", len(p['courses']))
            st.metric("Освоено навыков", len(p['skills']))

        st.subheader("🎓 Пройденные курсы")
        if p['courses']:
            st.write(" • ".join(p['courses']))
        else:
            st.info("Пока нет пройденных курсов")

        st.subheader("💡 Освоенные навыки")
        if p['skills']:
            st.write(" • ".join(p['skills']))
        else:
            st.info("Пока нет освоенных навыков")

with tab2:
    st.subheader("Чего не хватает до цели?")
    gaps = []
    try:
        gaps = conn.query(GET_GAP_ANALYSIS, {"student_id": student_id})
    except Exception as e:
        st.error(f"Ошибка анализа пробелов: {e}")

    if gaps:
        df = pd.DataFrame(gaps)
        df.columns = ["Навык", "Приоритет"]

        st.dataframe(df, use_container_width=True, hide_index=True)
        st.info(f"Нужно освоить **{len(gaps)}** навыков: "
                f"**{sum(1 for g in gaps if g['priority'] == 'must')}** обязательных, "
                f"**{sum(1 for g in gaps if g['priority'] == 'nice')}** желательных")
    else:
        st.success("Поздравляем! Все необходимые навыки уже освоены!")

with tab3:
    st.subheader("Персональный план обучения")
    paths = []
    try:
        paths = conn.query(GET_LEARNING_PATH, {"student_id": student_id})
    except Exception as e:
        st.error(f"Ошибка построения плана: {e}")

    if paths:
        for p in paths:
            with st.expander(f"**{p['skill']}** — {p['hours']} ч. / {p['price']:,} ₽"):
                st.markdown("**Путь обучения:**")
                for i, course in enumerate(p['path'], 1):
                    st.markdown(f"{i}. {course}")
    else:
        st.info("Нет данных для построения плана")

with tab4:
    st.subheader("Рекомендуемые менторы")
    mentors = []
    try:
        mentors = conn.query(GET_MENTORS, {"student_id": student_id})
    except Exception as e:
        st.error(f"Ошибка загрузки менторов: {e}")

    if mentors:
        for m in mentors:
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.markdown(f"### {m['mentor']}")
                    st.caption(f"{m['company']} · {m['experience']} лет опыта")
                with col2:
                    st.markdown("**Знает нужные навыки:**")
                    st.write(", ".join(m['skills']))
                with col3:
                    st.metric("Ставка", f"{m['rate']} ₽/ч")
                    st.metric("Совпадений", m['matches'])
                st.divider()
    else:
        st.info("Менторы из целевой компании не найдены")

with tab5:
    st.subheader("Студенты с похожими целями")
    peers = []
    try:
        peers = conn.query(GET_PEERS, {"student_id": student_id})
    except Exception as e:
        st.error(f"Ошибка загрузки единомышленников: {e}")

    if peers:
        for p in peers:
            st.markdown(f"**{p['peer']}** — {p['goal']}")
            st.caption("Общие навыки: " + ", ".join(p['skills']))
    else:
        st.info("Пока нет студентов с такими же целями")

with tab6:
    st.subheader("Самые востребованные навыки")
    stats = []
    try:
        stats = conn.query(GET_MARKET_STATS)
    except Exception as e:
        st.error(f"Ошибка загрузки статистики: {e}")

    if stats:
        df = pd.DataFrame(stats)
        df.columns = ["Навык", "Всего вакансий", "Обязательных", "Желательных"]

        col1, col2 = st.columns(2)
        with col1:
            st.bar_chart(df.set_index("Навык")["Всего вакансий"])
        with col2:
            st.dataframe(df, use_container_width=True, hide_index=True)