import sys
import os

# Add the src directory to PYTHONPATH dynamically
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal
from src.orchestrator import Orchestrator
import nest_asyncio
from fastapi.responses import JSONResponse


# Initialize FastAPI app
app = FastAPI()

# CORS middleware for development convenience
from fastapi.middleware.cors import CORSMiddleware

# Add CORS middleware - using wildcard for development to avoid origin mismatch issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Set to False when using wildcard origins
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize Orchestrator
orch = Orchestrator()

# Pydantic models for request and response validation
class CurriculumRequest(BaseModel):
    topic: str
    level: Literal["beginner", "intermediate", "advanced"]
    goal: str | None = None

class FeedbackRequest(BaseModel):
    curriculum: dict
    review: dict
    feedback: str

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "LMS API is running"}

@app.get("/debug")
async def debug():
    """Debug endpoint."""
    return {"status": "API is working", "cors": "enabled"}

@app.post("/curriculum/plan")
async def plan_curriculum(request: CurriculumRequest):
    """Endpoint to plan a curriculum and return course structure quickly."""
    try:
        print(f"🚀 Starting curriculum generation for: {request.topic}")
        
        # Step 1: Create initial curriculum draft
        print("📋 Step 1: Creating curriculum draft...")
        draft = orch.plan_curriculum(topic=request.topic, level=request.level, goal=request.goal)
        print(f"✅ Draft created with {len(draft.modules)} modules")
        
        # Step 2: Auto-approve the curriculum (skip human review for web interface)
        approved = draft
        print("✅ Curriculum auto-approved")
        
        # Step 3: Generate detailed syllabus
        print("📚 Step 3: Generating detailed syllabus...")
        detailed = orch.draft_details(approved)
        total_subtopics = sum(len(m.subtopics) for m in detailed.outline)
        print(f"✅ Detailed syllabus created with {len(detailed.outline)} modules and {total_subtopics} subtopics")
        
        # Step 4: Save the course and get course_id
        print("💾 Step 4: Saving course...")
        course_id = orch.save_course(approved, detailed)
        print(f"✅ Course saved with ID: {course_id}")
        
        print(f"🎉 Course structure ready! Use /materials/build/{course_id} to generate content.")
        
        # Return course structure without materials (for speed)
        return {
            "course_id": course_id,
            "curriculum": approved.model_dump(),
            "detailed_syllabus": detailed.model_dump(),
            "total_lessons": total_subtopics,
            "status": "Course structure created successfully. Use /materials/build/{course_id} to generate content.",
            "build_url": f"/materials/build/{course_id}"
        }
        
    except Exception as e:
        print(f"❌ Error during course generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/curriculum/review")
async def review_curriculum(request: FeedbackRequest):
    """Endpoint to review and approve a curriculum."""
    try:
        approved = orch.revise_until_approved(request.curriculum, lambda c, r: request.feedback)
        return {"approved": approved.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/curriculum/details/{course_id}")
async def get_detailed_syllabus(course_id: str):
    """Endpoint to get detailed syllabus."""
    try:
        detailed = orch.draft_details(course_id)
        return {"detailed": detailed.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/course/save")
async def save_course(request: FeedbackRequest):
    """Endpoint to save a course."""
    try:
        course_id = orch.save_course(request.curriculum, request.review)
        return {"course_id": course_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/list")
async def list_courses():
    """Endpoint to list all existing courses."""
    try:
        print("📚 Listing existing courses...")
        courses = orch.store.list_courses()
        print(f"✅ Found {len(courses)} existing courses")
        return {"courses": courses}
    except Exception as e:
        print(f"❌ Error listing courses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/load/{course_id}")
async def load_existing_course(course_id: str):
    """Endpoint to load an existing course with all materials."""
    try:
        print(f"📖 Loading existing course: {course_id}")
        
        # Load course index
        index = orch.store.load_index(course_id)
        from src.models.curriculum import DetailedSyllabus
        syllabus = DetailedSyllabus.model_validate(index["syllabus"])
        total = sum(len(m.subtopics) for m in syllabus.outline)
        
        print(f"📊 Course has {total} lessons across {len(syllabus.outline)} modules")
        
        # Load all existing materials
        materials = []
        completed = 0
        
        for m_idx, mod in enumerate(syllabus.outline):
            print(f"📖 Loading Module {m_idx + 1}: {mod.title}")
            module_materials = []
            for s_idx, subtopic in enumerate(mod.subtopics):
                title, content = orch.get_or_build_lesson(course_id, m_idx, s_idx)
                module_materials.append({
                    "subtopic_index": s_idx,
                    "title": title,
                    "content": content,
                    "subtopic_description": subtopic
                })
                completed += 1
            
            materials.append({
                "module_index": m_idx,
                "module_title": mod.title,
                "subtopics": module_materials
            })
            print(f"✅ Module {m_idx + 1} loaded ({len(module_materials)} lessons)")
        
        print(f"🎉 Course loaded! {total} lessons available.")
        
        return {
            "course_id": course_id,
            "curriculum": {
                "topic": index["topic"],
                "level": index["level"],
                "goal": index["goal"]
            },
            "materials": materials,
            "total": total,
            "completed": completed,
            "status": "Course loaded successfully",
            "created_at": index.get("created_at", "Unknown")
        }
        
    except Exception as e:
        print(f"❌ Error loading course: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/materials/build/{course_id}")
async def build_materials(course_id: str):
    """Endpoint to build all study materials and return complete course content."""
    try:
        print(f"🔨 Building materials for course: {course_id}")
        
        # Load the course structure from saved index
        index = orch.store.load_index(course_id)
        from src.models.curriculum import DetailedSyllabus
        syllabus = DetailedSyllabus.model_validate(index["syllabus"])
        total = sum(len(m.subtopics) for m in syllabus.outline)
        
        print(f"📊 Building {total} lessons across {len(syllabus.outline)} modules")
        
        # Build all materials
        materials = []
        completed = 0
        
        for m_idx, mod in enumerate(syllabus.outline):
            print(f"📖 Processing Module {m_idx + 1}: {mod.title}")
            module_materials = []
            for s_idx, subtopic in enumerate(mod.subtopics):
                print(f"  📝 Creating lesson {completed + 1}/{total}: {subtopic[:50]}...")
                title, content = orch.get_or_build_lesson(course_id, m_idx, s_idx)
                module_materials.append({
                    "subtopic_index": s_idx,
                    "title": title,
                    "content": content,
                    "subtopic_description": subtopic
                })
                completed += 1
                print(f"  ✅ Completed {completed}/{total}")
            
            materials.append({
                "module_index": m_idx,
                "module_title": mod.title,
                "subtopics": module_materials
            })
            print(f"✅ Module {m_idx + 1} completed ({len(module_materials)} lessons)")
        
        print(f"🎉 All materials generated! {total} lessons created.")
        
        return {
            "course_id": course_id,
            "materials": materials,
            "total": total,
            "completed": completed,
            "status": "All materials generated successfully"
        }
        
    except Exception as e:
        print(f"❌ Error building materials: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/materials/subtopic/{course_id}/{module_number}/{subtopic_number}")
async def get_subtopic(course_id: str, module_number: int, subtopic_number: int):
    """Endpoint to fetch a specific subtopic."""
    try:
        title, md = orch.get_or_build_lesson(course_id, module_number - 1, subtopic_number - 1)
        return {"title": title, "content": md}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.middleware("http")
async def log_requests(request, call_next):
    print(f"Incoming request: {request.method} {request.url}")
    print(f"Headers: {request.headers}")
    response = await call_next(request)
    return response

nest_asyncio.apply()
