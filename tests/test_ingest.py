import numpy as np
import pytest

from jobassist import ingest as ing


@pytest.fixture
def setup(tmp_path, monkeypatch):
    calls = []

    def fake_embed(texts, kind="passage"):
        calls.append(list(texts))
        return np.tile(np.array([1.0, 0.0], dtype=np.float32), (len(texts), 1))

    monkeypatch.setattr(ing, "embed", fake_embed)
    monkeypatch.setattr(ing, "provider_id", lambda: "fake:v1")
    mat = tmp_path / "mat"
    mat.mkdir()
    (mat / "a.md").write_text("Texto do arquivo A.", encoding="utf-8")
    (mat / "b.md").write_text("Texto do arquivo B.", encoding="utf-8")
    return mat, tmp_path / "i.db", calls


def test_segunda_rodada_nao_recalcula(setup):
    mat, db, calls = setup
    assert ing.ingest(mat, db) == {"novos": 2, "inalterados": 0, "removidos": 0}
    assert ing.ingest(mat, db) == {"novos": 0, "inalterados": 2, "removidos": 0}
    assert len(calls) == 1  # só a primeira rodada chamou o embedding


def test_alterar_um_arquivo_reindexa_so_ele(setup):
    mat, db, calls = setup
    ing.ingest(mat, db)
    (mat / "a.md").write_text("Texto NOVO do arquivo A.", encoding="utf-8")
    assert ing.ingest(mat, db) == {"novos": 1, "inalterados": 1, "removidos": 0}
    assert calls[-1] == ["Texto NOVO do arquivo A."]
    ids, texts, _ = ing.load_index(db)
    assert "Texto NOVO do arquivo A." in texts and "Texto do arquivo A." not in texts


def test_arquivo_removido_sai_do_indice(setup):
    mat, db, _ = setup
    ing.ingest(mat, db)
    (mat / "b.md").unlink()
    assert ing.ingest(mat, db)["removidos"] == 1
    assert ing.load_index(db)[0] == ["a.md#c1"]


def test_load_index_formato(setup):
    mat, db, _ = setup
    assert ing.load_index(db) is None
    ing.ingest(mat, db)
    ids, texts, m = ing.load_index(db)
    assert ids == ["a.md#c1", "b.md#c1"] and m.shape == (2, 2) and m.dtype == np.float32


def test_recusa_misturar_provedores(setup, monkeypatch):
    mat, db, _ = setup
    ing.ingest(mat, db)
    monkeypatch.setattr(ing, "provider_id", lambda: "fake:v2")
    with pytest.raises(RuntimeError, match="--rebuild"):
        ing.ingest(mat, db)
    assert ing.ingest(mat, db, rebuild=True)["novos"] == 2


def test_indice_antigo_sem_marca_do_chunker_e_refeito(setup, capsys):
    import sqlite3
    mat, db, calls = setup
    ing.ingest(mat, db)
    con = sqlite3.connect(db)
    con.execute("DELETE FROM meta WHERE key='chunker'")  # simula um índice criado antes da marca existir
    con.commit(); con.close()
    assert ing.ingest(mat, db)["novos"] == 2  # tudo reindexado, mesmo com arquivos inalterados
    assert "refazendo o índice" in capsys.readouterr().err and len(calls) == 2


def test_mudanca_de_versao_do_chunker_refaz_o_indice(setup, monkeypatch, capsys):
    mat, db, calls = setup
    ing.ingest(mat, db)
    assert ing.ingest(mat, db)["novos"] == 0  # mesma versão: incremental, nada a fazer
    monkeypatch.setattr(ing, "CHUNKER_VERSION", 99)
    assert ing.ingest(mat, db)["novos"] == 2 and "v2 para v99" in capsys.readouterr().err
    assert ing.ingest(mat, db)["novos"] == 0  # e a nova versão fica registrada


def test_indice_novo_nao_avisa_nada(setup, capsys):
    mat, db, _ = setup
    ing.ingest(mat, db)
    assert "refazendo" not in capsys.readouterr().err


# ---------- cache do índice em memória ----------

def test_load_index_reaproveita_a_leitura_enquanto_o_arquivo_nao_muda(setup):
    mat, db, _ = setup
    ing.ingest(mat, db)
    a, b = ing.load_index(db), ing.load_index(db)
    assert a is b  # mesma leitura, sem ir ao SQLite de novo
    assert ing.load_index(db, use_cache=False) is not a  # mas dá para forçar a leitura a frio


def test_load_index_percebe_que_o_arquivo_mudou(setup):
    mat, db, _ = setup
    ing.ingest(mat, db)
    antes = ing.load_index(db)
    (mat / "c.md").write_text("Texto novo do arquivo C.", encoding="utf-8")
    ing.ingest(mat, db)
    depois = ing.load_index(db)
    assert depois is not antes and "c.md#c1" in depois[0] and "c.md#c1" not in antes[0]


def test_load_index_nao_serve_cache_de_arquivo_apagado_ou_vazio(setup, tmp_path):
    mat, db, _ = setup
    ing.ingest(mat, db)
    assert ing.load_index(db) is not None
    db.unlink()
    assert ing.load_index(db) is None
    vazio = tmp_path / "vazio.db"
    ing.ingest(tmp_path / "nada", vazio) if False else None  # índice sem nenhum trecho
    import sqlite3
    sqlite3.connect(vazio).executescript(ing.SCHEMA)
    assert ing.load_index(vazio) is None


def test_matriz_carregada_tem_o_formato_e_os_valores_certos(setup):
    mat, db, _ = setup
    ing.ingest(mat, db)
    ids, texts, m = ing.load_index(db, use_cache=False)
    assert m.shape == (len(ids), 2) and m.dtype == np.float32 and np.allclose(m, [[1.0, 0.0]] * len(ids))
