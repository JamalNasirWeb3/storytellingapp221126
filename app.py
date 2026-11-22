import io
import os
from xml.sax.saxutils import escape

import streamlit as st
from groq import Groq
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

st.set_page_config(page_title='AI Storytelling Studio', page_icon='📖', layout='wide')


def setting(name, default=None):
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)


def generate_story(topic, genre, audience, length, language, characters, moral, creativity):
    api_key = setting('GROQ_API_KEY')
    if not api_key:
        raise ValueError('GROQ_API_KEY is missing. Add it to Streamlit Cloud Secrets.')
    model = setting('GROQ_MODEL', 'llama-3.1-8b-instant')
    word_limits = {'Short': '200–300', 'Medium': '500–700', 'Long': '900–1200'}
    system = ('You are a talented creative storyteller. Write original, engaging, age-appropriate '
              'stories with a compelling title, a clear beginning, character development, conflict, '
              'climax and satisfying ending. Use vivid descriptions and natural dialogue. '
              'Write in the requested language. Output only the story.')
    prompt = f'''Create an original story with these preferences:
Story idea: {topic}
Genre: {genre}
Audience: {audience}
Approximate length: {word_limits[length]} words
Language: {language}
Characters: {characters.strip() if characters.strip() else 'Choose suitable characters'}
Moral or lesson: {moral.strip() if moral.strip() else 'Choose a meaningful lesson'}
Include a creative title and a complete ending.'''
    response = Groq(api_key=api_key).chat.completions.create(
        model=model,
        messages=[{'role': 'system', 'content': system}, {'role': 'user', 'content': prompt}],
        temperature=float(creativity), max_completion_tokens=3500,
    )
    story = response.choices[0].message.content
    if not story:
        raise ValueError('The model returned an empty story. Please try again.')
    return story


def story_pdf(story):
    if any('\u0600' <= c <= '\u06ff' or '\u0900' <= c <= '\u097f' for c in story):
        return None
    buffer = io.BytesIO()
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    if os.path.exists(font_path) and 'StoryFont' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('StoryFont', font_path))
    font = 'StoryFont' if os.path.exists(font_path) else 'Helvetica'
    style = ParagraphStyle('StoryBody', parent=getSampleStyleSheet()['BodyText'],
                           fontName=font, fontSize=11, leading=17, spaceAfter=9)
    blocks = [Paragraph(escape(line), style) if line.strip() else Spacer(1, 8)
              for line in story.splitlines()]
    SimpleDocTemplate(buffer, pagesize=(595, 842), leftMargin=45, rightMargin=45,
                      topMargin=50, bottomMargin=50).build(blocks)
    return buffer.getvalue()


st.title('📖 AI Storytelling Studio')
st.caption('Create imaginative stories powered by Python, Streamlit and Groq AI')

left, right = st.columns([1, 2], gap='large')
with left:
    with st.form('story_form'):
        topic = st.text_area('Story Idea', placeholder='A young explorer discovers a hidden city...', height=120)
        genre = st.selectbox('Story Genre', ['Adventure', 'Fantasy', 'Mystery', 'Science Fiction',
                                            'Horror', 'Romance', 'Comedy', 'Educational', 'Historical'])
        audience = st.selectbox('Target Audience', ['Children', 'Teenagers', 'Adults', 'All Ages'])
        length = st.radio('Story Length', ['Short', 'Medium', 'Long'], horizontal=True)
        language = st.selectbox('Story Language', ['English', 'Urdu', 'Hindi', 'Arabic', 'Spanish'])
        characters = st.text_input('Main Characters (optional)', placeholder='Ali, Sara, Professor Ahmed')
        moral = st.text_input('Moral or Lesson (optional)', placeholder='Courage and teamwork')
        creativity = st.slider('Creativity Level', 0.1, 1.5, 0.8, 0.1)
        submitted = st.form_submit_button('✨ Generate Story', type='primary', use_container_width=True)

with right:
    st.subheader('Your AI-Generated Story')
    if submitted:
        if not topic.strip():
            st.warning('Please enter a story idea first.')
        else:
            with st.spinner('Writing your story...'):
                try:
                    st.session_state['story'] = generate_story(
                        topic, genre, audience, length, language, characters, moral, creativity
                    )
                except Exception as exc:
                    st.error(f'Story generation failed: {exc}')
    story = st.session_state.get('story')
    if story:
        st.markdown(story)
        st.divider()
        st.download_button('📥 Download TXT', data=story.encode('utf-8'),
                           file_name='story.txt', mime='text/plain', use_container_width=True)
        pdf = story_pdf(story)
        if pdf:
            st.download_button('📄 Download PDF', data=pdf, file_name='story.pdf',
                               mime='application/pdf', use_container_width=True)
        else:
            st.info('For Urdu, Arabic and Hindi stories, use TXT download. PDF shaping is not configured for these scripts.')
    else:
        st.info('Enter your preferences and click Generate Story to begin.')

st.divider()
st.caption('Powered by Groq AI • Generated stories may contain inaccuracies; review before publishing.')
