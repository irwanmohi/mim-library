import streamlit as st
from pathlib import Path

LOGO_PATH = Path(__file__).parent / "assets" / "logo.png"


def render_sidebar():
    if LOGO_PATH.exists():
        st.sidebar.image(str(LOGO_PATH), width=160)
    st.sidebar.title("MIM Library")
    st.sidebar.caption("Library Management System")
    st.sidebar.divider()
    st.sidebar.markdown("""
        <div style='text-align:center; color:#888; font-size:0.78rem; line-height:1.6;'>
            <em>Created &amp; Designed by</em><br>
            <strong style='color:#ccc;'>Mohd Irwan bin Mohi</strong><br>
            <code>B25090011</code><br><br>
            <strong style='color:#ccc;'>Izzat Dhiyauddin bin Zainuddin</strong><br>
            <code>B25080294</code>
        </div>
    """, unsafe_allow_html=True)


def render_footer():
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    st.markdown("""
        <div style='text-align:center; color:#666; font-size:0.80rem; padding:0.5rem 0 1rem 0;'>
            <strong style='color:#888;'>Mohd Irwan bin Mohi</strong> <code>B25090011</code>
            &nbsp;&amp;&nbsp;
            <strong style='color:#888;'>Izzat Dhiyauddin bin Zainuddin</strong> <code>B25080294</code>
            &nbsp;|&nbsp; MIM Library &copy; 2026
        </div>
    """, unsafe_allow_html=True)
