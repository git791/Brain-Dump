import streamlit as st
import google.generativeai as genai
import json
import os
from datetime import datetime
from io import StringIO
from dotenv import load_dotenv
load_dotenv()

# ============================================
# CONFIGURATION
# ============================================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

KNOWLEDGE_FILE = "knowledge_notes.json"
model = genai.GenerativeModel('gemini-2.5-flash-lite')

# ============================================
# STORAGE FUNCTIONS
# ============================================
def load_knowledge():
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "r") as f:
            return json.load(f)
    return {"chapters": {}, "concepts": [], "takeaways": [], "confusion_points": [], "definitions": []}

def save_knowledge(knowledge):
    with open(KNOWLEDGE_FILE, "w") as f:
        json.dump(knowledge, f, indent=2)

def extract_takeaways(messages, chapter):
    context = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-12:]])
    
    prompt = f"""
    Analyze this study conversation about "{chapter}" and extract knowledge in JSON.
    Return ONLY valid JSON.
    Format:
    {{
        "concepts": ["concept1"],
        "takeaways": ["summary"],
        "confusion_points": ["struggles"],
        "definitions": ["term: definition"]
    }}
    CONVERSATION:
    {context}
    """
    
    # Gemini's way of generating content
    response = model.generate_content(prompt)
    
    # Clean the response text (Gemini sometimes wraps JSON in ```json blocks)
    text = response.text
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
        
    return json.loads(text.strip())

def generate_10min_pathway(confusion_points, chapter):
    # If confusion_points is empty, we provide a default string
    topic = confusion_points if confusion_points else "general concepts"
    
    prompt = f"""
    The user is studying {chapter} and is stuck on: {topic}.
    Create a specific 10-minute action plan. 
    Do NOT mention square brackets or placeholders.
    Return ONLY valid JSON:
    {{ "steps": [ {{"time": "2 min", "action": "...", "detail": "..."}} ] }}
    """
    
    response = model.generate_content(prompt)
    # Aggressive cleaning for Gemini
    text = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(text)

# ============================================
# EXPORT FUNCTIONS
# ============================================
def export_to_markdown(knowledge, chapter):
    md = f"# {chapter} - Knowledge Notes\n\n"
    md += f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n"
    
    if knowledge.get("concepts"):
        md += "## 🧠 Key Concepts\n\n"
        for c in knowledge["concepts"]:
            md += f"- {c}\n"
        md += "\n"
    
    if knowledge.get("definitions"):
        md += "## 📝 Definitions & Formulas\n\n"
        for d in knowledge["definitions"]:
            md += f"- {d}\n"
        md += "\n"
    
    if knowledge.get("takeaways"):
        md += "## 💡 Takeaways\n\n"
        for t in knowledge["takeaways"]:
            md += f"- {t}\n"
        md += "\n"
    
    if knowledge.get("confusion_points"):
        md += "## ⚠️ Points to Review\n\n"
        for c in knowledge["confusion_points"]:
            md += f"- {c}\n"
    
    return md

def export_to_anki(knowledge, chapter):
    """Export to Anki-compatible CSV format."""
    lines = [f"{chapter} - Key Concepts"]
    
    for concept in knowledge.get("concepts", []):
        # Find related definition if exists
        related_def = ""
        for d in knowledge.get("definitions", []):
            if concept.lower() in d.lower():
                related_def = d
                break
        
        lines.append(f'"{concept}","{related_def}"')
    
    return "\n".join(lines)

def export_to_notion(knowledge, chapter):
    """Export formatted for Notion copy-paste."""
    text = f"**{chapter}**\n\n"
    
    text += "**🧠 Concepts:**\n"
    for c in knowledge.get("concepts", []):
        text += f"• {c}\n"
    
    text += "\n**📝 Definitions:**\n"
    for d in knowledge.get("definitions", []):
        text += f"• {d}\n"
    
    text += "\n**💡 Key Takeaways:**\n"
    for t in knowledge.get("takeaways", []):
        text += f"• {t}\n"
    
    return text

