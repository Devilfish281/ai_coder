# File: my_utils/token_usage.py

import json
import signal
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ai_coder.my_utils.env_loader import load_dotenv_once


class SingletonMeta(type):
    """
    Thread-safe implementation of Singleton.
    """

    _instances = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        # Ensure thread-safe singleton instantiation
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class TokenUsage(metaclass=SingletonMeta):
    """
    Singleton class to manage and persist token usage across threads.
    """

    TOKEN_FILE = "token_usage_tier.json"

    RATE_LIMITS = {
        "Free": {
            "gpt-4o-mini": {"RPM": 3, "TPM": 40000, "Batch Queue Limit": "-"},
            "text-embedding-3-large": {
                "RPM": 100,
                "TPM": 2000,
                "Batch Queue Limit": 40000,
            },
            "text-embedding-3-small": {
                "RPM": 100,
                "TPM": 2000,
                "Batch Queue Limit": 40000,
            },
            "text-embedding-ada-002": {
                "RPM": 100,
                "TPM": 2000,
                "Batch Queue Limit": 40000,
            },
            "omni-moderation-*": {"RPM": 250, "TPM": 5000, "Batch Queue Limit": "-"},
            "whisper-1": {"RPM": 3, "TPM": "-", "Batch Queue Limit": "-"},
            "tts-1": {"RPM": 3, "TPM": "-", "Batch Queue Limit": "-"},
            "dall-e-2": {"RPM": 5, "TPM": "-", "Batch Queue Limit": "-"},
            "dall-e-3": {"RPM": 1, "TPM": "-", "Batch Queue Limit": "-"},
        },
        "Tier 1": {
            "gpt-4o": {"RPM": 500, "TPM": 30000, "Batch Queue Limit": 90000},
            "gpt-4o-mini": {"RPM": 500, "TPM": 200000, "Batch Queue Limit": 2000000},
            "gpt-4o-realtime-preview": {
                "RPM": 100,
                "TPM": 20000,
                "Batch Queue Limit": "-",
            },
            "o1-preview": {"RPM": 500, "TPM": 30000, "Batch Queue Limit": 90000},
            "o1-mini": {"RPM": 500, "TPM": 200000, "Batch Queue Limit": 2000000},
            "gpt-4-turbo": {"RPM": 500, "TPM": 30000, "Batch Queue Limit": 90000},
            "gpt-4": {"RPM": 500, "TPM": 10000, "Batch Queue Limit": 100000},
            "gpt-3.5-turbo": {
                "RPM": 3500,
                "TPM": 2000000,
                "Batch Queue Limit": 5000000,
            },
            "omni-moderation-*": {"RPM": 500, "TPM": 10000, "Batch Queue Limit": "-"},
            "text-embedding-3-large": {
                "RPM": 3000,
                "TPM": 1000000,
                "Batch Queue Limit": 3000000,
            },
            "text-embedding-3-small": {
                "RPM": 3000,
                "TPM": 1000000,
                "Batch Queue Limit": 3000000,
            },
            "text-embedding-ada-002": {
                "RPM": 3000,
                "TPM": 1000000,
                "Batch Queue Limit": 3000000,
            },
            "whisper-1": {"RPM": 500, "TPM": "-", "Batch Queue Limit": "-"},
            "tts-1": {"RPM": 500, "TPM": "-", "Batch Queue Limit": "-"},
            "tts-1-hd": {"RPM": 500, "TPM": "-", "Batch Queue Limit": "-"},
            "dall-e-2": {"RPM": 500, "TPM": "-", "Batch Queue Limit": "-"},
            "dall-e-3": {"RPM": 500, "TPM": "-", "Batch Queue Limit": "-"},
        },
        "Tier 2": {
            "gpt-4o": {"RPM": 5000, "TPM": 450000, "Batch Queue Limit": 1350000},
            "gpt-4o-mini": {"RPM": 5000, "TPM": 2000000, "Batch Queue Limit": 20000000},
            "gpt-4o-realtime-preview": {
                "RPM": 200,
                "TPM": 40000,
                "Batch Queue Limit": "-",
            },
            "o1-preview": {"RPM": 5000, "TPM": 450000, "Batch Queue Limit": 1350000},
            "o1-mini": {"RPM": 5000, "TPM": 2000000, "Batch Queue Limit": 20000000},
            "gpt-4-turbo": {"RPM": 5000, "TPM": 450000, "Batch Queue Limit": 1350000},
            "gpt-4": {"RPM": 5000, "TPM": 40000, "Batch Queue Limit": 200000},
            "gpt-3.5-turbo": {
                "RPM": 3500,
                "TPM": 2000000,
                "Batch Queue Limit": 5000000,
            },
            "omni-moderation-*": {"RPM": 500, "TPM": 20000, "Batch Queue Limit": "-"},
            "text-embedding-3-large": {
                "RPM": 5000,
                "TPM": 1000000,
                "Batch Queue Limit": 20000000,
            },
            "text-embedding-3-small": {
                "RPM": 5000,
                "TPM": 1000000,
                "Batch Queue Limit": 20000000,
            },
            "text-embedding-ada-002": {
                "RPM": 5000,
                "TPM": 1000000,
                "Batch Queue Limit": 20000000,
            },
            "whisper-1": {"RPM": 2500, "TPM": "-", "Batch Queue Limit": "-"},
            "tts-1": {"RPM": 2500, "TPM": "-", "Batch Queue Limit": "-"},
            "tts-1-hd": {"RPM": 2500, "TPM": "-", "Batch Queue Limit": "-"},
            "dall-e-2": {"RPM": 2500, "TPM": "-", "Batch Queue Limit": "-"},
            "dall-e-3": {"RPM": 2500, "TPM": "-", "Batch Queue Limit": "-"},
        },
        "Tier 3": {
            "gpt-4o": {"RPM": 5000, "TPM": 800000, "Batch Queue Limit": 50000000},
            "gpt-4o-mini": {"RPM": 5000, "TPM": 4000000, "Batch Queue Limit": 40000000},
            "gpt-4o-realtime-preview": {
                "RPM": 5000,
                "TPM": 400000,
                "Batch Queue Limit": "-",
            },
            "o1-preview": {"RPM": 5000, "TPM": 800000, "Batch Queue Limit": 50000000},
            "o1-mini": {"RPM": 5000, "TPM": 4000000, "Batch Queue Limit": 40000000},
            "gpt-4-turbo": {"RPM": 5000, "TPM": 600000, "Batch Queue Limit": 40000000},
            "gpt-4": {"RPM": 5000, "TPM": 80000, "Batch Queue Limit": 5000000},
            "gpt-3.5-turbo": {
                "RPM": 3500,
                "TPM": 4000000,
                "Batch Queue Limit": 100000000,
            },
            "omni-moderation-*": {"RPM": 1000, "TPM": 50000, "Batch Queue Limit": "-"},
            "text-embedding-3-large": {
                "RPM": 5000,
                "TPM": 5000000,
                "Batch Queue Limit": 100000000,
            },
            "text-embedding-3-small": {
                "RPM": 5000,
                "TPM": 5000000,
                "Batch Queue Limit": 100000000,
            },
            "text-embedding-ada-002": {
                "RPM": 5000,
                "TPM": 5000000,
                "Batch Queue Limit": 100000000,
            },
            "whisper-1": {"RPM": 5000, "TPM": "-", "Batch Queue Limit": "-"},
            "tts-1": {"RPM": 5000, "TPM": "-", "Batch Queue Limit": "-"},
            "tts-1-hd": {"RPM": 5000, "TPM": "-", "Batch Queue Limit": "-"},
            "dall-e-2": {"RPM": 5000, "TPM": "-", "Batch Queue Limit": "-"},
            "dall-e-3": {"RPM": 5000, "TPM": "-", "Batch Queue Limit": "-"},
        },
        "Tier 4": {
            "gpt-4o": {"RPM": 10000, "TPM": 2000000, "Batch Queue Limit": 200000000},
            "gpt-4o-mini": {
                "RPM": 10000,
                "TPM": 10000000,
                "Batch Queue Limit": 1000000000,
            },
            "gpt-4o-realtime-preview": {
                "RPM": 10000,
                "TPM": 2000000,
                "Batch Queue Limit": "-",
            },
            "o1": {"RPM": 1000, "TPM": 30000000, "Batch Queue Limit": "-"},
            "o1-preview": {
                "RPM": 10000,
                "TPM": 30000000,
                "Batch Queue Limit": 5000000000,
            },
            "o1-mini": {
                "RPM": 30000,
                "TPM": 150000000,
                "Batch Queue Limit": 15000000000,
            },
            "gpt-4-turbo": {
                "RPM": 10000,
                "TPM": 2000000,
                "Batch Queue Limit": 300000000,
            },
            "gpt-4": {"RPM": 10000, "TPM": 1000000, "Batch Queue Limit": 150000000},
            "gpt-3.5-turbo": {
                "RPM": 10000,
                "TPM": 50000000,
                "Batch Queue Limit": 10000000000,
            },
            "omni-moderation-*": {"RPM": 5000, "TPM": 500000, "Batch Queue Limit": "-"},
            "text-embedding-3-large": {
                "RPM": 10000,
                "TPM": 10000000,
                "Batch Queue Limit": 4000000000,
            },
            "text-embedding-3-small": {
                "RPM": 10000,
                "TPM": 10000000,
                "Batch Queue Limit": 4000000000,
            },
            "text-embedding-ada-002": {
                "RPM": 10000,
                "TPM": 10000000,
                "Batch Queue Limit": 4000000000,
            },
            "whisper-1": {"RPM": 7500, "TPM": "-", "Batch Queue Limit": "-"},
            "tts-1": {"RPM": 7500, "TPM": "-", "Batch Queue Limit": "-"},
            "tts-1-hd": {"RPM": 7500, "TPM": "-", "Batch Queue Limit": "-"},
            "dall-e-2": {"RPM": 7500, "TPM": "-", "Batch Queue Limit": "-"},
            "dall-e-3": {"RPM": 7500, "TPM": "-", "Batch Queue Limit": "-"},
        },
        "Tier 5": {
            "gpt-4o": {"RPM": 10000, "TPM": 30000000, "Batch Queue Limit": 5000000000},
            "gpt-4o-mini": {
                "RPM": 30000,
                "TPM": 150000000,
                "Batch Queue Limit": 15000000000,
            },
            "gpt-4o-realtime-preview": {
                "RPM": 20000,
                "TPM": 10000000,
                "Batch Queue Limit": "-",
            },
            "o1": {"RPM": 1000, "TPM": 30000000, "Batch Queue Limit": "-"},
            "o1-preview": {
                "RPM": 10000,
                "TPM": 30000000,
                "Batch Queue Limit": 5000000000,
            },
            "o1-mini": {
                "RPM": 30000,
                "TPM": 150000000,
                "Batch Queue Limit": 15000000000,
            },
            "gpt-4-turbo": {
                "RPM": 10000,
                "TPM": 2000000,
                "Batch Queue Limit": 300000000,
            },
            "gpt-4": {"RPM": 10000, "TPM": 1000000, "Batch Queue Limit": 150000000},
            "gpt-3.5-turbo": {
                "RPM": 10000,
                "TPM": 50000000,
                "Batch Queue Limit": 10000000000,
            },
            "omni-moderation-*": {"RPM": 5000, "TPM": 500000, "Batch Queue Limit": "-"},
            "text-embedding-3-large": {
                "RPM": 10000,
                "TPM": 10000000,
                "Batch Queue Limit": 4000000000,
            },
            "text-embedding-3-small": {
                "RPM": 10000,
                "TPM": 10000000,
                "Batch Queue Limit": 4000000000,
            },
            "text-embedding-ada-002": {
                "RPM": 10000,
                "TPM": 10000000,
                "Batch Queue Limit": 4000000000,
            },
            "whisper-1": {"RPM": 10000, "TPM": "-", "Batch Queue Limit": "-"},
            "tts-1": {"RPM": 10000, "TPM": "-", "Batch Queue Limit": "-"},
            "tts-1-hd": {"RPM": 10000, "TPM": "-", "Batch Queue Limit": "-"},
            "dall-e-2": {"RPM": 10000, "TPM": "-", "Batch Queue Limit": "-"},
            "dall-e-3": {"RPM": 10000, "TPM": "-", "Batch Queue Limit": "-"},
        },
    }

    def __new__(cls, *args, **kwargs):
        return super(TokenUsage, cls).__new__(cls)

    def __init__(self):
        self.lock = threading.Lock()
        self.reset_time = time.time() + 60  # Reset every 60 seconds
        self.current_tier = None
        self.current_model = None
        self.tpm = 0  # Tokens Per Minute
        self.remaining_tokens = 0
        self.batch_queue_limit = "-"
        self.shutdown_event = threading.Event()
        self.load_config()
        self.start_reset_thread()
        self.setup_signal_handlers()

    def load_config(self):
        """
        Load the tier and model from TOKEN_FILE and set TPM accordingly.
        """
        try:
            load_dotenv_once()
        except Exception:
            pass

        # Construct the path relative to the directory of token_usage.py
        config_path = Path(__file__).parent / self.TOKEN_FILE

        if not config_path.exists():
            raise FileNotFoundError(
                f"{self.TOKEN_FILE} does not exist in {Path(__file__).parent}."
            )

        with open(config_path, "r") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error decoding JSON from {self.TOKEN_FILE}: {e}")

        self.current_tier = config.get("tier")
        self.current_model = config.get("model")

        if not self.current_tier or not self.current_model:
            raise ValueError("TOKEN_FILE must contain 'tier' and 'model'.")

        # Fetch TPM and Batch Queue Limit from RATE_LIMITS
        tier_limits = self.RATE_LIMITS.get(self.current_tier)
        if not tier_limits:
            raise ValueError(f"Tier '{self.current_tier}' is not defined.")

        model_limits = tier_limits.get(self.current_model)
        if not model_limits:
            raise ValueError(
                f"Model '{self.current_model}' is not defined in Tier '{self.current_tier}'."
            )

        self.tpm = model_limits["TPM"]
        self.batch_queue_limit = model_limits["Batch Queue Limit"]

        if isinstance(self.tpm, str) and self.tpm == "-":
            self.tpm = 0

        self.remaining_tokens = self.tpm
        print(
            f"[{datetime.now(timezone.utc)}] Loaded configuration: Tier={self.current_tier}, Model={self.current_model}, TPM={self.tpm}"
        )

    def update_tokens(self, tokens_used):
        """
        Decrease the remaining_tokens by tokens_used.
        """
        with self.lock:
            if tokens_used > self.remaining_tokens:
                raise ValueError("Insufficient tokens remaining.")
            self.remaining_tokens -= tokens_used
            print(
                f"[{datetime.now(timezone.utc)}] Tokens used: {tokens_used}. Remaining tokens: {self.remaining_tokens}"
            )

    def get_remaining_tokens(self):
        """
        Return the number of remaining tokens.
        """
        with self.lock:
            return self.remaining_tokens

    def reset_tokens(self):
        """
        Reset remaining_tokens to tpm and restart the reset timer.
        """
        with self.lock:
            self.remaining_tokens = self.tpm
            self.reset_time = time.time() + 60  # Next reset in 60 seconds
            print(
                f"[{datetime.now(timezone.utc)}] Tokens have been reset. Remaining tokens: {self.remaining_tokens}"
            )

    def display_info(self):
        """
        Return the current model, tier, and TPM.
        """
        with self.lock:
            return {
                "Tier": self.current_tier,
                "Model": self.current_model,
                "TPM": self.tpm,
                "Remaining Tokens": self.remaining_tokens,
                "Batch Queue Limit": self.batch_queue_limit,
            }

    def start_reset_thread(self):
        """
        Start a background thread that resets tokens every 60 seconds.
        """
        reset_thread = threading.Thread(
            target=self._reset_tokens_periodically, daemon=True
        )
        reset_thread.start()

    def _reset_tokens_periodically(self):
        """
        Background thread to reset tokens at every reset_time.
        """
        while not self.shutdown_event.is_set():
            current_time = time.time()
            sleep_duration = self.reset_time - current_time
            if sleep_duration > 0:
                # Wait for either the sleep duration or a shutdown event
                shutdown = self.shutdown_event.wait(timeout=sleep_duration)
                if shutdown:
                    break  # Exit the loop if shutdown is signaled
            self.reset_tokens()

    ############################################################
    # Shutdown handling
    ############################################################
    def shutdown(self):
        """
        Signal the background thread to terminate gracefully.
        """
        self.shutdown_event.set()
        print(
            f"[{datetime.now(timezone.utc)}] Shutdown signal received. Terminating TokenUsage."
        )

    def setup_signal_handlers(self):
        """
        Setup signal handlers to gracefully shutdown on termination signals.
        """
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

    def handle_signal(self, signum, frame):
        """
        Handle incoming termination signals by initiating a graceful shutdown.
        """
        print(
            f"[{datetime.now(timezone.utc)}] Received signal {signum}. Initiating graceful shutdown."
        )
        self.shutdown()
