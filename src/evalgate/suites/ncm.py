"""Demo suite shipped with evalgate: extract the NCM code from a Portuguese invoice line.

Exercises the runner end to end before the A and C adapters exist. 20 cases with formatting
traps (dots, spaces, other numbers in the line, two codes where only one is the product).
"""

from __future__ import annotations

import re

from evalgate.suite import Case, Verdict

LINES = [
    ("n01", "Nota: 10 camisetas de algodão, NCM 6109.10.00, valor R$ 300.", "61091000"),
    ("n02", "Venda de arroz polido (NCM 1006.30.21) para supermercado.", "10063021"),
    ("n03", "Item: notebook, classificação fiscal 8471.30.12, garantia 1 ano.", "84713012"),
    ("n04", "Celular smartphone NCM 85171300 quantidade 2", "85171300"),
    ("n05", "Cerveja de malte, código NCM 2203.00.00, caixa com 12 latas", "22030000"),
    ("n06", "Pedido 4471.20.19 — Café torrado em grãos, NCM 0901.21.00, 30 kg.", "09012100"),
    ("n07", "Leite UHT integral 1 L (NCM: 0401.20.10), lote 2026-11.", "04012010"),
    ("n08", "Feijão preto tipo 1, NCM 0713.33.19; CFOP 5102; 50 sacos.", "07133319"),
    ("n09", "Açúcar cristal NCM 1701 14 00 embalagem 5 kg", "17011400"),
    ("n10", "Óleo de soja refinado — NCM 1507.90.11 — 20 caixas de 900 ml", "15079011"),
    ("n11", "Pneu novo para automóvel, NCM 4011.10.00, aro 15, 4 unidades.", "40111000"),
    ("n12", "Geladeira frost free, classificada na NCM 8418.10.00, 1 un.", "84181000"),
    ("n13", "Medicamento genérico (NCM 3004.90.99), registro ANVISA 1.2345.6789.001-1", "30049099"),
    ("n14", "Cimento Portland CP II, NCM 2523.29.10, 100 sacos de 50 kg", "25232910"),
    ("n15", "Sapato social masculino NCM 6403.99.90 tamanho 42", "64039990"),
    ("n16", "Peça: rolamento de esferas, NCM 8482.10.10; ref. fornecedor 6203-2RS", "84821010"),
    ("n17", "Vinho tinto seco 750 ml — NCM 2204.21.00 — safra 2023", "22042100"),
    ("n18", "Frango congelado inteiro, NCM 0207.12.00, 1.200 kg", "02071200"),
    ("n19", "Tecido de algodão tinto, NCM 5208.32.00, 300 metros, largura 1,50 m", "52083200"),
    ("n20", "Bicicleta aro 29 (NCM 8712.00.10), nota fiscal 000.123.456", "87120010"),
]


class NcmSuite:
    name = "ncm-extract"
    version = "1"
    system = (
        "Extraia o código NCM do produto descrito no texto. Responda apenas com os 8 "
        "dígitos, sem pontos nem espaços."
    )

    def prompts(self) -> dict[str, str]:
        return {"ncm-system": self.version}

    def cases(self) -> list[Case]:
        return [Case(id=i, input=t, target=e) for i, t, e in LINES]

    def score(self, case: Case, output) -> Verdict:
        text = str(output or "")
        m = re.search(r"\d{4}[.\s]?\d{2}[.\s]?\d{2}", text)
        got = re.sub(r"\D", "", m.group(0)) if m else ""
        target = case.target if isinstance(case.target, str) else str(case.target)
        return Verdict(
            correct=got == target,
            score=float(got == target),
            answer=got,
            detail={"raw": text[:200]},
        )
