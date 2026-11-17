"""Dashboard using real LANL authentication logs."""
import streamlit as st
from src.real_dashboard import render
st.set_page_config(page_title="LoginGuard AI", page_icon="🔒", layout="wide", initial_sidebar_state="expanded")
st.navigation([st.Page(lambda: None, title="Dashboard", default=True)], position="hidden")
st.session_state["_single_dashboard"] = True
render()
