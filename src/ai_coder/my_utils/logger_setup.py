# src/ai_coder/my_utils/logger_setup.py
# Add other file to use the logger
# import logging
# logger = logging.getLogger(__name__)  # Reuse the global logger
# poetry add aiofiles
# Example .env file content:
# LOG_LEVEL=DEBUG
# LOG_DIR=/var/logs
# LOG_MAX_BYTES=10485760  # 10 MB
# LOG_BACKUP_COUNT=10
# ENABLE_CONSOLE_LOGGING=True
# ENABLE_FILE_LOGGING=True

import json
import logging
import os
import queue
import sys
import threading
from collections.abc import Iterable
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler


from ai_coder.my_utils.env_loader import load_dotenv_once

# Load environment variables from .env file if it exists

try:
    load_dotenv_once()
except Exception:
    pass


# from aiofiles import open as aio_open  # This import can be removed if not used

# my_utils/logger_setup.py

# Change the console code page to UTF-8 on Windows to support Unicode characters.
if os.name == "nt":
    os.system("chcp 65001 >nul 2>&1")


def load_config(config_file=None):
    """
    Load logging configuration from a JSON file or environment variables, with overrides.

    :param config_file: Path to the JSON configuration file. If None, defaults will be used.
    :type config_file: str, optional

    :return: A dictionary containing the logging configuration.
    :rtype: dict

    **Default Configuration Keys:**
        - `log_level` (str): Logging level, default is "INFO".
        - `log_dir` (str): Directory for log files, default is the current working directory.
        - `log_max_bytes` (int): Max size of log files in bytes, default is 5 MB.
        - `log_backup_count` (int): Number of backup log files, default is 5.
        - `enable_console` (bool): Enable console logging, default is True.
        - `enable_file` (bool): Enable file logging, default is True.

    **Overrides:**
        - Environment variables can override the default and JSON file settings:
          - `LOG_LEVEL`, `LOG_DIR`, `LOG_MAX_BYTES`, `LOG_BACKUP_COUNT`,
            `ENABLE_CONSOLE_LOGGING`, `ENABLE_FILE_LOGGING`.
    """
    ############################
    # Default Configuration
    ############################
    config = {
        "log_level": "INFO",  # Default log level is INFO.
        "log_dir": os.getcwd(),  # Default to current directory if not provided
        "log_max_bytes": 5
        * 1024
        * 1024,  # Maximum log file size before rotation is 5 MB.
        "log_backup_count": 5,  # Retains up to 5 backup log files.
        "enable_console": True,  # Enables console logging by default.
        "enable_file": True,  # Enables file logging by default.
    }
    ############################
    # JSON File Configuration
    ############################
    # If a config_file is provided and exists, its contents are loaded as a JSON object and merged with the defaults.
    if config_file and os.path.exists(config_file):
        with open(config_file, "r") as f:
            json_config = json.load(f)
            config.update(json_config)

    ############################
    # Environment Variable Overrides
    ############################
    # Override settings from both the defaults and the JSON file.
    """
    Example variables:
        LOG_LEVEL: Sets the logging level (e.g., DEBUG, INFO).
        LOG_DIR: Specifies the log file directory.
        LOG_MAX_BYTES: Configures the maximum size of log files.
        LOG_BACKUP_COUNT: Configures how many backup log files to retain.
        ENABLE_CONSOLE_LOGGING: Enables or disables console logging.
        ENABLE_FILE_LOGGING: Enables or disables file logging
    """
    config["log_level"] = os.getenv("LOG_LEVEL", config["log_level"]).upper()
    config["log_dir"] = (
        os.getenv("LOG_DIR", config["log_dir"]) or os.getcwd()
    )  # Use current directory if LOG_DIR is empty or undefined
    config["log_max_bytes"] = int(os.getenv("LOG_MAX_BYTES", config["log_max_bytes"]))
    config["log_backup_count"] = int(
        os.getenv("LOG_BACKUP_COUNT", config["log_backup_count"])
    )
    config["enable_console"] = (
        os.getenv("ENABLE_CONSOLE_LOGGING", str(config["enable_console"])).lower()
        == "true"
    )
    config["enable_file"] = (
        os.getenv("ENABLE_FILE_LOGGING", str(config["enable_file"])).lower() == "true"
    )
    ############################
    # Configuration Validation
    ############################
    validate_config(config)

    # Returns the fully merged and validated configuration as a dictionary.
    return config


