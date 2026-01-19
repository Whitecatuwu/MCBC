from loguru import logger
from pathlib import Path
from sys import stdout


def setup_logging():
    logger.remove()

    log_dir = Path("logs")
    log_file = log_dir / "{time}.log"

    # Console（stdout）
    logger.add(
        stdout,
        level="INFO",
        backtrace=True,  # 更完整 traceback（開發很有用）
        diagnose=False,  # 避免過度顯示敏感資料；需要時再開
    )

    logger.add(
        log_file,
        level="TRACE",  # 記錄所有等級的日誌到檔案
        backtrace=True,  # 顯示完整的錯誤堆疊追蹤
        rotation="32 MB",  # 每個檔案滿 256MB 就切分
        retention="14 days",  # 只保留最近 10 天的日誌 (自動刪除舊的)
        compression="zip",  # 切分後的舊檔案自動壓縮成 zip (節省空間)
        encoding="utf-8",  # 防止中文亂碼
        enqueue=True,  # 多線程安全
    )


if __name__ == "__main__":
    setup_logging()
    logger.info("這是一條資訊")
    logger.error("這是一條錯誤")
    logger.debug("這是一條除錯訊息")
    logger.warning("這是一條警告訊息")
    logger.success("這是一條成功訊息")
    logger.trace("這是一條追蹤訊息")
    logger.critical("這是一條嚴重錯誤訊息")
    logger.exception("這是一條例外訊息")
