import argparse
import math
import random
from collections import Counter

matricula_pedro = 232006028
matricula_henrique = 222025039

def parametros() -> tuple[int, int, float]:
    m = (matricula_henrique + matricula_pedro) % 100
    k = 4 + m % 5
    r = 0.55 + 0.02 * ((m // 5) % 10)
    return m, k, r


def distribuicao(k: int, r: float) -> list[float]:
    return [r**i * (1 - r) / (1 - r**k) for i in range(k)]

def gerar(p: list[float],tamanho=5000000, seed=42) -> bytes:
    rng = random.Random(seed)
    return bytes(rng.choices(range(len(p)), weights=p, k=tamanho))


def main():
    m, k, r = parametros()
    p = distribuicao(k, r)
    dados = gerar(p=p)
    with open("data/fonte_sintetica.bin", "wb") as f:
        f.write(dados)

    print(f"m = {m}, k = {k}, r = {r:.2f}")
    print("p_i =", ", ".join(f"{x:.6f}" for x in p))
    print(f"Arquivo gerado: data/fonte_sintetica.bin ({len(dados)} bytes)")


if __name__ == "__main__":
    main()