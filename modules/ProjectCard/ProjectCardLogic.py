class ProjectCardLogic:
    def __init__(self):
        self.project_data = None

    def set_project(self, project_data):
        self.project_data = project_data

    def get_project_summary(self):
        if not self.project_data:
            return None
        return {
            "name": self.project_data.get("name", ""),
            "description": self.project_data.get("description", ""),
            "status": self.project_data.get("status", "")
        }
