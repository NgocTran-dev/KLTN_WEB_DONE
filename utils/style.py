from pathlib import Path
import streamlit as st

def inject_css() -> None:
    """Inject local CSS to make the UI look more consistent/professional."""
    css_path = Path(__file__).resolve().parents[1] / "assets" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)