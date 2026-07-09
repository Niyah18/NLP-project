import streamlit as st
import gameplan

st.set_page_config(
    page_title="GAMEPLAN – Cricket Strategy Chatbot",
    page_icon="🏏",
    layout="centered"
)

st.title("🏏 GAMEPLAN")
st.subheader("AI-Based Cricket Strategy Chatbot")
st.divider()

# ============================================
# INITIALIZE CHAT HISTORY
# ============================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": """👋 Hello! I'm **GAMEPLAN**, your AI Cricket Strategy Assistant!

I can help you with:
- 🎯 **Best Bowler** → *"Who should bowl against Virat Kohli?"*
- 🏏 **Best Batsman** → *"Who should face Bumrah?"*
- 📊 **Player Stats** → *"Show Rohit Sharma's performance"*

Ask me anything about IPL matchups! 🏆"""
        }
    ]

# ============================================
# DISPLAY CHAT HISTORY
# ============================================

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ============================================
# CHAT INPUT
# ============================================

if prompt := st.chat_input("Ask a cricket strategy question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Analyzing historical IPL matchups..."):
            output = gameplan.process_query(prompt)
        st.code(output)
    st.session_state.messages.append({"role": "assistant", "content": output})

# ============================================
# FOOTER
# ============================================

st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🏏 IPL Ball-by-Ball Data")
with col2:
    st.caption("🤖 NLP Powered")
with col3:
    st.caption("📊 Real Matchup Stats")
