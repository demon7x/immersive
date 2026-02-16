from pathlib import Path

from app.colab_render import main


def test_colab_pipeline_smoke(tmp_path: Path) -> None:
    out = tmp_path / "smoke.gif"
    rc = main(
        [
            "--duration-s",
            "1.0",
            "--fps",
            "10",
            "--width",
            "320",
            "--height",
            "180",
            "--format",
            "gif",
            "--path-type",
            "orbit",
            "--out",
            str(out),
        ]
    )

    assert rc == 0
    assert out.exists()
    assert out.stat().st_size > 0
