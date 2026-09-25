from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import main as project_main
from src.narration import engine
from src.narration.providers import ProviderError, ProviderResult


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_PATH = ROOT / "tests" / "audiovisual_pilot_s001_s006_v2_wordboundary" / "timing" / "boundaries" / "B001.json"
BOUNDARY = json.loads(BOUNDARY_PATH.read_text(encoding="utf-8"))
AUDIO_PATH = ROOT / BOUNDARY["audio_file"]


def sdk_result() -> ProviderResult:
    return ProviderResult(
        audio_data=AUDIO_PATH.read_bytes(),
        sample_rate=BOUNDARY["sample_rate"],
        boundaries=BOUNDARY["words"],
        metadata={
            "timing_quality": "WORD_BOUNDARY_REAL",
            "sdk_package": BOUNDARY["sdk_package"],
            "synthesis_id": BOUNDARY["synthesis_id"],
        },
    )


class NarrationEngineSmokeTest(unittest.TestCase):
    def test_main_narracao_defaults_to_sdk_for_one_beat(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".tmp-narration-smoke-", dir=ROOT) as temporary:
            target = Path(temporary)
            output = target / "b001.wav"
            timing_path = target / "b001_timing.json"
            raw_dir = target / "raw"
            raw_combined = target / "raw" / "combined.wav"
            with (
                mock.patch.object(engine.config, "load_env", return_value={}),
                mock.patch.object(engine.config, "azure_credentials", return_value=("test-key", "test-region")),
                mock.patch.object(engine.azure_sdk, "synthesize", return_value=sdk_result()) as sdk,
                mock.patch.object(engine.azure_rest, "synthesize") as rest,
                mock.patch.object(engine.local_kokoro, "synthesize") as local,
            ):
                exit_code = project_main.main([
                    "narracao",
                    "--entrada", str(ROOT / "README.md"),
                    "--beats", "B001",
                    "--saida", str(output),
                    "--timing-json", str(timing_path),
                    "--raw-dir", str(raw_dir),
                    "--raw-combined", str(raw_combined),
                    "--no-processing",
                ])

            self.assertEqual(exit_code, 0)
            sdk.assert_called_once()
            rest.assert_not_called()
            local.assert_not_called()
            timing = json.loads(timing_path.read_text(encoding="utf-8"))
            self.assertEqual(timing["provider"], "azure_speech_sdk")
            self.assertEqual(timing["timing_quality"], "WORD_BOUNDARY_REAL")
            self.assertGreater(len(timing["beats"][0]["words"]), 0)
            self.assertEqual(timing["anti_atropelamento"]["speech_overlap"], 0)
            self.assertEqual(timing["beats"][0]["synthesis_id"], BOUNDARY["synthesis_id"])
            self.assertEqual(timing["beats"][0]["provider_metadata"]["synthesis_id"], BOUNDARY["synthesis_id"])
            self.assertTrue(output.is_file())

    def test_sdk_failure_does_not_fallback_silently(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".tmp-narration-failure-", dir=ROOT) as temporary:
            target = Path(temporary)
            with (
                mock.patch.object(engine.config, "azure_credentials", return_value=("test-key", "test-region")),
                mock.patch.object(engine.azure_sdk, "synthesize", side_effect=ProviderError("sdk failure")),
                mock.patch.object(engine.azure_rest, "synthesize") as rest,
                mock.patch.object(engine.local_kokoro, "synthesize") as local,
            ):
                with self.assertRaises(engine.NarrationError):
                    engine.run_narration(
                        input_path=ROOT / "README.md",
                        beats="B001",
                        output_path=target / "failed.wav",
                        timing_path=target / "failed.json",
                        raw_dir=target / "raw",
                        raw_combined_path=target / "raw" / "combined.wav",
                        provider="azure_sdk",
                        no_processing=True,
                    )
            rest.assert_not_called()
            local.assert_not_called()


if __name__ == "__main__":
    unittest.main()