def validate_config(config):
    """
    Validate the logging configuration.

    :param config: The logging configuration dictionary to validate.
    :type config: dict

    :raises ValueError: If any required key is missing or a value is invalid.

    **Validation Checks:**
        - All required keys must be present: `log_level`, `log_dir`, `log_max_bytes`,
          `log_backup_count`, `enable_console`, `enable_file`.
        - `log_level` must be one of ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].
        - `log_max_bytes` must be a positive integer.
        - `log_backup_count` must be an integer less than or equal to 100.
        - `log_dir` must be a valid and existing directory.
    """
    # Defines a list of keys that must be present in the config dictionary.
    required_keys = [
        "log_level",
        "log_dir",
        "log_max_bytes",
        "log_backup_count",
        "enable_console",
        "enable_file",
    ]
    # Loops through the required_keys list and checks if each key exists in config.
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")

    # Ensures that config["log_level"] is a valid logging level.
    if config["log_level"] not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise ValueError(f"Invalid log level: {config['log_level']}")

    # Ensures that config["log_max_bytes"] is a positive integer.
    if not isinstance(config["log_max_bytes"], int) or config["log_max_bytes"] <= 0:
        raise ValueError("log_max_bytes must be a positive integer.")

    # Ensures that config["log_backup_count"] is a positive integer.
    if not isinstance(config["log_backup_count"], int):
        raise ValueError("log_backup_count must be an integer.")

    # Validates that log_backup_count does not exceed 100 (a practical limit to avoid excessive backup files).
    if config["log_backup_count"] > 100:
        raise ValueError("log_backup_count exceeds the maximum limit of 100.")

    # Normalize log_dir so relative values like "var\\logs" work anywhere
    log_dir_raw = str(config["log_dir"]).strip()
    log_dir_norm = os.path.expandvars(os.path.expanduser(log_dir_raw))
    log_dir_norm = os.path.abspath(log_dir_norm)
    config["log_dir"] = log_dir_norm

    # Create the directory if it does not exist
    try:
        os.makedirs(config["log_dir"], exist_ok=True)
    except Exception as e:
        raise ValueError(f"Failed to create log_dir '{config['log_dir']}': {e}")

    # Verifies that config["log_dir"] is a valid, existing directory.
    if not os.path.isdir(config["log_dir"]):
        raise ValueError(f"log_dir must be a valid directory: {config['log_dir']}")


class SecretRedactionFilter(logging.Filter):
    """Redact configured secret values from log records."""

    def __init__(self, secret_values: Iterable[object] = ()) -> None:
        super().__init__()
        self.secret_values = _clean_secret_values(secret_values)

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _redact_log_text(record.msg, self.secret_values)
        record.args = _redact_log_args(record.args, self.secret_values)
        return True


def _clean_secret_values(
    secret_values: Iterable[object],
) -> tuple[str, ...]:  #  Added Code
    cleaned_values: list[str] = []  #  Added Code

    for secret_value in secret_values:  #  Added Code
        cleaned_value = str(secret_value).strip()  #  Added Code

        if cleaned_value:  #  Added Code
            cleaned_values.append(cleaned_value)  #  Added Code

    return tuple(cleaned_values)  #  Added Code


def _redact_log_text(  #  Added Code
    text: object,  #  Added Code
    secret_values: tuple[str, ...],  #  Added Code
) -> str:  #  Added Code
    redacted_text = str(text)  #  Added Code

    for secret_value in secret_values:  #  Added Code
        redacted_text = redacted_text.replace(secret_value, "<redacted>")  #  Added Code

    return redacted_text  #  Added Code


def _redact_log_args(  #  Added Code
    args: object,  #  Added Code
    secret_values: tuple[str, ...],  #  Added Code
) -> object:  #  Added Code
    if isinstance(args, tuple):  #  Added Code
        return tuple(_redact_log_arg(arg, secret_values) for arg in args)  #  Added Code

    if isinstance(args, dict):  #  Added Code
        return {  #  Added Code
            key: _redact_log_arg(value, secret_values)  #  Added Code
            for key, value in args.items()  #  Added Code
        }  #  Added Code

    return args  #  Added Code


