# src/ai_coder/setup_config.py
import logging
import os
import threading
from pathlib import Path

# from logging import config
from typing import ClassVar, Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict, Field

from ai_coder.my_utils.env_loader import load_dotenv_once


from ai_coder.my_utils.llm_loader import get_llm_or_init
from ai_coder.my_utils.logger_setup import setup_logger

try:
    load_dotenv_once()
except Exception:
    pass


LOGGER_PROJECT_NAME = "AI_CODER"
DEFAULT_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "prompt.md"
DEFAULT_GITHUB_ISSUE_PATH = DEFAULT_PROMPT_PATH.with_name("github_issue.md")

DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOCKER_IMAGE_NAME = "ai-code-ralph-test-runtime:latest"
DEFAULT_RALPH_DOCKERFILE_PATH = (
    DEFAULT_PROJECT_ROOT / "docker" / "ralph-test-runtime" / "Dockerfile"
)


DEFAULT_DOCKER_BUILD_COMMAND = (
    "docker build -f docker/ralph-test-runtime/Dockerfile "
    "-t ai-code-ralph-test-runtime:latest ."
)


class c_setup_config(BaseModel):
    """Represents setup variables for the ai_coder project."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    llm: Optional[ChatOpenAI] = Field(default=None, description="LLM Configuration.")

    # OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.1")
    openai_model: str = Field(
        default_factory=lambda: c_setup_config.get_env("OPENAI_MODEL", "gpt-5.1"),
        description="Default OpenAI model to use for LLM interactions.",
    )

    testing_flag: bool = Field(
        default_factory=lambda: c_setup_config.env_bool("TESTING_FLAG", False),
        description="Flag to indicate if the application is running in testing mode.",
    )

    logger: Optional[logging.Logger] = Field(
        default=None, description="Logger Configuration."
    )
    ###########################################################################
    # Docker sandbox settings for RALPH
    ###########################################################################
    docker_image_name: str = Field(
        default_factory=lambda: c_setup_config.get_env(
            "RALPH_DOCKER_IMAGE_NAME",
            DEFAULT_DOCKER_IMAGE_NAME,
        ),
        description="Docker image used by the RALPH bind-mount test/runtime sandbox.",
    )

    ralph_dockerfile_path: Path = Field(
        default_factory=lambda: Path(
            c_setup_config.get_env(
                "RALPH_DOCKERFILE_PATH",
                str(DEFAULT_RALPH_DOCKERFILE_PATH),
            )
        ),
        description="Path to the RALPH test/runtime Dockerfile.",
    )

    sandbox_mode: str = Field(
        default_factory=lambda: c_setup_config.get_env(
            "RALPH_SANDBOX_MODE",
            "local",
        ),
        description="Sandbox mode for RALPH. Use 'local' or 'docker'.",
    )

    docker_env_allowlist: tuple[str, ...] = Field(
        default_factory=lambda: ("PYTHONUNBUFFERED",),
        description=(
            "Environment variable names allowed to pass into Docker sandbox commands. "
            "Do not include API keys by default."
        ),
    )

    docker_secret_env_allowlist: tuple[str, ...] = Field(
        default_factory=tuple,
        description=(
            "Secret-like environment variable names allowed to pass into Docker. "
            "Empty by default for the first Docker tracer bullet."
        ),
    )
    ###########################################################################
    # user GitHub Issue for RALPH
    ###########################################################################
    # ISSUE_NUMBER=1
    issue_number: int = Field(
        default_factory=lambda: c_setup_config.env_int("ISSUE_NUMBER", 0),
        description="Optional user-provided GitHub issue number for RALPH.",
    )

    # ISSUE_TITLE=""The title of the issue to use for the RALPH agent."
    issue_title: str = Field(
        default_factory=lambda: c_setup_config.get_env("ISSUE_TITLE", ""),
        description="Optional user-provided GitHub issue title for RALPH.",
    )

    # ISSUE_BODY="Build fake issue input to mock agent completion flow. This will help us test the end-to-end flow of the RALPH agent without relying on actual GitHub issues. The issue body should include a clear description of the task, any relevant details, and specific requirements for the agent to complete the task successfully."
    issue_body: str = Field(
        default_factory=lambda: c_setup_config.get_env("ISSUE_BODY", ""),
        description="Optional user-provided GitHub issue body for RALPH.",
    )
    ###########################################################################
    # END OF user GitHub Issue for RALPH
    ###########################################################################
    github_issue_path: Path = Field(
        default_factory=lambda: c_setup_config.resolve_github_issue_path(),
        description="Path to the local fallback GitHub issue markdown file.",
    )

    # LABEL="tracer bullet"
    label: str = Field(
        default_factory=lambda: c_setup_config.get_env("LABEL", "tracer bullet"),
        description="The label to use for the RALPH agent.",
    )

    # MAX_ITERATIONS=3
    max_iterations: int = Field(
        default_factory=lambda: c_setup_config.env_int("MAX_ITERATIONS", 3),
        description="The maximum number of iterations for the RALPH agent.",
    )

    # PROMPTH_PATH : DEFAULT_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "prompt.md"
    prompt_path: Path = Field(
        default_factory=lambda: Path(
            c_setup_config.get_env("PROMPT_PATH", str(DEFAULT_PROMPT_PATH))
        ),
        description="Path to the RALPH prompt markdown file.",
    )

    ##################################################################
    # Static Functions
    ##################################################################
    _instance: ClassVar[Optional["c_setup_config"]] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()

    @staticmethod
    def get_env(name: str, default: str | None = None) -> str:
        value = os.getenv(name, default)
        if value is None:
            raise ValueError(f"Missing required environment variable: {name}")
        return str(value).strip().strip("'\"")

    @staticmethod
    def get_required_env(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"Missing required environment variable: {name}")
        return value.strip().strip("'\"")

    @staticmethod
    def env_bool(name: str, default: bool = False) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "y", "on"}

    @staticmethod
    def env_int(name: str, default: int) -> int:
        raw = os.getenv(name)
        if raw is None or not raw.strip():
            return default
        return int(raw.strip().strip("'\""))

    @staticmethod
    def resolve_github_issue_path() -> Path:
        base_path = Path(
            c_setup_config.get_env(
                "GITHUB_ISSUE_PATH",
                str(DEFAULT_GITHUB_ISSUE_PATH),
            )
        )

        issue_dir = c_setup_config.get_env("GITHUB_ISSUE_DIR", "")
        issue_file_name = c_setup_config.get_env(
            "GITHUB_ISSUE_FILE_NAME",
            "",
        )

        if issue_dir and issue_file_name:
            return Path(issue_dir) / issue_file_name

        if issue_dir:
            return Path(issue_dir) / base_path.name

        if issue_file_name:
            return base_path.with_name(issue_file_name)

        return base_path

    def has_user_github_issue(self) -> bool:
        return (
            self.issue_number > 0
            or bool(self.issue_title.strip())
            or bool(self.issue_body.strip())
        )

    ##################################################################
    # set and get Functions
    ##################################################################
    def set_logger(self, logger: logging.Logger) -> None:
        self.logger = logger

    def get_logger(self) -> logging.Logger:
        if self.logger is None:

            # Avoid import-time failures: lazily create a logger the first time it's requested.
            self.logger = setup_logger(LOGGER_PROJECT_NAME)
            self.logger.info("logger Started!")
        return self.logger

    def get_llm(self) -> ChatOpenAI:
        """Return initialized LLM, initializing it once if needed."""
        if self.llm is None:
            self.llm = get_llm_or_init(
                self,
                temperature=0.0,
                streaming=True,
            )
        return self.llm

    def i_setup_config_set_sandbox_mode(self, sandbox_mode: str) -> None:
        cleaned_mode = sandbox_mode.strip().lower()
        if cleaned_mode not in {"local", "docker"}:
            raise ValueError("sandbox_mode must be 'local' or 'docker'.")
        self.sandbox_mode = cleaned_mode

    ############################################################################
    # Validation and Utility Functions
    ############################################################################
    def validate_initialization(
        self,
        *,
        require_llm: bool = False,
        require_docker: bool = False,
    ) -> None:
        logger = self.get_logger()
        logger.info("Validating configuration initialization...")
        if require_docker:
            self.validate_docker_configuration()

        self.validate_sandbox_mode()

        if self.has_user_github_issue():
            if self.issue_number < 1:
                logger.error(
                    "ISSUE_NUMBER must be a positive integer when a user issue is provided."
                )
                raise ValueError(
                    "ISSUE_NUMBER must be a positive integer when a user issue is provided."
                )

            if not self.issue_title.strip():
                logger.error(
                    "ISSUE_TITLE cannot be empty when a user issue is provided."
                )
                raise ValueError(
                    "ISSUE_TITLE cannot be empty when a user issue is provided."
                )

            if not self.issue_body.strip():
                logger.error(
                    "ISSUE_BODY cannot be empty when a user issue is provided."
                )
                raise ValueError(
                    "ISSUE_BODY cannot be empty when a user issue is provided."
                )

            if not self.label.strip():
                logger.error("LABEL cannot be empty when a user issue is provided.")
                raise ValueError("LABEL cannot be empty when a user issue is provided.")

        if self.max_iterations < 1:
            logger.error("MAX_ITERATIONS must be at least 1.")
            raise ValueError("MAX_ITERATIONS must be at least 1.")

        if not self.openai_model.strip():
            logger.error("OPENAI_MODEL cannot be empty.")
            raise ValueError("OPENAI_MODEL cannot be empty.")

        if not self.prompt_path.exists():
            logger.error("PROMPT_PATH does not exist: %s", self.prompt_path)
            raise ValueError(f"PROMPT_PATH does not exist: {self.prompt_path}")

        if not require_llm:
            return

        apikey = os.getenv("OPENAI_API_KEY", "").strip()
        if not apikey:
            logger.error("OPENAI_API_KEY environment variable not set")
            raise ValueError("OPENAI_API_KEY environment variable not set")

        if len(apikey) < 20:
            logger.error("OPENAI_API_KEY looks too short to be valid")
            raise ValueError("OPENAI_API_KEY looks too short to be valid")

        if self.llm is None:
            self.get_llm()

        if not self.docker_image_name.strip():
            logger.error("RALPH_DOCKER_IMAGE_NAME cannot be empty.")
            raise ValueError("RALPH_DOCKER_IMAGE_NAME cannot be empty.")

        if not self.ralph_dockerfile_path.exists():
            logger.error(
                "RALPH_DOCKERFILE_PATH does not exist: %s",
                self.ralph_dockerfile_path,
            )
            raise ValueError(
                f"RALPH_DOCKERFILE_PATH does not exist: {self.ralph_dockerfile_path}"
            )

    def to_dict(self) -> dict:
        """Return a safe dictionary representation of the configuration."""
        return {
            "testing_flag": self.testing_flag,
            "openai_model": self.openai_model,
            "issue_number": self.issue_number,
            "issue_title": self.issue_title,
            "issue_body": self.issue_body,
            "has_user_github_issue": self.has_user_github_issue(),
            "label": self.label,
            "max_iterations": self.max_iterations,
            "prompt_path": str(self.prompt_path),
            "logger_initialized": self.logger is not None,
            "llm_initialized": self.llm is not None,
            "github_issue_path": str(self.github_issue_path),
            "docker_image_name": self.docker_image_name,
            "ralph_dockerfile_path": str(self.ralph_dockerfile_path),
            "docker_build_command": self.get_docker_build_command(),
            "docker_env_allowlist": list(self.docker_env_allowlist),
            "docker_secret_env_allowlist": list(self.docker_secret_env_allowlist),
        }

    def get_docker_build_command(self) -> str:
        """Return the manual Docker build command for the RALPH test/runtime image."""
        return (
            f"docker build -f {self.ralph_dockerfile_path} "
            f"-t {self.docker_image_name} ."
        )

    def __repr__(self) -> str:
        short_issue_body = self.issue_body
        if len(short_issue_body) > 80:
            short_issue_body = short_issue_body[:77] + "..."

        return (
            "c_setup_config("
            f"testing_flag={self.testing_flag!r}, "
            f"openai_model={self.openai_model!r}, "
            f"issue_number={self.issue_number!r}, "
            f"issue_title={self.issue_title!r}, "
            f"issue_body={short_issue_body!r}, "
            f"has_user_github_issue={self.has_user_github_issue()!r}, "
            f"label={self.label!r}, "
            f"max_iterations={self.max_iterations!r}, "
            f"prompt_path={str(self.prompt_path)!r}, "
            f"github_issue_path={str(self.github_issue_path)!r}, "
            f"logger={'Initialized' if self.logger else 'Not Initialized'}, "
            f"llm={'Initialized' if self.llm else 'Not Initialized'}",
            f"docker_image_name={self.docker_image_name!r}, "
            f"ralph_dockerfile_path={str(self.ralph_dockerfile_path)!r}, "
            ")",
        )

    ###########################################################################
    # Validation Functions
    ###########################################################################
    def validate_docker_configuration(self) -> None:
        logger = self.get_logger()

        if not self.docker_image_name.strip():
            logger.error("RALPH_DOCKER_IMAGE_NAME cannot be empty.")
            raise ValueError("RALPH_DOCKER_IMAGE_NAME cannot be empty.")

        if not self.ralph_dockerfile_path.exists():
            logger.error(
                "RALPH_DOCKERFILE_PATH does not exist: %s",
                self.ralph_dockerfile_path,
            )
            raise ValueError(
                f"RALPH_DOCKERFILE_PATH does not exist: {self.ralph_dockerfile_path}"
            )

    def validate_sandbox_mode(self) -> None:
        allowed_modes = {"local", "docker"}
        if self.sandbox_mode not in allowed_modes:
            raise ValueError("RALPH_SANDBOX_MODE must be 'local' or 'docker'.")

    # Thread Safety for Singleton:
    @classmethod
    def get_instance(cls) -> "c_setup_config":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
