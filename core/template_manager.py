import json
import os
from typing import Dict, List, Any
from core.dashboard_model import Dashboard, Page, ChartConfig


class TemplateManager:
    """Управление шаблонами дашбордов"""
    
    TEMPLATES_DIR = "templates"
    
    @classmethod
    def get_templates_dir(cls):
        """Возвращает путь к папке с шаблонами"""
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(current_dir, cls.TEMPLATES_DIR)
    
    @classmethod
    def ensure_templates_dir(cls):
        """Создаёт папку для шаблонов если её нет"""
        templates_dir = cls.get_templates_dir()
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
        return templates_dir
    
    @classmethod
    def get_templates(cls) -> List[Dict[str, Any]]:
        """Возвращает список доступных шаблонов"""
        templates = []
        templates_dir = cls.ensure_templates_dir()
        
        for filename in os.listdir(templates_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(templates_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        templates.append({
                            "name": data.get("name", filename.replace('.json', '')),
                            "description": data.get("description", ""),
                            "filename": filename,
                            "data": data
                        })
                except Exception as e:
                    print(f"❌ Error loading template {filename}: {e}")
        
        return templates
    
    @classmethod
    def save_template(cls, name: str, description: str, dashboard_data: Dict[str, Any]) -> bool:
        """Сохраняет дашборд как шаблон"""
        try:
            templates_dir = cls.ensure_templates_dir()
            
            filename = name.lower().replace(' ', '_') + '.json'
            filepath = os.path.join(templates_dir, filename)
            
            template_data = {
                "name": name,
                "description": description,
                "created": __import__('datetime').datetime.now().isoformat(),
                "dashboard": dashboard_data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Template saved: {name}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving template: {e}")
            return False
    
    @classmethod
    def load_template(cls, filename: str) -> Dict[str, Any]:
        """Загружает шаблон по имени файла"""
        try:
            templates_dir = cls.get_templates_dir()
            filepath = os.path.join(templates_dir, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
            
        except Exception as e:
            print(f"❌ Error loading template {filename}: {e}")
            return {}
    
    @classmethod
    def delete_template(cls, filename: str) -> bool:
        """Удаляет шаблон"""
        try:
            templates_dir = cls.get_templates_dir()
            filepath = os.path.join(templates_dir, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"✅ Template deleted: {filename}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Error deleting template: {e}")
            return False
    
    @classmethod
    def apply_template(cls, template_data: Dict[str, Any], target_dashboard: Dashboard) -> int:
        """Применяет шаблон к существующему дашборду"""
        try:
            dashboard_data = template_data.get("dashboard", {})
            
            target_dashboard.pages.clear()
            
            for page_data in dashboard_data.get("pages", []):
                page = Page.from_dict(page_data)
                target_dashboard.pages.append(page)
            
            target_dashboard.current_page = 0
            
            print(f"✅ Template applied: {len(target_dashboard.pages)} pages restored")
            return len(target_dashboard.pages)
            
        except Exception as e:
            print(f"❌ Error applying template: {e}")
            return 0