def _redact_log_arg(  #  Added Code
    arg: object,  #  Added Code
    secret_values: tuple[str, ...],  #  Added Code
) -> object:  #  Added Code
    if isinstance(arg, str):  #  Added Code
        return _redact_log_text(arg, secret_values)  #  Added Code

    return arg  #  Added Code


class AsyncRotatingFileHandler(RotatingFileHandler):
    """
    Custom asynchronous rotating file handler for logging using a background thread.

    :param buffer_size: Number of log messages to batch before writing to the file. Default is 1.
    :type buffer_size: int
    :param debug_messages: Enable debug messages for debugging the handler's behavior.
    :type debug_messages: bool
    """

    """
    Custom asynchronous rotating file handler for logging using a background thread.

    Summary of the Workflow
        The constructor initializes all the necessary components for asynchronous logging.
        Log messages are enqueued into self.queue when the emit() method is called.
        The background worker thread (self.worker) processes messages from the queue and writes them to the file in batches defined by self.buffer_size.
        This setup ensures non-blocking log writing and efficient handling of file I/O operations.

    Asynchronous Logging Workflow
        emit() adds a log message to the queue.
        The background thread dequeues messages in _process_queue().
        Messages are written in batches to improve performance.
        The handler ensures all pending messages are written before shutting down.
    """

    def __init__(self, *args, buffer_size=1, debug_messages=False, **kwargs):
        """
        Initialize the asynchronous rotating file handler.

        :param args: Positional arguments for the base `RotatingFileHandler`.
        :param buffer_size: Number of log messages to batch before writing to the file. Default is 1.
        :type buffer_size: int
        :param debug_messages: Enable debug messages for debugging the handler's behavior.
        :type debug_messages: bool
        :param kwargs: Keyword arguments for the base `RotatingFileHandler`.
        """
        super().__init__(*args, **kwargs)
        self.debug_messages = debug_messages  # Enable/disable debug messages
        if self.debug_messages:
            print(
                f"AsyncRotatingFileHandler initialized with file: {self.baseFilename}"
            )
        # Stores the batch size for writing logs. Messages will accumulate in a buffer until this size is reached.
        self.buffer_size = buffer_size  # Buffer size for batch writes
        # A thread-safe queue (queue.Queue()) to hold log messages.
        # It acts as a bridge between the main thread (producing logs) and
        # the background worker thread (processing logs).
        self.queue = queue.Queue()
        # A threading event used to signal the worker thread to stop gracefully when the handler is closed.
        self._stop_event = threading.Event()
        # A lock to ensure thread-safe operations, especially when closing the handler.
        self._lock = threading.RLock()
        ########################
        # Worker Thread Setup:
        ########################
        # A background thread that continuously monitors the queue and writes messages to the file in batches.
        # The thread is marked as a daemon thread, meaning it will automatically stop when the main program exits.
        self.worker = threading.Thread(target=self._process_queue, daemon=True)
        # Starts the worker thread, which runs the _process_queue method.
        self.worker.start()
        # Tracks whether the handler has been closed. This prevents duplicate or unsafe closure operations.
        self._closed = False  # Initialize the closed flag

    def _debug(self, message):
        if self.debug_messages:
            print(message)

    def emit(self, record):
        """
        Enqueue a log record for asynchronous processing.

        :param record: The log record to enqueue.
        :type record: logging.LogRecord
        """

        """
        Override emit to enqueue the formatted record instead of writing it immediately.

        Key Features of This Method:
            - Asynchronous Behavior:
                By enqueueing messages, the main thread avoids being blocked by potentially slow file I/O operations.
                Writing to the log file is handled in a separate thread, improving the application's responsiveness.
            - Thread Safety:
                Using a thread-safe queue (self.queue) ensures that log messages can be safely added to the queue from multiple threads.
            - Error Resilience:
                The try-except block ensures that issues during logging do not crash the application. Errors are gracefully handled using handleError.
            - Debugging Support:
                The debug statements provide insights into the flow of log messages through the handler, which is useful during development.
        """
        self._debug("function emit")  # Debug statement
        try:
            if self._stop_event.is_set() or self._closed:
                return
            # # Format the record object into a string (msg) using the formatter associated with the handler.
            # msg = self.format(record)
            # # Add the formatted log message to the queue without blocking.
            # self.queue.put_nowait(msg)
            # self._debug(f"Enqueued log message: {msg}")  # Debug statement

            # Enqueue the LogRecord, not the formatted string
            self.queue.put_nowait(record)
            self._debug(f"Enqueued LogRecord: {record.getMessage()}")

        except Exception as e:
            self._debug(f"Error in emit: {e}")
            self.handleError(record)

    def _process_queue(self):
        """
        Process log messages from the queue in a background thread.

        **Workflow:**
            - Continuously dequeues log messages until the stop event is set.
            - Writes messages to the log file in batches.
        """

        buffer = []
        self._debug("function _process_queue")  # Debug statement
        self._debug("Background thread started")

        # The loop continues until the stop event is set and the queue is empty.
        while not self._stop_event.is_set() or not self.queue.empty():
            try:
                # Retrieves a message from the queue.
                # If the queue is empty, a queue.Empty exception is raised, which is caught to prevent the thread from exiting.
                record = self.queue.get(timeout=0.1)
                if record is None:
                    continue
                # Adds the dequeued message to the buffer.
                buffer.append(record)
                self._debug(
                    f"\nDequeued log message: \n{record.getMessage()}"
                )  # Debug statement

                ############################
                # Batch Processing
                ############################
                # Checks if the buffer size has reached the predefined buffer_size.
                if len(buffer) >= self.buffer_size:
                    self._debug(f"Buffer size: {len(buffer)}")  # Debug statement
                    # Calls self._write_buffer(buffer) to write the messages to the log file.
                    self._write_buffer(buffer)
                    # Clears the buffer.
                    buffer.clear()
            except queue.Empty:
                self._debug("Queue is empty")  # Debug statement
                if buffer:
                    # Calls self._write_buffer(buffer) to write the messages to the log file.
                    self._write_buffer(buffer)
                    buffer.clear()
            except Exception as e:
                # can't call handleError without a record here; just keep looping
                self._debug(f"Error in _process_queue: {e}")
                pass

        # while loop ends when the stop event is set and the queue is empty
        # Write any remaining messages
        if buffer:
            self._debug(f"Writing remaining messages: {len(buffer)}")  # Debug
            # Calls self._write_buffer(buffer) to write the messages to the log file.
            self._write_buffer(buffer)
        self._debug("Background thread exiting")

        # def _write_buffer(self, buffer):
        #     """
        #     Write a batch of log messages to the file.

        #     :param buffer: List of log messages to write.
        #     :type buffer: list
        #     """

        #     """
        #     Messages are collected into a buffer by the _process_queue method.
        #     When the buffer reaches a predefined size (buffer_size), the _write_buffer method is called.
        #     The method writes all buffered messages to the log file in one operation.
        #     Any errors during the writing process are handled gracefully, ensuring system stability.

        #     Write a batch of log messages to the file.
        #     Writes a batch of messages to the file. Called by the background thread to write buffered messages.
        #     """
        #     self._debug("function _write_buffer")  # Debug statement
        #     self._debug("Writing buffer to file.")  # Debug statement
        #     try:
        #         # Joins all messages in the buffer into a single string, separated by newlines.
        #         # Each log message in the buffer becomes a separate line in the log file.
        #         # Ensures there is an additional newline at the end of the final log message.
        #         joined_messages = "\n".join(buffer) + "\n"
        #         # Writes the joined string of log messages to the log file (file stream).
        #         # The self.stream is managed by the parent RotatingFileHandler class and represents the open log file.
        #         self.stream.write(joined_messages)
        #         # Flushes the file stream to ensure that the messages are written to the file immediately.
        #         self.flush()
        #         # Debug statement to confirm the number of messages written to the file.
        #         self._debug(f"Wrote {len(buffer)} messages to file.")
        #         for msg in buffer:
        #             self._debug(f"  {msg}")  # Print each message written
        #     except Exception as e:
        #         self._debug(f"Error writing buffer to file: {e}")
        #         for msg in buffer:
        #             self.handleError(msg)

    def _write_buffer(self, buffer):
        try:
            with self._lock:
                if self.stream is None:
                    self.stream = self._open()

                for record in buffer:
                    if self.shouldRollover(record):
                        self._safe_do_rollover()

                    if self.stream is None:
                        self.stream = self._open()

                    msg = self.format(record)
                    self.stream.write(msg + "\n")

                self.flush()

        except Exception:
            for record in buffer:
                self.handleError(record)

    def _safe_do_rollover(self) -> None:
        try:
            self.doRollover()
        except PermissionError as error:
            self._debug(f"Skipped log rollover because the log file is locked: {error}")

            if self.stream is None:
                try:
                    self.stream = self._open()
                except Exception:
                    self.stream = None
                    raise

    def close(self):
        """
        Safely close the logging handler.

        **Workflow:**
            - Writes all pending log messages in the queue to the file.
            - Ensures the background thread exits cleanly.
            - Calls the base class's close method.
        """

        """
        Key Features of the close Method:
            - Thread Safety:
                Uses a lock (self._lock) to ensure the closure process is safe in multi-threaded environments.
            - Graceful Shutdown:
                Signals the background thread to stop using self._stop_event.
                Ensures the thread finishes processing before shutting down completely.
            - Processing Remaining Messages:
                Checks for any remaining messages in the queue and writes them to the file to prevent data loss.
            - Integration with Parent Class:
                Calls the parent class’s close method to ensure proper cleanup of resources.
            - Idempotence:
                Ensures that calling close multiple times has no adverse effects by checking the self._closed flag.
        """
        with self._lock:  # Ensure thread-safe closure
            self._debug("function close")  # Debug statement
            if self._closed:
                return

            self._closed = True
            self._debug("Closing AsyncRotatingFileHandler")  # Debug statement

            # Signals the background thread to stop using self._stop_event.
            self._stop_event.set()  # Signal the thread to stop

            try:
                self.queue.put_nowait(None)
            except Exception:
                pass

            # Waits for the background thread to complete its work and exit gracefully.
            self.worker.join(timeout=2.0)  # Wait for the thread to finish

            ########################################
            # Process Remaining Messages
            ########################################
            buffer = []
            while True:
                try:
                    item = self.queue.get_nowait()
                except queue.Empty:
                    break
                if item is None:
                    continue
                buffer.append(item)

            if buffer:
                self._write_buffer(buffer)

            try:
                self.flush()
            except Exception:
                pass

            # Calls the close method of the parent class to release resources.
            super().close()  # Call the base class close method
            self._debug("AsyncRotatingFileHandler closed")  # Debug statement


