import streamlit as st
import ollama
import re

st.set_page_config(page_title="Ollama Chat", layout="wide")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("💬 Live Thinking Chat")

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()

def is_thinking_complete(text):
    """Check if thinking process is complete"""
    return '</think>' in text

def extract_current_thinking(text):
    """Extract current thinking content"""
    if '<think>' in text:
        thinking = text.split('<think>')[1]
        if '</think>' in thinking:
            thinking = thinking.split('</think>')[0]
        return thinking.strip()
    return ""

def get_response_after_thinking(text):
    """Get text after </think> tag"""
    parts = text.split('</think>')
    if len(parts) > 1:
        return parts[1].strip()
    return ""

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            thinking = extract_current_thinking(message["content"])
            response = get_response_after_thinking(message["content"])
            if thinking:
                with st.expander("✨ Thinking completed", expanded=False):
                    st.markdown(thinking)
            if response:
                st.markdown(response)
        else:
            st.markdown(message["content"])

# User input and response generation
if prompt := st.chat_input("What would you like to know?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_response = ""
        thinking_complete = False
        thinking_placeholder = st.empty()
        response_placeholder = st.empty()
        temp_response = ""
        
        # Stream the response
        for chunk in ollama.chat(
            model="deepseek-r1:1.5b",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        ):
            if chunk['message']['content']:
                full_response += chunk['message']['content']
                current_thinking = extract_current_thinking(full_response)
                
                # If we're in thinking phase
                if current_thinking:
                    # Show live thinking with expanded box while in progress
                    if not thinking_complete:
                        with thinking_placeholder.expander("🤔 Thinking in progress...", expanded=True):
                            st.markdown(current_thinking + "▌")
                    
                    # When thinking is complete
                    if is_thinking_complete(full_response) and not thinking_complete:
                        with thinking_placeholder.expander("✨ Thinking completed", expanded=False):
                            st.markdown(current_thinking)
                        thinking_complete = True
                        
                # Show response after thinking is complete
                if thinking_complete:
                    temp_response = get_response_after_thinking(full_response)
                    if temp_response:
                        response_placeholder.markdown(temp_response + "▌")
        
        # Final update without cursor
        if temp_response:
            response_placeholder.markdown(temp_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})