# src/ai_coder/docker_sandbox_provider/docker_sandbox_provider.py

"""

DockerSandboxProvider
DockerSandboxHandle
i_dockersandbox_check_image()
i_dockersandbox_create()
"""

DEFAULT_DOCKER_IMAGE_NAME = "ai-code-ralph-test-runtime:latest"
DOCKER_BUILD_COMMAND = (
    "docker build -f docker/ralph-test-runtime.Dockerfile "
    "-t ai-code-ralph-test-runtime:latest ."
)


class DockerSandboxProvider:
    def __init__(self, image_name: str = DEFAULT_DOCKER_IMAGE_NAME) -> None:
        self.image_name = image_name
