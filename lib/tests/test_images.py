import tomllib

import pytest

from botelo.images import affected, dockerfile, plan, smoke_lines, write_context
from botelo.registry import parse

TOML = """
[images.base]
engines = ["sf", "lc0"]

[images.extra]
parent = "base"
engines = ["old"]

[engines.sf.commands]
sf = { run = "sf/stockfish", expect = "classical" }

[engines.lc0]
runtime = ["zlib1g", "libopenblas0"]
[engines.lc0.commands]
lc0 = { run = "lc0/lc0", smoke = false }
maia = { run = "lc0/lc0 --weights=/opt/engines/maia.pb.gz", go = "go nodes 1" }

[engines.old.commands]
old-1ply = { run = "old/old -ply 1", go = "go" }
"""


@pytest.fixture
def registry():
    return parse(tomllib.loads(TOML))


def test_plan(registry):
    assert plan(registry, "base") == [("engine", "sf"), ("engine", "lc0"), ("image", "base")]
    assert plan(registry, "extra") == [
        ("engine", "sf"), ("engine", "lc0"), ("engine", "old"), ("image", "base"), ("image", "extra"),
    ]
    assert plan(registry, "test-old") == [("engine", "old"), ("test", "old")]
    for target in ("nothing", "test-nothing"):
        with pytest.raises(KeyError):
            plan(registry, target)


def test_dockerfile_root(registry):
    text = dockerfile(registry, ["sf", "lc0"], None, "bot-elo-estimator-base")
    assert "ARG BASE=ubuntu:26.04\nFROM bot-elo-estimator-engine-sf AS sf\nFROM bot-elo-estimator-engine-lc0 AS lc0\n" in text
    assert "\nFROM ${BASE}\n" in text
    assert "apt-get install -y --no-install-recommends libopenblas0 zlib1g" in text
    assert "COPY --from=sf /opt/engines/ /opt/engines/\nCOPY --from=lc0 /opt/engines/ /opt/engines/\n" in text
    assert "ENV PATH=/opt/engines/bin:" in text
    assert text.endswith('RUN smoke_test\n\nCMD ["bash"]\n')


def test_dockerfile_child(registry):
    text = dockerfile(registry, ["old"], "base", "bot-elo-estimator-extra")
    assert "ARG PARENT=bot-elo-estimator-base\n" in text and "\nFROM ${PARENT}\n" in text
    assert "apt-get" not in text and "ENV PATH" not in text


def test_smoke_lines(registry):
    assert smoke_lines(registry, ["sf", "lc0", "old"]) == (
        "sf\tgo depth 10\tclassical\nmaia\tgo nodes 1\nold-1ply\tgo\n"
    )


def test_write_context(registry, tmp_path):
    assert write_context(registry, "image", "extra", tmp_path / "extra") == "bot-elo-estimator-extra"
    files = sorted(str(p.relative_to(tmp_path / "extra")) for p in (tmp_path / "extra").rglob("*") if p.is_file())
    assert files == ["Dockerfile", "bin/old-1ply", "smoke/extra.tsv"]
    assert write_context(registry, "test", "lc0", tmp_path / "lc0") == "bot-elo-estimator-test-lc0"
    wrapper = tmp_path / "lc0" / "bin" / "maia"
    assert wrapper.read_text() == '#!/bin/sh\nexec /opt/engines/lc0/lc0 --weights=/opt/engines/maia.pb.gz "$@"\n'
    assert wrapper.stat().st_mode & 0o111
    assert (tmp_path / "lc0" / "bin" / "smoke_test").is_file()
    assert (tmp_path / "lc0" / "smoke" / "lc0.tsv").read_text() == "maia\tgo nodes 1\n"


OLD = tomllib.loads(TOML)


def edited(**changes):
    new = tomllib.loads(TOML)
    for path, value in changes.items():
        table = new
        *keys, last = path.split("__")
        for key in keys:
            table = table[key]
        table[last] = value
    return new


@pytest.mark.parametrize("old, new, changed, full, expected", [
    # Nothing changed.
    (OLD, OLD, ["README.md"], False, ([], False)),
    # An engine's folder.
    (OLD, OLD, ["images/engines/old/Dockerfile"], False, (["old"], False)),
    # An engine's table, and after the merge the images build too.
    (OLD, edited(engines__lc0__runtime=["zlib1g"]), ["bots.toml"], False, (["lc0"], False)),
    (OLD, edited(engines__lc0__runtime=["zlib1g"]), ["bots.toml"], True, (["lc0"], True)),
    # A bot alone builds nothing.
    (OLD, edited(bots={"x": {"runs": "X"}}), ["bots.toml"], True, ([], False)),
    # A new engine in an image builds the engine; the images build after the merge.
    (OLD, edited(engines__new={"commands": {"n": {"run": "n/n"}}}, images__extra__engines=["old", "new"]),
     ["bots.toml", "images/engines/new/Dockerfile"], False, (["new"], False)),
    (OLD, edited(engines__new={"commands": {"n": {"run": "n/n"}}}, images__extra__engines=["old", "new"]),
     ["bots.toml", "images/engines/new/Dockerfile"], True, (["new"], True)),
    # A new parent changes every image after it.
    (OLD, edited(images__extra__parent=None), ["bots.toml"], False, ([], True)),
    # What every build shares.
    (OLD, OLD, ["images/common/smoke_test.sh"], False, (["lc0", "old", "sf"], True)),
    (OLD, OLD, ["build_docker.sh"], False, (["lc0", "old", "sf"], True)),
    # No registry before.
    (None, OLD, [], False, (["lc0", "old", "sf"], True)),
])
def test_affected(old, new, changed, full, expected):
    result = affected(old, new, changed, full)
    assert (result["engines"], result["images"]) == expected
