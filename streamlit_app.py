import sys
import os
import asyncio
import streamlit as st
import nest_asyncio

nest_asyncio.apply()

# Add the src directory to PYTHONPATH dynamically
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.orchestrator import Orchestrator
from src.models.curriculum import Curriculum, Review, DetailedSyllabus
from src.utils.file_store import FileContentStore
from pathlib import Path
import json
from datetime import datetime

# Initialize the orchestrator
orch = Orchestrator()

# Page configuration
st.set_page_config(
    page_title="AI-Powered Learning Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2c3e50;
        font-size: 2.5em;
        margin-bottom: 30px;
    }
    .course-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #e9ecef;
        margin-bottom: 20px;
    }
    .module-header {
        background-color: #34495e;
        color: white;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
        cursor: pointer;
    }
    .subtopic-header {
        background-color: #f8f9fa;
        padding: 10px 15px;
        border-left: 4px solid #3498db;
        margin-bottom: 5px;
        cursor: pointer;
    }
    .content-area {
        background-color: white;
        padding: 20px;
        border-radius: 5px;
        border: 1px solid #ecf0f1;
    }
    .stats-box {
        background-color: #e8f6ff;
        padding: 15px;
        border-radius: 5px;
        text-align: center;
        margin-bottom: 20px;
    }
    .loading-text {
        text-align: center;
        color: #3498db;
        font-size: 18px;
        margin: 20px 0;
    }
    .success-text {
        text-align: center;
        color: #27ae60;
        font-size: 16px;
        margin: 10px 0;
    }
    .sidebar-course-btn {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 5px;
        padding: 8px 12px;
        margin-bottom: 5px;
        width: 100%;
        text-align: left;
        cursor: pointer;
        font-size: 12px;
    }
    .sidebar-course-btn:hover {
        background-color: #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_course' not in st.session_state:
    st.session_state.current_course = None
if 'course_data' not in st.session_state:
    st.session_state.course_data = None
if 'generation_active' not in st.session_state:
    st.session_state.generation_active = False
if 'current_concurrency' not in st.session_state:
    st.session_state.current_concurrency = None
if 'generation_status' not in st.session_state:
    st.session_state.generation_status = None

def main():
    # Check requirements first
    show_requirements_warning()

    st.markdown('<h1 class="main-header">🎓 AI-Powered Learning Management System</h1>', unsafe_allow_html=True)

    # Sidebar for navigation and current course info
    with st.sidebar:
        st.markdown("### 📚 Your Courses")

        # Get and display existing courses
        courses = get_existing_courses()

        # Search and filter functionality
        if courses:
            search_term = st.text_input("🔍 Search courses", placeholder="Type to filter...", key="course_search")
            if search_term:
                filtered_courses = [c for c in courses if search_term.lower() in c['topic'].lower()]
                display_courses = filtered_courses
                st.markdown(f"**{len(display_courses)} of {len(courses)} courses match:**")
            else:
                display_courses = courses
                st.markdown(f"**{len(courses)} available courses:**")

            for course in display_courses:
                course_id = course['course_id']
                topic = course['topic']
                level = course['level']
                total_lessons = course['total_lessons']

                # Create a compact button for each course
                button_text = f"{topic[:15]}... ({level})"
                if st.button(button_text, key=f"course_{course_id}", help=f"{total_lessons} lessons"):
                    load_course_from_sidebar(course_id)
        else:
            st.info("No courses yet. Create your first!")

        st.markdown("---")

        # Current course info (compact)
        if st.session_state.current_course:
            st.markdown("---")
            st.markdown("### 🎯 Active")
            current_course_data = next((c for c in courses if c['course_id'] == st.session_state.current_course), None)
            if current_course_data:
                st.markdown(f"**{current_course_data['topic'][:15]}...**")
                st.markdown(f"*{current_course_data['level']} • {current_course_data['total_lessons']} lessons*")
            if st.button("🔄 Switch Course", key="clear_course"):
                st.session_state.current_course = None
                st.session_state.course_data = None
                st.rerun()

        # Show current generation status if active
        if 'generation_active' in st.session_state and st.session_state.generation_active:
            st.markdown("---")
            st.markdown("### 🚀 Active Generation")
            st.markdown(f"**Concurrency:** {st.session_state.get('current_concurrency', 'N/A')}")
            st.markdown(f"**Status:** {st.session_state.get('generation_status', 'Processing...')}")

    # Create tabs for different functionalities
    tab1, tab2 = st.tabs(["📚 Quick Load", "🚀 Create New Course"])

    with tab1:
        load_existing_course_tab()

    with tab2:
        create_new_course_tab()

    # Display current course if loaded
    if st.session_state.course_data:
        display_current_course()

def show_requirements_warning():
    """Show requirements warning if needed."""
    import os

    missing_reqs = []

    if not os.getenv('OPENAI_API_KEY'):
        missing_reqs.append("OpenAI API Key")

    if missing_reqs:
        with st.expander("⚠️ Setup Required", expanded=True):
            st.warning("The following are required to use this application:")
            for req in missing_reqs:
                st.markdown(f"• {req}")

            if "OpenAI API Key" in missing_reqs:
                st.code("export OPENAI_API_KEY='your-openai-api-key-here'", language="bash")
                st.markdown("[Get your API key from OpenAI](https://platform.openai.com/api-keys)")

def display_current_course():
    """Display the currently loaded course."""
    if st.session_state.course_data:
        st.markdown("---")
        st.markdown("## 📖 Current Course Content")

        data = st.session_state.course_data
        syllabus = data['syllabus']

        # Display course header
        display_course_header(data['index'], syllabus)

        # Display materials
        display_course_materials(data['course_id'], syllabus)

def load_existing_course_tab():
    st.markdown("### 📚 Load Existing Course")

    # Get list of existing courses
    courses = get_existing_courses()

    if not courses:
        st.info("No existing courses found. Create a new course using the sidebar or the tab below.")
        return

    st.markdown(f"**Available Courses:** {len(courses)}")
    st.markdown("💡 **Tip:** You can also load courses directly from the sidebar!")

    # Simple course selection for those who prefer dropdown
    course_options = [f"{course['topic'][:40]}... ({course['level']}) - {course['total_lessons']} lessons"
                     for course in courses]
    course_ids = [course['course_id'] for course in courses]

    selected_course = st.selectbox(
        "Quick course selection:",
        options=[""] + course_ids,
        format_func=lambda x: "Select a course..." if x == "" else course_options[course_ids.index(x)],
        key="existing_course_select"
    )

    if selected_course and st.button("📖 Load Selected Course", key="load_course_btn"):
        load_course_from_sidebar(selected_course)

def create_new_course_tab():
    st.markdown("### 🚀 Create New Course")

    # Check if OpenAI API key is available
    if not check_openai_key():
        st.error("❌ OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        st.info("You can set it by running: `export OPENAI_API_KEY='your-key-here'`")
        return

    with st.form("course_form"):
        col1, col2 = st.columns(2)

        with col1:
            topic = st.text_input(
                "What do you want to learn?",
                placeholder="e.g., Python Programming, History of Ancient Rome, Quantum Mechanics",
                help="Enter the main topic for your course"
            )

        with col2:
            level = st.selectbox(
                "Level:",
                options=["beginner", "intermediate", "advanced"],
                help="Select your current knowledge level"
            )

        goal = st.text_area(
            "Goal (optional):",
            placeholder="e.g., Prepare for certification, Understand basics for work",
            help="Optional: Specify your learning objective"
        )

        concurrency = st.slider(
            "Generation Speed:",
            min_value=1,
            max_value=16,
            value=6,
            help="Higher values generate content faster but may hit API rate limits"
        )

        submitted = st.form_submit_button("🚀 Generate Complete Course")

        if submitted:
            if not topic.strip():
                st.error("❌ Please enter a topic for your course.")
            else:
                create_and_display_course(topic.strip(), level, goal.strip() or None, concurrency)

def get_existing_courses():
    """Get list of existing courses from the file system."""
    try:
        store = FileContentStore(Path("content"))
        return store.list_courses()
    except Exception as e:
        st.error(f"Error loading courses: {str(e)}")
        return []

def load_course_from_sidebar(course_id):
    """Load a course from the sidebar."""
    with st.spinner(f"Loading course {course_id[:20]}..."):
        try:
            # Load course data
            store = FileContentStore(Path("content"))
            index = store.load_index(course_id)
            syllabus = DetailedSyllabus.model_validate(index["syllabus"])

            # Store in session state
            st.session_state.current_course = course_id
            st.session_state.course_data = {
                'course_id': course_id,
                'index': index,
                'syllabus': syllabus
            }

            st.success(f"✅ Loaded course: {index['topic']}")
            st.rerun()

        except Exception as e:
            st.error(f"Error loading course: {str(e)}")

def load_and_display_course(course_id):
    """Load and display an existing course."""
    with st.spinner("📖 Loading existing course..."):
        try:
            # Load course data
            store = FileContentStore(Path("content"))
            index = store.load_index(course_id)
            syllabus = DetailedSyllabus.model_validate(index["syllabus"])

            # Store in session state
            st.session_state.current_course = course_id
            st.session_state.course_data = {
                'course_id': course_id,
                'index': index,
                'syllabus': syllabus
            }

            st.success("✅ Course loaded successfully!")
            st.rerun()

        except Exception as e:
            st.error(f"Error loading course: {str(e)}")

def check_openai_key():
    """Check if OpenAI API key is available."""
    import os
    return bool(os.getenv('OPENAI_API_KEY'))

def create_and_display_course(topic, level, goal, concurrency=6):
    """Create a new course and display it."""
    with st.spinner("🤖 AI is creating your course structure..."):
        try:
            # Step 1: Create course structure
            st.markdown('<p class="loading-text">🤖 AI is creating your course structure...</p>', unsafe_allow_html=True)
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("📋 Step 1: Creating curriculum draft...")
            draft = orch.plan_curriculum(topic=topic, level=level, goal=goal)
            progress_bar.progress(25)

            status_text.text("✅ Curriculum auto-approved")
            approved = draft  # Auto-approve for web interface
            progress_bar.progress(50)

            status_text.text("📚 Step 2: Generating detailed syllabus...")
            detailed = orch.draft_details(approved)
            progress_bar.progress(75)

            status_text.text("💾 Step 3: Saving course...")
            course_id = orch.save_course(approved, detailed)
            progress_bar.progress(100)

            status_text.text("🎉 Course structure ready!")
            progress_bar.empty()
            status_text.empty()

            # Display course header
            display_course_header({
                "topic": topic,
                "level": level,
                "goal": goal,
                "course_id": course_id,
                "created_at": datetime.utcnow().isoformat() + "Z"
            }, detailed)

            # Step 2: Build materials concurrently with enhanced progress tracking
            st.markdown('<p class="loading-text">📚 Course structure created! Now building study materials...</p>', unsafe_allow_html=True)

            total_lessons = sum(len(m.subtopics) for m in detailed.outline)
            estimated_time = max(1, total_lessons // (concurrency * 2))  # Rough estimate: ~2 lessons per minute per concurrent task

            st.info(f"🚀 **Concurrent Generation Mode Enabled!**\n"
                   f"• Total lessons: {total_lessons}\n"
                   f"• Concurrency level: {concurrency}\n"
                   f"• Estimated time: {estimated_time}-{estimated_time*2} minutes\n"
                   f"• **Performance boost**: Up to {concurrency}x faster than sequential generation!\n"
                   f"• **File format**: All lessons saved as .md files for consistency")

            # Enhanced progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            lesson_counter = st.empty()
            time_estimate = st.empty()

            # Create a custom concurrent builder with progress updates
            import time
            start_time = time.time()

            # Set generation status
            st.session_state.generation_active = True
            st.session_state.current_concurrency = concurrency
            st.session_state.generation_status = "Starting concurrent generation..."

            result = asyncio.run(build_materials_with_progress(
                course_id, detailed, concurrency, progress_bar, status_text, lesson_counter, time_estimate, start_time
            ))

            progress_bar.progress(100)
            total_time = time.time() - start_time
            status_text.text("✅ All materials generated successfully!")
            lesson_counter.text(f"🎉 Completed {result['completed']}/{result['total']} lessons in {total_time:.1f}s")
            time_estimate.empty()

            # Clear generation status
            st.session_state.generation_active = False
            st.session_state.current_concurrency = None
            st.session_state.generation_status = None

            if result['failures']:
                st.warning(f"⚠️ {len(result['failures'])} failures occurred during generation")
                with st.expander("View failures"):
                    for failure in result['failures']:
                        st.error(failure)

            # Store in session state
            st.session_state.current_course = course_id
            st.session_state.course_data = {
                'course_id': course_id,
                'index': {
                    "topic": topic,
                    "level": level,
                    "goal": goal,
                    "course_id": course_id,
                    "created_at": datetime.utcnow().isoformat() + "Z"
                },
                'syllabus': detailed
            }

            st.success("✅ Course created and materials generated successfully!")
            st.balloons()

            # Performance summary
            st.info("**🚀 Performance Summary:**\n"
                   f"• Generated {result['completed']}/{result['total']} lessons\n"
                   f"• Total time: {total_time:.1f} seconds\n"
                   f"• Average speed: {result['completed']/total_time:.1f} lessons/second\n"
                   f"• All files saved in consistent .md format")

            st.rerun()

        except Exception as e:
            st.error(f"Error creating course: {str(e)}")

def display_course_header(index, syllabus):
    """Display course header information."""
    st.markdown('<div class="course-card">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"**📚 Topic:** {index['topic']}")

    with col2:
        st.markdown(f"**🎯 Level:** {index['level']}")

    with col3:
        st.markdown(f"**🆔 Course ID:** {index['course_id']}")

    if index.get('goal'):
        st.markdown(f"**🎯 Goal:** {index['goal']}")

    st.markdown('</div>', unsafe_allow_html=True)

    # Course statistics
    total_lessons = sum(len(m.subtopics) for m in syllabus.outline)
    st.markdown('<div class="stats-box">', unsafe_allow_html=True)
    st.markdown(f"**📊 Course Statistics:** {len(syllabus.outline)} Modules | {total_lessons} Lessons")
    st.markdown('</div>', unsafe_allow_html=True)

def display_course_materials(course_id, syllabus):
    """Display course materials with expandable modules and subtopics."""
    for module_idx, module in enumerate(syllabus.outline):
        with st.expander(f"📖 Module {module_idx + 1}: {module.title} ({len(module.subtopics)} lessons)", expanded=False):
            for subtopic_idx, subtopic in enumerate(module.subtopics):
                with st.expander(f"📝 {subtopic}", expanded=False):
                    try:
                        # Check if lesson exists in .md format first (fastest)
                        if orch.store.has_lesson(course_id, module_idx, subtopic_idx, subtopic):
                            title, content = subtopic, orch.store.read_lesson(course_id, module_idx, subtopic_idx, subtopic)
                            st.success(f"✅ Loaded from cache (.md format)")
                        else:
                            # Try old format for backward compatibility
                            title, content = orch.get_or_build_lesson(course_id, module_idx, subtopic_idx)
                            # Save in new format for future use
                            if not orch.store.has_lesson(course_id, module_idx, subtopic_idx, subtopic):
                                orch.store.write_lesson(course_id, module_idx, subtopic_idx, subtopic, content)
                            st.info(f"📝 Migrated to .md format")

                        # Process content for better Streamlit rendering
                        processed_content = process_markdown_content(content)

                        # Render the markdown content
                        st.markdown(processed_content, unsafe_allow_html=True)

                    except Exception as e:
                        st.error(f"Error loading lesson: {str(e)}")

def process_markdown_content(content):
    """Process markdown content for better Streamlit rendering."""
    # Streamlit handles most markdown well, but we can add some enhancements
    # Ensure proper line breaks and formatting
    processed = content.replace('\n\n', '\n\n')  # Ensure double line breaks

    # Add some custom styling for better readability
    processed = f'<div class="content-area">\n{processed}\n</div>'

    return processed

async def build_materials_with_progress(course_id, syllabus, concurrency, progress_bar, status_text, lesson_counter, time_estimate, start_time):
    """Build materials concurrently with enhanced progress tracking."""
    import time
    total = sum(len(m.subtopics) for m in syllabus.outline)
    completed = 0
    failures = []

    # Create semaphore for concurrency control
    sem = asyncio.Semaphore(concurrency)

    async def process_lesson(m_idx, s_idx):
        nonlocal completed
        try:
            async with sem:
                module = syllabus.outline[m_idx]
                subtopic = module.subtopics[s_idx]

                # Update status
                status_text.text(f"📝 Generating: Module {m_idx + 1}.{s_idx + 1} - {subtopic[:50]}...")
                lesson_counter.text(f"Progress: {completed + 1}/{total} lessons")

                # Update session state for sidebar
                st.session_state.generation_status = f"Module {m_idx + 1}.{s_idx + 1}: {subtopic[:30]}..."

                # Update time estimate
                elapsed = time.time() - start_time
                if completed > 0:
                    avg_time_per_lesson = elapsed / completed
                    remaining_lessons = total - completed
                    estimated_remaining = avg_time_per_lesson * remaining_lessons
                    time_estimate.text(f"⏱️ Est. remaining: {estimated_remaining:.1f}s")

                # Generate the lesson
                title, content = await orch.get_or_build_lesson_async(course_id, syllabus, m_idx, s_idx)

                # Ensure it's saved with proper .md extension
                if not orch.store.has_lesson(course_id, m_idx, s_idx, subtopic):
                    await asyncio.to_thread(orch.store.write_lesson, course_id, m_idx, s_idx, subtopic, content)

                # Update progress
                completed += 1
                progress = int((completed / total) * 100)
                progress_bar.progress(progress)

                return (m_idx, s_idx, title, content)

        except Exception as e:
            failures.append(f"Module {m_idx + 1}.{s_idx + 1} ({subtopic}): {str(e)}")
            completed += 1
            progress = int((completed / total) * 100)
            progress_bar.progress(progress)
            return None

    # Create tasks for all lessons
    tasks = [
        asyncio.create_task(process_lesson(m_idx, s_idx))
        for m_idx, mod in enumerate(syllabus.outline)
        for s_idx, _ in enumerate(mod.subtopics)
    ]

    # Run tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    materials = []
    result_map = {}

    for r in results:
        if isinstance(r, Exception):
            failures.append(str(r))
            continue
        if r is not None:
            m_idx, s_idx, title, content = r
            result_map[(m_idx, s_idx)] = {
                "subtopic_index": s_idx,
                "title": title,
                "content": content,
                "subtopic_description": syllabus.outline[m_idx].subtopics[s_idx],
            }

    # Organize by module
    for m_idx, mod in enumerate(syllabus.outline):
        module_materials = [
            result_map[(m_idx, s_idx)]
            for s_idx in range(len(mod.subtopics))
            if (m_idx, s_idx) in result_map
        ]
        materials.append({
            "module_index": m_idx,
            "module_title": mod.title,
            "subtopics": module_materials,
        })

    return {
        "course_id": course_id,
        "materials": materials,
        "total": total,
        "completed": completed - len(failures),
        "failures": failures,
        "status": "Concurrent build completed" if not failures else "Completed with some failures",
    }

if __name__ == "__main__":
    main()
