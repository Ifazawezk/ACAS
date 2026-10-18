import streamlit as st
import requests
import os

API_BASE = os.getenv('API_BASE', 'http://127.0.0.1:8000')

st.title('Advanced Comment Analysis - Dashboard (MVP)')

st.sidebar.markdown('## Controls')

if st.sidebar.button('Refresh'):
    st.experimental_rerun()

st.header('KPIs')
try:
    r = requests.get(f"{API_BASE}/dashboard/metrics")
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
