from fastapi.templating import Jinja2Templates
import os

templates_path = "app/frontend/templates"
if not os.path.exists(templates_path):
    os.makedirs(templates_path, exist_ok=True)

templates = Jinja2Templates(directory=templates_path)
print(f"Has env: {hasattr(templates, 'env')}")
if hasattr(templates, 'env'):
    print(f"Env type: {type(templates.env)}")
