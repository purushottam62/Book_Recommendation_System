from django.apps import AppConfig
import os, sys, importlib, traceback

class BackendAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend_app'

    def ready(self):
        """Executed once when Django finishes loading all apps."""
        try:
            MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../model'))
            if MODEL_DIR not in sys.path:
                sys.path.insert(0, MODEL_DIR)

            if 'utils' in sys.modules:
                importlib.reload(sys.modules['utils'])
            else:
                import utils

            print("🚀 model/utils.py loaded successfully in AppConfig.ready().")

        except Exception as e:
            print("⚠️ Failed to import model/utils.py during startup!")
            print(traceback.format_exc())
