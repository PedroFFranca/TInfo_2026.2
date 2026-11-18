import argparse
import heapq
import math
import struct
from collections import Counter


MAGICA = b"HUFF"


class Node:
    def __init__(self, char, freq, left=None, right=None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other):
        return self.freq < other.freq


def build_huffman_tree(contagens: Counter) -> Node | None:
    if not contagens:
        return None

    heap = [Node(char, freq) for char, freq in contagens.items()]
    heapq.heapify(heap)

    # Arquivo com um único símbolo: cria um nó pai com um filho só,
    # para que esse símbolo ganhe um código de 1 bit ("0").
    if len(heap) == 1:
        only = heapq.heappop(heap)
        return Node(None, only.freq, left=only)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = Node(None, left.freq + right.freq, left, right)
        heapq.heappush(heap, merged)

    return heap[0]


def build_codes(root: Node | None) -> dict[int, str]:
    if not root:
        return {}

    codes: dict[int, str] = {}

    def traverse(node: Node, current_code: str):
        if node.char is not None:
            codes[node.char] = current_code or "0"
            return
        if node.left:
            traverse(node.left, current_code + "0")
        if node.right:
            traverse(node.right, current_code + "1")

    traverse(root, "")
    return codes


def entropia(contagens: Counter, total: int) -> float:
    if total == 0:
        return 0.0
    # max(0.0, ...) evita imprimir -0.0 quando há um único símbolo
    return max(0.0, -sum((c / total) * math.log2(c / total) for c in contagens.values()))


def comprimento_medio(contagens: Counter, codes: dict[int, str], total: int) -> float:
    if total == 0:
        return 0.0
    return sum((c / total) * len(codes[s]) for s, c in contagens.items())


def bits_para_bytes(bits: str) -> tuple[bytes, int]:
    padding = (-len(bits)) % 8
    bits += "0" * padding
    dados = bytearray(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
    return bytes(dados), padding


def cabecalho(tamanho: int, padding: int, contagens: Counter) -> bytes:
    # A ordem é a de aparição no arquivo. O heap desempata só pela
    # frequência, então a descompactação tem de montar a lista igual.
    partes = [MAGICA, struct.pack("<QBH", tamanho, padding, len(contagens))]
    for simbolo, freq in contagens.items():
        partes.append(struct.pack("<BQ", simbolo, freq))
    return b"".join(partes)


def bytes_para_bits(dados: bytes, padding: int) -> str:
    bits = "".join(f"{b:08b}" for b in dados)
    if padding:
        bits = bits[:-padding]
    return bits


def ler_cabecalho(blob: bytes) -> tuple[int, int, Counter, bytes]:
    if len(blob) < 15 or blob[:4] != MAGICA:
        raise SystemExit("arquivo compactado inválido")
    tamanho, padding, n = struct.unpack_from("<QBH", blob, 4)
    if padding > 7 or n > 256:
        raise SystemExit("cabeçalho inválido")
    offset = 15
    contagens: Counter = Counter()
    for _ in range(n):
        if offset + 9 > len(blob):
            raise SystemExit("cabeçalho truncado")
        simbolo, freq = struct.unpack_from("<BQ", blob, offset)
        offset += 9
        contagens[simbolo] = freq
    if sum(contagens.values()) != tamanho:
        raise SystemExit("frequências não batem com o tamanho original")
    return tamanho, padding, contagens, blob[offset:]


def huffman_decode(bits: str, root: Node, tamanho: int) -> bytes:
    decoded = bytearray()
    curr = root
    for bit in bits:
        curr = curr.left if bit == "0" else curr.right
        if curr is None:
            raise SystemExit("arquivo compactado corrompido")
        if curr.char is not None:
            decoded.append(curr.char)
            if len(decoded) == tamanho:
                break
            curr = root
    if len(decoded) != tamanho:
        raise SystemExit("não foi possível recuperar todos os bytes")
    return bytes(decoded)


def descompactar(blob: bytes) -> bytes:
    tamanho, padding, contagens, payload = ler_cabecalho(blob)
    if tamanho == 0:
        return b""
    root = build_huffman_tree(contagens)
    bits = bytes_para_bits(payload, padding)
    return huffman_decode(bits, root, tamanho)


def compactar(data: bytes) -> tuple[bytes, Counter, dict[int, str]]:
    contagens = Counter(data)
    root = build_huffman_tree(contagens)
    codes = build_codes(root)
    bits = "".join(codes[b] for b in data)
    payload, padding = bits_para_bytes(bits)
    return cabecalho(len(data), padding, contagens) + payload, contagens, codes


def destino_descompactado(caminho: str) -> str:
    if caminho.endswith(".huff"):
        return caminho[:-5]
    return caminho + ".out"


def main():
    parser = argparse.ArgumentParser(description="Compactador de arquivos por Huffman")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("-c", dest="comprimir", metavar="ARQUIVO",
                       help="compacta o arquivo e gera ARQUIVO.huff")
    grupo.add_argument("-d", dest="descomprimir", metavar="ARQUIVO",
                       help="descompacta o .huff e restaura o arquivo original")
    args = parser.parse_args()

    if args.comprimir:
        with open(args.comprimir, "rb") as f:
            data = f.read()
        saida, contagens, codes = compactar(data)
        destino = args.comprimir + ".huff"
        with open(destino, "wb") as f:
            f.write(saida)
        total = len(data)
        print(f"Arquivo gerado: {destino}")
        print(f"Entropia estimada (H): {entropia(contagens, total):.4f} bits/símbolo")
        print(f"Comprimento médio (L): {comprimento_medio(contagens, codes, total):.4f} bits/símbolo")
        print(f"Taxa de compressão: {total / len(saida):.4f}")
        return
    else:
        with open(args.descomprimir, "rb") as f:
            blob = f.read()
        data = descompactar(blob)
        destino = destino_descompactado(args.descomprimir)
        with open(destino, "wb") as f:
            f.write(data)
        print(f"Arquivo gerado: {destino}")
    

if __name__ == "__main__":
    main()
