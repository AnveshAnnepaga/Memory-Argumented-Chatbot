# Root main.py forwarding to app/main.py for root uvicorn & container execution
import os
import sys

# Prevent transformers from loading broken TensorFlow protobuf bindings on Windows
os.environ["USE_TF"] = "0"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from app.main import app, create_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
