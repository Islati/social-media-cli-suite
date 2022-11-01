from flask_cors import CORS

from bot import DefaultConfig
from bot.webapp import create_app

config = DefaultConfig()
flask_app = create_app(config)

if __name__ == "__main__":
    flask_app.run(debug=True,port=5000)