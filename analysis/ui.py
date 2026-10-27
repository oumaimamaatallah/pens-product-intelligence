import streamlit as st

BLUE = "#213DB7"
INK = "#192442"
COLORS = [BLUE, "#0D938A", "#E4A848", "#9B9BC6", "#C97870"]


def setup():
    st.set_page_config(page_title="Pens.com | Product notebook", page_icon="✎", layout="wide")
    st.markdown("""<style>
    [data-testid="stMainBlockContainer"] {padding-top:4.5rem !important; max-width:1530px;}
    .stApp {background:#F4F5F8; color:#192442;}
    h1 {font-size:2.65rem !important; letter-spacing:-.06em; font-weight:650 !important;}
    h2,h3 {letter-spacing:-.035em;}
    [data-testid="stMetric"] {background:white; border:1px solid #E0E4EF; border-radius:14px; padding:20px;}
    [data-testid="stMetricValue"] {font-size:2rem;}
    [data-testid="stPlotlyChart"] {border-radius:14px; border:1px solid #E0E4EF; overflow:hidden;}
    [data-testid="stSidebar"] {background:#fff; border-right:1px solid #E0E4EF;}
    .eyebrow {color:#6F7B94; font-size:12px; font-weight:600; letter-spacing:.17em; margin:0 0 12px;}
    .motion-rule {height:4px; border-radius:3px; background:#213DB7; width:60px; margin-bottom:22px;
       animation:extend .65s ease-out both;}
    @keyframes extend {from {width:0; opacity:0} to {width:60px; opacity:1}}
    [data-testid="stMetric"] {animation:arrive .4s ease-out both;}
    @keyframes arrive {from {opacity:0;transform:translateY(8px)} to {opacity:1;transform:translateY(0)}}
    @media(prefers-reduced-motion:reduce) {*,*::before,*::after {animation:none !important;transition:none !important;}}
    </style>""", unsafe_allow_html=True)


def chart(fig, key, height=340):
    fig.update_layout(template="plotly_white", colorway=COLORS, height=height, font={"family":"Arial","color":INK},
                      paper_bgcolor="white", plot_bgcolor="white", margin={"l":25,"r":25,"t":55,"b":45},
                      title_font_size=15, transition_duration=300, legend_title_text="")
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#EEF0F5", zeroline=False)
    st.plotly_chart(fig, key=key, width="stretch", config={"displaylogo":False})


def metrics(values):
    for col, (label, value, help_text) in zip(st.columns(len(values)), values):
        col.metric(label, value, help=help_text)
