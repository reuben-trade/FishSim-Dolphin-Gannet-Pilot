# Source provenance and third-party notices

This standalone research notebook package was assembled from the FishSim-RL research workspace on 9 November 2026 (Australia/Perth). The original project repository is https://github.com/reuben-trade/FishSim-RL and its recorded upstream is https://github.com/yangyushi/FishSim. The notebook, study controllers, sealed case evidence and analysis accompany the dolphin–gannet pilot.

The frozen source closure preserves original file content and notices. INPUT_MANIFEST.json records protected file hashes; the historical case completion seals remain unchanged. Some historical manifests contain absolute authoring-machine paths as provenance. They are not required as runtime destinations: the optional runner relocates copied JSON paths and records the relocation. No credentials or Git authentication files are part of this package.

No top-level LICENSE or COPYING file was present in the source workspace at packaging time. This package does not assign a new blanket license to the inherited project, third-party code, or study data. Retained notices apply to their respective files.

Third-party source and license texts are included intact:

- pybind11: frozen_model/extern/pybind11/LICENSE (BSD three-clause terms, copyright Wenzel Jakob and contributors).
- Eigen: frozen_model/extern/eigen3/COPYING.README and COPYING.MPL2, with additional COPYING.* texts for the third-party portions identified in their source headers. Eigen describes its primary license as MPL 2.0.
- Additional attribution links/comments in the original FishSim Python source remain intact.

The historical native binary is supplied with the complete corresponding frozen C++ source and vendored dependencies. [NATIVE_SETUP.md](NATIVE_SETUP.md) describes the historical binary; [CURRENT_MODEL_SETUP.md](CURRENT_MODEL_SETUP.md) and [V6_MODEL_SETUP.md](V6_MODEL_SETUP.md) record later bounded checks of a separately source-built Linux amd64 binary. Native build-reference files are provenance records, not portable installation settings.
