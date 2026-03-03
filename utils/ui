import streamlit as st

def apply_base_style(app_title: str | None = None) -> None:
    """Apply a simple, clean style to make the app look more like a polished student project."""
    st.markdown(
        """
        <style>
          /* Layout */
          .block-container { padding-top: 2rem; padding-bottom: 2.5rem; max-width: 1180px; }
          /* Typography */
          h1, h2, h3 { letter-spacing: -0.2px; }
          [data-testid="stMetricValue"] { font-size: 1.6rem; }
          .muted { color: rgba(49, 51, 63, 0.72); font-size: 0.95rem; }
          .badge { display:inline-block; padding:0.15rem 0.55rem; border-radius: 999px; background:#f1f3f6; }

          /* Hide Streamlit chrome for a cleaner look */
          #MainMenu { visibility: hidden; }
          footer { visibility: hidden; }
          header { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if app_title:
        st.markdown(f"<div class='muted'>{app_title}</div>", unsafe_allow_html=True)
