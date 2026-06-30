from fastapi import APIRouter
from app.config.universities.registry import registry

router = APIRouter()

@router.get("/universities", summary="Get all configured universities")
async def get_universities():
    universities = registry.get_all()
    # Format the response to match the frontend expectations
    # as defined in the API Design section of the implementation plan
    response_data = []
    for uni in universities:
        response_data.append({
            "university_id": uni.university_id,
            "university_name": uni.university_name,
            "short_name": uni.short_name,
            "logo_url": uni.branding.logo_url,
            "primary_color": uni.branding.primary_color,
            "welcome_message": uni.branding.welcome_message,
            "status": "active" if uni.connectors else "inactive"
        })
    
    return {"universities": response_data}
