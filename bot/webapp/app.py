from bot.webapp import create_app
from bot.webapp.config import Config, DefaultConfig

app = create_app(DefaultConfig())
