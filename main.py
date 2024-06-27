# Imports
import uvicorn
from api.config import config

# start API via python
if __name__ == "__main__":
    uvicorn.run("StartAPI:app",
                host=config.host,
                port=config.port,
                reload=config.debug,
                workers=config.workers)

    # root_path = config.PREFIX

