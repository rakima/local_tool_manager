from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from local_tool_manager.config import get_database_path, get_log_path
from local_tool_manager.database import Database, ToolRepository
from local_tool_manager.database.migrations import initialize_database
from local_tool_manager.ui.main_window import MainWindow
from local_tool_manager.utils.logging_config import configure_logging


def run() -> int:
    configure_logging(get_log_path())
    logger = logging.getLogger(__name__)
    logger.info("アプリ起動")
    application = QApplication(sys.argv)
    application.setApplicationName("Local Tool Manager")
    try:
        database = Database(get_database_path())
        initialize_database(database)
        window = MainWindow(ToolRepository(database))
        window.show()
        result = application.exec()
    except Exception as error:
        logger.exception("アプリ初期化失敗")
        QMessageBox.critical(None, "起動エラー", f"アプリを起動できませんでした。\n{error}")
        result = 1
    logger.info("アプリ終了")
    return result

