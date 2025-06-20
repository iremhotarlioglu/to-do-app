import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import uuid
import time
from alert import play_alert
import pytz

# Türkiye saat dilimi
TURKEY_TZ = pytz.timezone('Europe/Istanbul')

# Sayfa yapılandırması
st.set_page_config(
    page_title="Reminder App",
    page_icon="✅",
    layout="wide"
)

# Stil tanımlamaları
st.markdown("""
    <style>
    /* Ana tema renkleri */
    .main {
        background-color: #FFF0F5;  /* Açık pembe arka plan */
    }
    
    /* Başlık stilleri */
    h1, h2, h3 {
        color: #C71585;  /* Koyu pembe başlıklar */
        font-weight: bold;
    }
    
    /* Buton stilleri */
    .stButton>button {
        width: 100%;
        background-color: #FF69B4;  /* Pembe butonlar */
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #C71585;  /* Hover durumunda koyu pembe */
    }
    
    /* Görev stilleri */
    .task-completed {
        text-decoration: line-through;
        color: #888;
    }
    
    .deleted-tasks {
        background-color: #FFE4E1;  /* Silinen görevler için açık pembe arka plan */
        padding: 10px;
        border-radius: 5px;
        margin-top: 20px;
        border: 1px solid #FFB6C1;  /* İnce pembe kenarlık */
    }
    
    /* Geri sayım stili */
    .countdown {
        color: #C71585;  /* Koyu pembe geri sayım */
        font-weight: bold;
    }
    
    /* Form elemanları */
    .stTextInput>div>div>input {
        border: 1px solid #FFB6C1;
        border-radius: 5px;
    }
    
    .stDateInput>div>div>input {
        border: 1px solid #FFB6C1;
        border-radius: 5px;
    }
    
    .stTimeInput>div>div>input {
        border: 1px solid #FFB6C1;
        border-radius: 5px;
    }
    
    /* Uyarı mesajları */
    .stAlert {
        background-color: #FFE4E1;
        border: 1px solid #FFB6C1;
    }
    
    /* Checkbox stilleri */
    .stCheckbox>div>div>div {
        color: #C71585;
    }
    
    /* Caption stilleri */
    .stCaption {
        color: #C71585;
    }

    /* Yanıp sönme animasyonu */
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }

    .upcoming-task {
        animation: blink 2s infinite;
        padding: 10px;
        border-radius: 5px;
        background-color: #FFE4E1;
        border: 2px solid #FF69B4;
        margin: 5px 0;
    }

    .urgent-task {
        animation: blink 1s infinite;
        background-color: #FFB6C1;
        border: 2px solid #C71585;
    }

    .time-remaining {
        font-size: 1.2em;
        font-weight: bold;
        color: #C71585;
        margin-top: 5px;
        padding: 5px;
        background-color: rgba(255, 255, 255, 0.5);
        border-radius: 3px;
        display: inline-block;
    }

    .urgent-time {
        color: #FF1493;
        animation: blink 1s infinite;
    }
    </style>
    
    <audio id="alertSound" preload="auto">
        <source src="https://www.soundjay.com/buttons/sounds/button-09.mp3" type="audio/mpeg">
    </audio>
    
    <script>
    function playAlertSound() {
        var audio = document.getElementById('alertSound');
        audio.play();
    }
    </script>
    """, unsafe_allow_html=True)

