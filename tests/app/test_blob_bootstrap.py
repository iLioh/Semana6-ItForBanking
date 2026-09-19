from types import SimpleNamespace

from src.app import blob_bootstrap


def test_bootstrap_uploads_only_four_and_deletes_only_exact_legacy(monkeypatch) -> None:
    names = {"reactiva_anonimizada.csv", "complaints_golden.csv", "keep-me.csv"}
    uploaded = []
    deleted = []

    class Container:
        def list_blobs(self):
            return [SimpleNamespace(name=name) for name in names]

        def delete_blob(self, name):
            deleted.append(name)
            names.remove(name)

    class Storage:
        def __init__(self, settings):
            self.client = SimpleNamespace(get_container_client=lambda _: Container())

        def upload_prepared_if_absent(self, name, content):
            assert content
            uploaded.append(name)
            names.add(name)

    monkeypatch.setattr(blob_bootstrap, "PrivateBlobStorage", Storage)
    monkeypatch.setattr(blob_bootstrap, "get_settings", lambda: object())
    blob_bootstrap.bootstrap_official_blobs()
    assert set(uploaded) == set(blob_bootstrap.FILES)
    assert set(deleted) == set(blob_bootstrap.LEGACY)
    assert "keep-me.csv" in names
