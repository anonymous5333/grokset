import streamlit as st
import json
import pandas as pd
import os
import html

st.set_page_config(layout="wide", page_title="Conversation Annotation")

SAMPLE_FILE = "annotation_sample.json"
OUTPUT_FILE = "human_annotations.csv"

@st.cache_data
def load_data():
    if not os.path.exists(SAMPLE_FILE):
        st.error(f"Sample file not found at {SAMPLE_FILE}. Please run sample_conversations.py first.")
        return []
    with open(SAMPLE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

conversations = load_data()

if not conversations:
    st.stop()

if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0

idx = st.session_state.current_idx
conv = conversations[idx]
conv_id = str(conv.get("conversationId", ""))

def auto_save():
    data = {
        "conversationId": conv_id,
        "is_discussion": st.session_state.get(f"is_discussion_{conv_id}") or "NA",
        "discussion_intensity": st.session_state.get(f"discussion_intensity_{conv_id}") if st.session_state.get(f"discussion_intensity_{conv_id}") is not None else "NA",
        "discussion_type": ", ".join(st.session_state.get(f"discussion_type_{conv_id}", [])) if st.session_state.get(f"discussion_type_{conv_id}") else "NA",
        "bias_language": st.session_state.get(f"bias_language_{conv_id}") or "NA",
        "assistant_bias": ", ".join(st.session_state.get(f"assistant_bias_{conv_id}", [])) if st.session_state.get(f"assistant_bias_{conv_id}") else "NA",
        "bias_intensity": st.session_state.get(f"bias_intensity_{conv_id}") if st.session_state.get(f"bias_intensity_{conv_id}") is not None else "NA",
        "assistant_stance": st.session_state.get(f"assistant_stance_{conv_id}") or "NA",
        "assistant_stance_bias": ", ".join(st.session_state.get(f"assistant_stance_bias_{conv_id}", [])) if st.session_state.get(f"assistant_stance_bias_{conv_id}") else "NA",
        "user_response_type": st.session_state.get(f"user_response_type_{conv_id}") or "NA"
    }
    
    df_new = pd.DataFrame([data])
    if os.path.exists(OUTPUT_FILE):
        try:
            df_existing = pd.read_csv(OUTPUT_FILE)
            df_existing = df_existing[df_existing['conversationId'].astype(str) != conv_id]
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        except pd.errors.EmptyDataError:
            df_combined = df_new
    else:
        df_combined = df_new
        
    df_combined.to_csv(OUTPUT_FILE, index=False)

# Look up existing data for this conv_id to restore state
existing_data = {}
if os.path.exists(OUTPUT_FILE):
    try:
        df = pd.read_csv(OUTPUT_FILE)
        df['conversationId'] = df['conversationId'].astype(str)
        row = df[df['conversationId'] == conv_id]
        if not row.empty:
            existing_data = row.iloc[0].fillna("NA").to_dict()
    except pd.errors.EmptyDataError:
        pass

def get_idx(options, val):
    if pd.isna(val) or val == "NA": return None
    # handle float values for intensity gracefully
    try: 
        if isinstance(val, str) and val.isdigit(): val = int(val)
        elif isinstance(val, float): val = int(val)
    except: pass
    return options.index(val) if val in options else None

def get_list(val):
    if pd.isna(val) or val == "NA" or not val: return []
    return [x.strip() for x in str(val).split(",")]

st.title(f"Conversation Annotation ({st.session_state.current_idx + 1} / {len(conversations)})")

progress = (st.session_state.current_idx + 1) / len(conversations)
st.progress(progress)

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("⬅️ Previous"):
        if st.session_state.current_idx > 0:
            st.session_state.current_idx -= 1
            st.rerun()

with col2:
    if st.button("Next ➡️"):
        if st.session_state.current_idx < len(conversations) - 1:
            st.session_state.current_idx += 1
            st.rerun()

with col3:
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "rb") as file:
            st.download_button(
                label="📥 Download Current Results (CSV)",
                data=file,
                file_name="human_annotations.csv",
                mime="text/csv"
            )

st.divider()

left_col, right_col = st.columns([1.5, 1])

