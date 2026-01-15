import streamlit as st
import requests


st.set_page_config(
    page_title="AI Commerce",
    page_icon="🛒",
    layout="wide"
)

BACKEND_URL = "http://localhost:8000/trigger-campaign"
USER_ID = "U001"


def trigger_event(description: str) -> bool:
    payload = {
        "user_id": USER_ID,
        "description": description
    }
    try:
        requests.post(
            BACKEND_URL,
            json=payload,
            timeout=0.5  # short on purpose
        )
        return True
    except requests.exceptions.Timeout:
        # Expected – backend keeps running
        return True
    except Exception:
        return False

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown(
    """
    <h1 style="text-align:center;">🛒 AI Commerce Store</h1>
    <p style="text-align:center;color:gray;">
    Smart shopping powered by AI-driven marketing
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()


with st.sidebar:
    st.markdown("### 🔍 What are you looking for?")
    user_interest = st.text_area(
        "Describe your interest",
        placeholder="e.g. A sweater under ₹5000",
        height=120
    )

    if st.button("Submit", key="submit_interest"):
        if user_interest.strip():
            ok = trigger_event(user_interest)
            if ok:
                st.success("🙏 Thank you for showing your interest!")
            else:
                st.error("❌ Service temporarily unavailable")
        else:
            st.warning("⚠️ Please enter a description")


def product_card(title, price, img_url, key):
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(img_url, width=130)
    with col2:
        st.markdown(f"**{title}**")
        st.markdown(f"💰 ₹{price}")
        st.button(
            "View Product",
            disabled=True,
            key=key
        )

tab_clothes, tab_phones, tab_cameras, tab_cosmetics = st.tabs(
    ["👕 Clothes", "📱 Smartphones", "📷 Cameras", "💄 Cosmetics"]
)

with tab_clothes:
    st.subheader("Trending Clothes")
    product_card(
        "Men's Denim Jacket",
        "2,499",
        "https://via.placeholder.com/150?text=Denim+Jacket",
        "c1"
    )
    product_card(
        "Women's Summer Dress",
        "1,899",
        "https://via.placeholder.com/150?text=Summer+Dress",
        "c2"
    )

with tab_phones:
    st.subheader("Popular Smartphones")
    product_card(
        "Smartphone X Pro",
        "29,999",
        "https://via.placeholder.com/150?text=Smartphone",
        "p1"
    )
    product_card(
        "Budget Phone Lite",
        "14,999",
        "https://via.placeholder.com/150?text=Budget+Phone",
        "p2"
    )

with tab_cameras:
    st.subheader("Top Cameras")
    product_card(
        "DSLR Camera 500D",
        "49,999",
        "https://via.placeholder.com/150?text=DSLR+Camera",
        "ca1"
    )
    product_card(
        "Action Camera Go",
        "18,999",
        "https://via.placeholder.com/150?text=Action+Camera",
        "ca2"
    )

with tab_cosmetics:
    st.subheader("Beauty & Cosmetics")
    product_card(
        "Organic Skincare Kit",
        "1,299",
        "https://via.placeholder.com/150?text=Skincare+Kit",
        "co1"
    )
    product_card(
        "Luxury Makeup Box",
        "2,999",
        "https://via.placeholder.com/150?text=Makeup+Box",
        "co2"
    )

st.divider()
st.markdown(
    """
    <p style="text-align:center;color:gray;">
    © 2026 AI Commerce • Event-Driven Marketing • LangGraph Powered
    </p>
    """,
    unsafe_allow_html=True
)
