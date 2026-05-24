"""
ARVIN — Arvind Limited HR Policy Chatbot
Run: streamlit run app.py
"""

import os
import streamlit as st
from dotenv import load_dotenv
from rag import stream_answer

load_dotenv()

st.set_page_config(
    page_title="ARVIN | HR Policy Assistant",
    page_icon="🏢",
    layout="centered",
)

# --- Sidebar ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Arvind_Limited_Logo.svg/320px-Arvind_Limited_Logo.svg.png", width=160)
    st.markdown("## ARVIN")
    st.markdown("**Arvind Limited HR Policy Assistant**")
    st.divider()
    st.markdown("**Policies covered:**")
    policies = [
        "📄 Local Conveyance Policy",
        "✈️ Domestic Travel Policy",
        "⚖️ Gender Policy 2025",
        "📢 Grievance Mechanism Policy",
        "🛡️ POSH Policy",
        "🔄 Talent Mobility Policy",
        "🔔 Whistleblower Policy",
        "🤝 Joining Policy",
    ]
    for p in policies:
        st.markdown(f"- {p}")
    st.divider()
    st.markdown("**Need HR support?**")
    st.markdown("📞 Ethics Helpline: `1800 200 8301`")
    st.markdown("🌐 [Ethics Web Portal](https://www.in.kpmg.com/ethicshelpline/arvind)")
    st.markdown("📧 arvind@ethicshelpline.in")
    st.divider()
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.rerun()

# --- Header ---
st.title("ARVIN — HR Policy Assistant")
st.caption("Ask me anything about Arvind Limited's HR policies. I'll answer based on official policy documents.")

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Check if vectorstore exists
vectorstore_ready = os.path.exists("vectorstore") and any(
    f for f in os.listdir("vectorstore") if not f.startswith(".")
) if os.path.exists("vectorstore") else False

if not vectorstore_ready:
    st.warning(
        "**Policy database not built yet.** Run `python ingest.py` first to index all policy documents.",
        icon="⚠️",
    )

# --- Suggested questions ---
if not st.session_state.messages:
    st.markdown("**Quick questions to get started:**")
    suggestions = [
        "What is the reimbursement rate for local conveyance using my personal car?",
        "How do I raise a grievance at Arvind?",
        "What is the domestic travel booking process?",
        "What counts as sexual harassment under the POSH policy?",
        "What is the talent mobility / job rotation policy?",
    ]
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        if cols[i % 2].button(suggestion, use_container_width=True):
            st.session_state.pending_question = suggestion
            st.rerun()

# Handle pending question from button click
if "pending_question" in st.session_state:
    prompt = st.session_state.pop("pending_question")
    st.session_state.messages.append({"role": "user", "content": prompt})

# --- Display chat history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🏢"):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📋 Policy sources cited", expanded=False):
                for src in msg["sources"]:
                    st.markdown(f"- **{src['policy']}** (page {src['page']})")

# --- Chat input ---
if prompt := st.chat_input("Ask about any HR policy…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

# Process last user message if no assistant response yet
if (
    st.session_state.messages
    and st.session_state.messages[-1]["role"] == "user"
    and vectorstore_ready
):
    prompt = st.session_state.messages[-1]["content"]

    with st.chat_message("assistant", avatar="🏢"):
        response_placeholder = st.empty()
        full_response = ""
        sources = []

        with st.spinner("Searching policies…"):
            for chunk in stream_answer(prompt, st.session_state.chat_history):
                if isinstance(chunk, dict) and "sources" in chunk:
                    sources = chunk["sources"]
                else:
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")

        response_placeholder.markdown(full_response)

        if sources:
            with st.expander("📋 Policy sources cited", expanded=True):
                for src in sources:
                    st.markdown(f"- **{src['policy']}** (page {src['page']})")

    # Save to session
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "sources": sources,
    })
    # Keep last 6 turns in chat history for Claude context
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
    st.session_state.chat_history = st.session_state.chat_history[-12:]
