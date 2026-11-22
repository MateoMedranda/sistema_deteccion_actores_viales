from app.domain.schemas import WebPolicy
class WebPolicyService:
    def __init__(self,settings,state):self.settings,self.state=settings,state
    def get(self)->WebPolicy:
        s=self.settings;state=self.state
        service=getattr(state,"enrichment_job_service",None)
        capabilities=getattr(getattr(service,"processor",None),"capabilities",{})
        def ready(name):return capabilities.get(name)=="ready"
        return WebPolicy(
          image={"media_types":["image/jpeg","image/png"],"max_upload_bytes":s.max_upload_bytes,"max_image_pixels":s.max_image_pixels},
          video={"media_types":["video/mp4","video/quicktime"],"max_upload_bytes":s.max_video_upload_bytes,"max_duration_seconds":s.max_video_duration_seconds,"max_width":s.max_video_width,"max_height":s.max_video_height,"max_fps":s.max_video_fps,"max_frames":s.max_video_frames},
          capabilities={"image_detection":bool(getattr(state,"ready",False)),"video_analysis":bool(getattr(state,"ready",False) and getattr(state,"video_tools_ready",False)),"attributes":ready("attributes"),"plates":ready("plate_localization") and ready("plate_ocr")})