# ============================================
# STREAMLIT UI
# ============================================
def main():
    st.set_page_config(page_title="Study Companion", page_icon="📚", layout="wide")
    
    # Custom CSS for polish
    st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        border-radius: 8px;
    }
    .knowledge-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .pathway-card {
        background-color: #e8f4fd;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_chapter" not in st.session_state:
        st.session_state.current_chapter = "Chapter 1"
    if "knowledge" not in st.session_state:
        st.session_state.knowledge = load_knowledge()
    if "extraction_count" not in st.session_state:
        st.session_state.extraction_count = 0
    if "show_exam_review" not in st.session_state:
        st.session_state.show_exam_review = False
    
    # ============================================
    # SIDEBAR - Knowledge File
    # ============================================
    with st.sidebar:
        st.title("📚 Knowledge File")
        
        # Progress indicator
        k = st.session_state.knowledge
        concept_count = len(k.get("concepts", []))
        def_count = len(k.get("definitions", []))
        
        st.markdown(f"""
        <div class="knowledge-card">
            <strong>🧠 {concept_count} concepts</strong><br>
            <strong>📝 {def_count} definitions</strong>
        </div>
        """, unsafe_allow_html=True)
        
        # Chapter management
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆕 New"):
                st.session_state.current_chapter = f"Chapter {len(k.get('chapters', {})) + 1}"
                st.session_state.messages = []
                st.rerun()
        with col2:
            if st.button("📖 Review"):
                st.session_state.show_exam_review = not st.session_state.show_exam_review
        
        st.divider()
        
        # Export buttons
        st.subheader("📤 Export Notes")
        
        export_col1, export_col2 = st.columns(2)
        with export_col1:
            md_content = export_to_markdown(k, st.session_state.current_chapter)
            st.download_button("📄 Markdown", md_content, f"{st.session_state.current_chapter}.md", "text/markdown")
        with export_col2:
            anki_content = export_to_anki(k, st.session_state.current_chapter)
            st.download_button("🃏 Anki", anki_content, f"{st.session_state.current_chapter}_anki.csv", "text/csv")
        
        if st.button("📋 Copy for Notion"):
            notion_content = export_to_notion(k, st.session_state.current_chapter)
            st.code(notion_content, language="text")
            st.success("Copy the code above!")
        
        st.divider()
        
        # Live knowledge display
        st.subheader("📖 Your Brain's Notes")
        
        if concept_count > 0:
            st.write("**🧠 Concepts:**")
            for concept in k["concepts"][-8:]:
                st.write(f"• {concept}")
        
        if def_count > 0:
            st.write("**📝 Definitions:**")
            for defn in k["definitions"][-5:]:
                st.write(f"• {defn[:80]}{'...' if len(defn) > 80 else ''}")
        
        if st.button("🗑️ Clear All"):
            st.session_state.knowledge = {"chapters": {}, "concepts": [], "takeaways": [], "confusion_points": [], "definitions": []}
            save_knowledge(st.session_state.knowledge)
            st.rerun()
    
    # ============================================
    # MAIN CONTENT AREA
    # ============================================
    
    # Exam Review Mode
    if st.session_state.show_exam_review:
        st.markdown("## 📝 Exam Review Mode")
        st.markdown("*Your brain's notes, distilled for quick review.*\n")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if k.get("concepts"):
                st.subheader("🧠 Key Concepts")
                for i, concept in enumerate(k["concepts"], 1):
                    with st.expander(f"{i}. {concept}"):
                        # Find related definition
                        related = ""
                        for d in k.get("definitions", []):
                            if concept.lower() in d.lower():
                                related = d
                                break
                        if related:
                            st.info(related)
                        else:
                            st.write("No definition extracted yet.")
            
            if k.get("takeaways"):
                st.subheader("💡 Key Takeaways")
                for t in k["takeaways"]:
                    st.success(f"✓ {t}")
        
        with col2:
            st.subheader("⚠️ Review These")
            for cp in k.get("confusion_points", []):
                st.warning(f"• {cp}")
            
            st.subheader("📊 Stats")
            st.metric("Concepts", concept_count)
            st.metric("Definitions", def_count)
            st.metric("Takeaways", len(k.get("takeaways", [])))
        
        st.divider()
        if st.button("← Back to Chat"):
            st.session_state.show_exam_review = False
            st.rerun()
        
        st.markdown("---")
    
    # Regular Chat Mode
    st.title(f"📖 {st.session_state.current_chapter}")
    
    # Chapter rename
    new_chapter = st.text_input("Rename chapter", value=st.session_state.current_chapter, label_visibility="collapsed")
    if new_chapter != st.session_state.current_chapter:
        st.session_state.current_chapter = new_chapter
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input("Ask a question, explain something, or say 'I'm stuck'"):
        # User message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            response = ""
            
            # Check for confusion keywords
            confused_keywords = ["stuck", "confused", "don't understand", "doesn't make sense", "help", "what is", "explain"]
            is_confused = any(kw in prompt.lower() for kw in confused_keywords)
            
            if is_confused:
                saved_confusion = st.session_state.knowledge.get("confusion_points", [])
                topic_to_fix = prompt if not saved_confusion else saved_confusion[-3:]
    
                pathway = generate_10min_pathway(topic_to_fix, st.session_state.current_chapter)
    
                # Build plain markdown (no raw HTML) — works cleanly everywhere
                response = "### 🛤️ Your 10-Minute Pathway to Get Unstuck\n\n"
    
                for i, step in enumerate(pathway["steps"], 1):
                    response += f"**⏱️ Step {i} ({step['time']}): {step['action']}**\n\n"
                    response += f"> {step.get('detail', '')}\n\n"
                    response += "---\n"
    
                response += "*Check your Knowledge File in the sidebar for related concepts!*"
                
            else:
                chat_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-10:]])
                ai_prompt = f"""You are a helpful, friendly study tutor for the topic: "{st.session_state.current_chapter}".
                Answer the student's question clearly and concisely. Use simple language.

                Conversation so far:
                {chat_context}

                Student's question: {prompt}"""
                ai_response = model.generate_content(ai_prompt)
                response = ai_response.text
            
            st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Extract takeaways every 3 messages
        st.session_state.extraction_count += 1
        if st.session_state.extraction_count >= 3:
            st.session_state.extraction_count = 0
            with st.spinner("📝 Extracting knowledge..."):
                takeaways = extract_takeaways(
                    st.session_state.messages, 
                    st.session_state.current_chapter
                )
                
                k = st.session_state.knowledge
                
                # Merge with deduplication
                for key in ["concepts", "takeaways", "confusion_points", "definitions"]:
                    new_items = takeaways.get(key, [])
                    existing = k.get(key, [])
                    for item in new_items:
                        if item not in existing:
                            existing.append(item)
                    k[key] = existing
                
                save_knowledge(k)
                st.toast(f"✨ {len(takeaways.get('concepts', []))} new concepts extracted!", icon="📚")
                st.rerun()
if __name__ == "__main__":
    main()