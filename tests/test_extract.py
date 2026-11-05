from jobassist import extract

VAGA = "Dev Júnior. Precisamos de Python e Docker."


def job(*techs):
    return {
        "title": "Dev", "company": None, "seniority": "Júnior", "language": "pt",
        "requirements": [{"text": t, "kind": "tech", "required": True} for t in techs],
    }


def test_tech_literal_ok():
    assert extract.techs_not_in_text(job("Python", "docker"), VAGA) == []


def test_tech_inventada_detectada():
    assert extract.techs_not_in_text(job("Python", "Kubernetes"), VAGA) == ["Kubernetes"]


def test_extract_job_usa_llm(monkeypatch):
    seen = {}

    def fake(prompt, system=None, schema=None):
        seen.update(prompt=prompt, schema=schema)
        return job("Python")

    monkeypatch.setattr(extract, "complete", fake)
    out = extract.extract_job(VAGA)
    assert out["company"] is None and seen["prompt"] == VAGA and seen["schema"] is extract.SCHEMA