def setup_logger(  #  Changed Code
    logger_name=None,  #  Added Code
    config_file=None,  #  Added Code
    debug_messages=False,  #  Added Code
    secret_values: Iterable[object] = (),  #  Added Code
):  #  Added Code
    """
    Set up a named logger with asynchronous file logging and dynamic configuration.

    :param logger_name: Name of the logger. Defaults to the module name if None.
    :type logger_name: str, optional
    :param config_file: Path to a JSON configuration file for logging.
    :type config_file: str, optional
    :param debug_messages: Enable debug messages during logger setup.
    :type debug_messages: bool
    :param secret_values: Configured secret values to redact from handler output.
    :type secret_values: Iterable[object]

    :return: A configured logger instance.
    :rtype: logging.Logger
    """

    """
    Set up a named logger with asynchronous file logging and dynamic configuration.
    """

    def _debug(message):
        """
        Print debug messages if debug_messages is enabled.
        """
        if debug_messages:
            print(message)

    _debug("function setup_logger")  # Debug statement

    # A JSON file specified by config_file can be used to configure the logger.
    # Environment variables with defaults for missing keys.
    config = load_config(config_file)

    # Retrieve log directory and file name from environment variables
    # log_dir: The directory where log files are stored, defaulting to a subdirectory var/logs if not specified.
    log_dir = os.getenv("LOG_DIR")
    log_dir = (log_dir or "").strip()
    if not log_dir:
        log_dir = os.path.join(config["log_dir"], "var", "logs")

    # log_file_name: The name of the log file, defaulting to reportlog.log.
    log_file_name = os.getenv("LOG_FILE_NAME", "reportlog.log")

    # os.makedirs: Ensures the log directory exists; creates it if necessary.
    os.makedirs(log_dir, exist_ok=True)  # Ensure the directory exists

    # Combines log_dir and log_file_name into a full path for the log file.
    log_file = os.path.abspath(os.path.join(log_dir, log_file_name))

    # Debug statements to verify paths
    _debug(f"Log directory: {os.path.abspath(log_dir)}")  # Debug statement
    _debug(f"Log file absolute path: {log_file}")

    # Uses logger_name if provided, otherwise defaults to the module name (__name__).
    logger = logging.getLogger(logger_name or __name__)  # Reuse the global logger

    logger.setLevel(getattr(logging, config["log_level"], logging.INFO))
    # Prevents log messages from propagating to parent loggers.
    logger.propagate = False

    redaction_filter = SecretRedactionFilter(secret_values)  #  Added Code

    existing_handlers = list(logger.handlers)

    # Clear existing handlers to avoid duplicates
    # if logger.hasHandlers():
    #     logger.handlers.clear()  # Remove all existing handlers
    #     _debug("Cleared existing handlers")  # Debug statement

    # Do NOT clear existing handlers here.
    # logging.getLogger(name) returns the same shared logger object for the same name,
    # so tearing down handlers during setup can break other parts of the program.

    has_console_handler = any(
        isinstance(handler, logging.StreamHandler)
        and getattr(handler, "_test_browser_mcp_handler", False)
        and getattr(handler, "_test_browser_mcp_handler_type", "") == "console"
        for handler in existing_handlers
    )

    has_matching_file_handler = any(
        isinstance(handler, AsyncRotatingFileHandler)
        and getattr(handler, "_test_browser_mcp_handler", False)
        and getattr(handler, "_test_browser_mcp_handler_type", "") == "file"
        and os.path.abspath(getattr(handler, "baseFilename", "")) == log_file
        for handler in existing_handlers
    )

    ############################
    # Console Logging
    ############################S
    if config["enable_console"] and not has_console_handler:
        # Ensure stdout is UTF-8 without relying on fileno() (safer in IDEs/redirects).
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        console_handler.setLevel(getattr(logging, config["log_level"], logging.INFO))
        console_handler.addFilter(redaction_filter)  #  Added Code
        console_handler._test_browser_mcp_handler = True
        console_handler._test_browser_mcp_handler_type = "console"

        logger.addHandler(console_handler)
        _debug(
            "Added StreamHandler for console logging with UTF-8 encoding"
        )  # Debug statement
    elif config["enable_console"]:
        _debug("Console handler already configured; skipping duplicate add")

    ############################
    # File Logging with Async Rotating File Handler
    ############################
    if config["enable_file"] and not has_matching_file_handler:
        try:
            file_handler = AsyncRotatingFileHandler(
                log_file,
                maxBytes=config["log_max_bytes"],
                backupCount=config["log_backup_count"],
                buffer_size=1,  # Set buffer size to 1 for immediate writing
                encoding="utf-8",  # for encoding
                debug_messages=debug_messages,
            )
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s %(name)s:%(lineno)d [%(threadName)s] %(message)s"
                )
            )
            file_handler.addFilter(redaction_filter)  #  Added Code
            file_handler._test_browser_mcp_handler = True
            file_handler._test_browser_mcp_handler_type = "file"
            logger.addHandler(file_handler)
            _debug(f"AsyncRotatingFileHandler added: {log_file}")  # Debug statement
        except Exception as file_error:
            logger.warning(
                "File logging failed: %s. Falling back to console-only logging.",
                file_error,
            )
            _debug(
                f"Failed to add AsyncRotatingFileHandler: {file_error}"
            )  # Debug statement
    elif config["enable_file"]:
        _debug("Matching file handler already configured; skipping duplicate add")

    # Returns the configured logger, ready for use.
    return logger


@contextmanager
def managed_logger(logger_name=None, config_file=None):
    """
    Context manager for a logger with automatic cleanup.

    :param logger_name: Name of the logger.
    :type logger_name: str, optional
    :param config_file: Path to a JSON configuration file for logging.
    :type config_file: str, optional

    :yield: A configured logger instance.
    :rtype: logging.Logger

    **Example:**
        >>> with managed_logger("my_logger", "config.json") as logger:
        >>>     logger.info("Log message")
    """

    """
    Why Use managed_logger: It simplifies logger management, ensures proper cleanup,
    and integrates seamlessly with Python's with statement for clean and readable code.

    Best Practice: Use managed_logger for temporary loggers or in scenarios where
    automatic cleanup is critical. For long-lived applications,
    a persistent logger configured at startup may be more appropriate.
    """
    logger = setup_logger(logger_name, config_file)
    try:
        yield logger
    finally:
        for handler in logger.handlers[:]:
            if getattr(handler, "_test_browser_mcp_handler", False):
                try:
                    handler.close()
                finally:
                    logger.removeHandler(handler)
