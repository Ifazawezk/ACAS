import streamlit as st
import requests
import os

API_BASE = os.getenv('API_BASE', 'http://127.0.0.1:8000')

st.title('Advanced Comment Analysis - Dashboard (MVP)')

st.sidebar.markdown('## Controls')

if st.sidebar.button('Refresh'):
    st.experimental_rerun()


def log_in():
    username = st.sidebar.text_input('Username')
    password = st.sidebar.text_input('Password', type='password')
    if st.sidebar.button('Log in'):
        r = requests.post(f"{API_BASE}/auth/token", json={'username': username, 'password': password}, timeout=10)
        if r.ok:
            st.session_state['token'] = r.json()['access_token']
            st.experimental_rerun()
        st.sidebar.error('Login failed')
    st.info('Log in from the sidebar to see the dashboard.')
    st.stop()


if 'token' not in st.session_state:
    log_in()

st.header('KPIs')
try:
    r = requests.get(
        f"{API_BASE}/dashboard/metrics",
        headers={'Authorization': f"Bearer {st.session_state['token']}"},
        timeout=10,
    )
    if r.status_code == 401:
        del st.session_state['token']
        st.experimental_rerun()
    r.raise_for_status()
    data = r.json()
except Exception as e:
    st.error(f"Failed to fetch metrics: {e}")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric('Total comments', data['total_comments'])
col2.metric('% Negative', f"{data['pct_negative']*100:.1f}%")
col3.metric('High priority tickets', data['high_priority_tickets'])

st.subheader('Sentiment distribution')
import pandas as pd
sent = pd.DataFrame(data['sentiment_distribution'])
if not sent.empty:
    st.bar_chart(sent.set_index('emotion'))

st.subheader('Priority distribution')
prio = pd.DataFrame(data['priority_distribution'])
if not prio.empty:
    st.bar_chart(prio.set_index('priority'))

st.subheader('Top complaint')
st.write(data.get('top_complaint') or 'N/A')

st.subheader('Ticket status breakdown')
stat = pd.DataFrame(data['ticket_status_breakdown'])
if not stat.empty:
    st.bar_chart(stat.set_index('status'))
