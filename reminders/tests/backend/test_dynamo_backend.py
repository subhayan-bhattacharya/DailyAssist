import pytest


@pytest.fixture(scope='session')
def docker_compose_files(pytestconfig):
    """Get the docker-compose.yml absolute path.
    Override this fixture in your tests if you need a custom location.
    """
    return [
        pytestconfig.invocation_dir / "tests/backend/docker-compose.yml"
    ]


@pytest.fixture(scope='session')
def docker_app(docker_services):
    docker_services.start('dynamodb-local')
    public_port = docker_services.wait_for_service("dynamodb-local", 8000)
    url = "http://{docker_services.docker_ip}:{public_port}".format(**locals())
    return url


def test_dynamo_backend(docker_app):
    """Dummy test."""
    pass