with left_col:
    st.subheader(f"Conversation ID: {conv_id}")
    
    thread_url = None
    if 'threads' in conv and len(conv['threads']) > 0:
        first_thread = conv['threads'][0]
        if 'tweets' in first_thread and len(first_thread['tweets']) > 0:
            thread_url = first_thread['tweets'][0].get('twitterUrl') or first_thread['tweets'][0].get('url')
            
    if thread_url:
        st.markdown(f"**[🔗 Link to original thread]({thread_url})**")
    
    st.markdown("### Thread Messages")
    
    messages = []
    seen = set()
    if 'threads' in conv:
        for thread in conv.get('threads', []):
            for tweet in thread.get('tweets', []):
                text = tweet.get('text', '')
                if text not in seen:
                    author_data = tweet.get('author', {})
                    if isinstance(author_data, dict):
                        author = author_data.get('userName') or author_data.get('name') or 'USER'
                    else:
                        author = str(author_data) if author_data else 'USER'
                        
                    if 'ASSISTANT' in author.upper() or 'GROK' in author.upper():
                        role = 'assistant'
                    else:
                        role = 'user'
                    messages.append({'role': role, 'author': author, 'content': text})
                    seen.add(text)
    
    user_colors = ['#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784', '#66BB6A']
    user_color_map = {}
    color_idx = 0
    
    html_str = "<div style='display: flex; flex-direction: column; gap: 10px; padding-bottom: 20px;'>"
    for i, msg in enumerate(messages):
        author = msg['author']
        if msg['role'] == 'assistant':
            bg_color = "#1D3557"
            text_color = "white"
            align = "flex-end"
            bubble_align = "left"
        else:
            if author not in user_color_map:
                user_color_map[author] = user_colors[color_idx % len(user_colors)]
                color_idx += 1
            bg_color = user_color_map[author]
            text_color = "black"
            align = "flex-start"
            bubble_align = "left"
            
        content_escaped = html.escape(msg['content']).replace('\n', '<br/>')
        author_escaped = html.escape(author)
        
        html_str += f"""
        <div style='display: flex; justify-content: {align}; margin-bottom: 15px;'>
            <div style='background-color: {bg_color}; color: {text_color}; padding: 12px; border-radius: 12px; max-width: 80%; text-align: {bubble_align}; box-shadow: 0 1px 2px rgba(0,0,0,0.1);'>
               <div style='font-size: 0.8em; margin-bottom: 4px; opacity: 0.8;'><b>{author_escaped}</b> (Turn {i+1})</div>
               <div style='line-height: 1.4; word-wrap: break-word;'>{content_escaped}</div>
            </div>
        </div>
        """
    html_str += "</div>"
    st.components.v1.html(html_str, height=800, scrolling=True)

with right_col:
    st.subheader("Annotation Form (Auto-Saves)")
    
    st.markdown("#### 1. Discussion Detection")
    is_disc_opts = ["yes", "no", "uncertain"]
    st.radio(
        "is_discussion",
        is_disc_opts,
        index=get_idx(is_disc_opts, existing_data.get("is_discussion")),
        key=f"is_discussion_{conv_id}",
        on_change=auto_save,
        help="YES if back-and-forth/persuasion/rebuttal. NO if simple praise/thanks, demo+ack, single-turn Q->A. UNCERTAIN if ambiguous."
    )
    
    intens_opts = [0, 1, 2, 3]
    st.radio(
        "discussion_intensity",
        intens_opts,
        index=get_idx(intens_opts, existing_data.get("discussion_intensity")),
        key=f"discussion_intensity_{conv_id}",
        on_change=auto_save,
        help="0=not a discussion. 1=light polite disagreement. 2=moderate explicit disagreement. 3=heated, insults, aggressive."
    )
    
    taxonomy = ["social","political","ethical","technical","scientific","health","legal","economic","personal","entertainment","other"]
    st.multiselect(
        "discussion_type",
        taxonomy,
        default=get_list(existing_data.get("discussion_type")),
        key=f"discussion_type_{conv_id}",
        on_change=auto_save,
        help="Controlled taxonomy: choose any applicable."
    )
    
    st.markdown("#### 2. Bias Language")
    bias_lang_opts = ["yes", "no", "uncertain"]
    st.radio(
        "bias_language",
        bias_lang_opts,
        index=get_idx(bias_lang_opts, existing_data.get("bias_language")),
        key=f"bias_language_{conv_id}",
        on_change=auto_save,
        help="YES if assistant (or participants) use loaded evaluative phrases. Originating in assistant's language."
    )
    
    bias_types = ["political_bias", "ideological_bias", "response_bias", "safety_bias", "none_detected"]
    st.multiselect(
        "assistant_bias",
        bias_types,
        default=get_list(existing_data.get("assistant_bias")),
        key=f"assistant_bias_{conv_id}",
        on_change=auto_save,
        help="Detect bias originating in the assistant's language. If none, select none_detected."
    )
    
    st.radio(
        "bias_intensity",
        intens_opts,
        index=get_idx(intens_opts, existing_data.get("bias_intensity")),
        key=f"bias_intensity_{conv_id}",
        on_change=auto_save,
        help="0=no bias. 1=mildly loaded. 2=explicit normative/adversarial language. 3=explicit discriminatory or high-intensity ideological labeling."
    )
    
    st.markdown("#### 3. Assistant Stance")
    stance_options = ["neutral", "assertive", "hedging", "sycophantic", "defensive", "contrarian", "uncertain"]
    st.selectbox(
        "assistant_stance",
        stance_options,
        index=get_idx(stance_options, existing_data.get("assistant_stance")),
        key=f"assistant_stance_{conv_id}",
        on_change=auto_save,
        help="neutral=factual; assertive=strongly states pos; hedging=uses qualifiers; sycophantic=excessively agrees; defensive=apologetic/deflecting; contrarian=pushes opposite view; uncertain=cannot determine"
    )
    
    st.multiselect(
        "assistant_stance_bias",
        bias_types,
        default=get_list(existing_data.get("assistant_stance_bias")),
        key=f"assistant_stance_bias_{conv_id}",
        on_change=auto_save,
        help="Same label options as bias_language origin flags"
    )
    
    st.markdown("#### 4. User Response")
    user_response_options = ["engaged", "disregard", "hostile", "confused", "neutral", "other"]
    st.selectbox(
        "user_response_type",
        user_response_options,
        index=get_idx(user_response_options, existing_data.get("user_response_type")),
        key=f"user_response_type_{conv_id}",
        on_change=auto_save,
        help="engaged=builds on reply; disregard=ignores assistant; hostile=insults/anger; confused=asks clarifying Qs indicating misunderstanding; neutral=brief ack without affect; other=doesn't fit"
    )
