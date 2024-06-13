from typer.testing import CliRunner

from src.assign_images import app

runner = CliRunner(mix_stderr=False)


def test_help():
    """Test the CLI with --help flag."""
    result = runner.invoke(app, ["--help"])
    print(result.output)
    assert result.exit_code == 0
    assert "Assigns Images to Points" in result.output