# Veri yönetimi için yardımcı fonksiyonlar
def load_tasks():
    if os.path.exists('tasks.json'):
        with open('tasks.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    with open('tasks.json', 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

def get_deleted_tasks():
    if 'deleted_tasks' not in st.session_state:
        st.session_state.deleted_tasks = []
    return st.session_state.deleted_tasks

def get_last_alert_time():
    if 'last_alert_time' not in st.session_state:
        st.session_state.last_alert_time = 0
    return st.session_state.last_alert_time

def set_last_alert_time():
    st.session_state.last_alert_time = time.time()

def get_time_remaining(due_date, due_time=None):
    # Şu anki zamanı Türkiye saatine göre al
    now = datetime.now(TURKEY_TZ)
    if due_time is None:
        due_time = "23:59"  # Varsayılan olarak günün sonu
    
    # Bitiş zamanını Türkiye saatine göre oluştur
    due = datetime.strptime(f"{due_date} {due_time}", "%Y-%m-%d %H:%M")
    due = TURKEY_TZ.localize(due)
    
    remaining = due - now
    
    if remaining.total_seconds() <= 0:
        return "Time's up!"
    
    days = remaining.days
    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60
    
    if days > 0:
        return f"{days}g {hours}s {minutes}d kaldı"
    elif hours > 0:
        return f"{hours}s {minutes}d kaldı"
    else:
        return f"{minutes}d kaldı"

def is_urgent(due_date, due_time):
    now = datetime.now(TURKEY_TZ)
    due = datetime.strptime(f"{due_date} {due_time}", "%Y-%m-%d %H:%M")
    due = TURKEY_TZ.localize(due)
    remaining = due - now
    return remaining.total_seconds() <= 3600  # 1 saatten az kaldıysa acil

# Ana uygulama
def main():
    st.title("📝 Reminder App")
    
    # Session state başlatma
    if 'tasks' not in st.session_state:
        st.session_state.tasks = load_tasks()
        # Eski görevler için varsayılan saat ekle
        for task in st.session_state.tasks:
            if "due_time" not in task:
                task["due_time"] = "23:59"
        save_tasks(st.session_state.tasks)
    
    # Yeni görev ekleme
    with st.form("new_task_form"):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            new_task = st.text_input("New Task", placeholder="Enter task description...")
        with col2:
            due_date = st.date_input("Due Date", min_value=datetime.now(TURKEY_TZ).date())
        with col3:
            # Saat seçimi için özel widget
            hour = st.selectbox("Hour", range(24), index=21, key="hour_select")
            minute = st.selectbox("Minute", range(0, 60, 5), index=6, key="minute_select")  # 5'er dakikalık aralıklarla
            due_time = f"{hour:02d}:{minute:02d}"
        
        submitted = st.form_submit_button("Add Task")
        if submitted and new_task:
            new_task_data = {
                "id": str(uuid.uuid4()),
                "task": new_task,
                "completed": False,
                "due_date": due_date.strftime("%Y-%m-%d"),
                "due_time": due_time,
                "created_at": datetime.now(TURKEY_TZ).strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.tasks.append(new_task_data)
            save_tasks(st.session_state.tasks)
            st.rerun()

    # Görevleri görüntüleme
    st.subheader("My Tasks")
    
    # Yaklaşan görevleri kontrol et
    today = datetime.now(TURKEY_TZ).date()
    upcoming_tasks = [task for task in st.session_state.tasks 
                     if not task["completed"] and 
                     datetime.strptime(task["due_date"], "%Y-%m-%d").date() <= today + timedelta(days=3)]
    
    if upcoming_tasks:
        st.warning("⚠️ You have upcoming tasks!")
        for task in upcoming_tasks:
            time_remaining = get_time_remaining(task["due_date"], task.get("due_time"))
            is_task_urgent = is_urgent(task["due_date"], task.get("due_time", "23:59"))
            task_class = "urgent-task" if is_task_urgent else "upcoming-task"
            time_class = "urgent-time" if is_task_urgent else "time-remaining"
            
            st.markdown(f"""
                <div class="{task_class}">
                    <div>📅 {task['task']}</div>
                    <div>Due: {task['due_date']} at {task.get('due_time', '23:59')}</div>
                    <div class="{time_class}">⏰ {time_remaining}</div>
                </div>
            """, unsafe_allow_html=True)
        
        # Sesli uyarı için kontrol
        current_time = time.time()
        if current_time - get_last_alert_time() > 300:  # 5 dakikada bir uyarı ver
            try:
                play_alert()  # Sistem sesi çal
            except:
                st.error("Could not play alert sound")
            set_last_alert_time()

    # Görev listesi
    for task in st.session_state.tasks:
        col1, col2, col3 = st.columns([0.1, 0.7, 0.2])
        
        with col1:
            if st.checkbox("", key=f"check_{task['id']}", value=task["completed"], label_visibility="collapsed"):
                if not task["completed"]:
                    task["completed"] = True
                    save_tasks(st.session_state.tasks)
            else:
                if task["completed"]:
                    task["completed"] = True
                    save_tasks(st.session_state.tasks)
        
        with col2:
            task_style = "task-completed" if task["completed"] else ""
            time_remaining = get_time_remaining(task["due_date"], task.get("due_time"))
            st.markdown(f"<div class='{task_style}'>{task['task']}</div>", unsafe_allow_html=True)
            st.caption(f"Due: {task['due_date']} at {task.get('due_time', '23:59')} ({time_remaining})")
        
        with col3:
            if st.button("🗑️", key=f"delete_{task['id']}"):
                get_deleted_tasks().append(task)
                st.session_state.tasks.remove(task)
                save_tasks(st.session_state.tasks)
                st.rerun()

    # Silinen görevler bölümü
    if get_deleted_tasks():
        st.markdown("---")
        st.subheader("Deleted Tasks")
        st.markdown('<div class="deleted-tasks">', unsafe_allow_html=True)
        
        for i, deleted_task in enumerate(get_deleted_tasks()):
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.markdown(f"~~{deleted_task['task']}~~ - Due: {deleted_task['due_date']} at {deleted_task.get('due_time', '23:59')}")
            with col2:
                if st.button("↩️ Undo", key=f"undo_{deleted_task['id']}"):
                    st.session_state.tasks.append(deleted_task)
                    get_deleted_tasks().pop(i)
                    save_tasks(st.session_state.tasks)
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Sayfayı her 30 saniyede bir otomatik yenile
    time.sleep(30)
    st.rerun()

if __name__ == "__main__":
    main() 