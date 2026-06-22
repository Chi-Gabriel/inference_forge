import argparse
import asyncio
import json
import time
from dataclasses import asdict, dataclass

from app.services.embeddings.qwen import QwenEmbeddingEngine


@dataclass(frozen=True, slots=True)
class Measurement:
    name: str
    batch_size: int
    elapsed_seconds: float
    peak_allocated_gib: float
    peak_reserved_gib: float


def gib(value: int) -> float:
    return value / 1024**3


async def benchmark(args: argparse.Namespace) -> list[Measurement]:
    import torch

    engine = QwenEmbeddingEngine(
        model_id=args.model_id,
        revision=args.revision,
        resident_vram_gib=15.2,
        max_length=args.max_length,
    )
    await engine.prepare_cpu()
    await engine.load_gpu()
    await engine.warmup()

    measurements: list[Measurement] = []
    sample = "Multimodal retrieval benchmark input. " * args.repetitions
    for batch_size in args.batch_sizes:
        torch.cuda.reset_peak_memory_stats()
        started = time.perf_counter()
        await engine.embed([sample] * batch_size)
        elapsed = time.perf_counter() - started
        measurements.append(
            Measurement(
                name="text",
                batch_size=batch_size,
                elapsed_seconds=elapsed,
                peak_allocated_gib=gib(torch.cuda.max_memory_allocated()),
                peak_reserved_gib=gib(torch.cuda.max_memory_reserved()),
            )
        )
    return measurements


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", default="Qwen/Qwen3-VL-Embedding-8B")
    parser.add_argument(
        "--revision", default="2c4565515e0f265c6511776e7193b22c0968ddc7"
    )
    parser.add_argument("--max-length", type=int, default=8192)
    parser.add_argument("--batch-sizes", type=int, nargs="+", default=[1, 2, 4])
    parser.add_argument("--repetitions", type=int, default=32)
    return parser.parse_args()


if __name__ == "__main__":
    results = asyncio.run(benchmark(parse_args()))
    print(json.dumps([asdict(result) for result in results], indent=2))
