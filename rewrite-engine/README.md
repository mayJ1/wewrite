# WeWrite local rewrite engine

This directory is intentionally kept lightweight in Git.

For a full Windows distribution, place the local rewrite model runtime here before running `build_windows.ps1`:

- `qwen3-merged-aigc_zhv3-Q4_K_M.gguf`
- `llama-server.exe`
- required llama.cpp DLL files, or a subfolder that contains them

At runtime WeWrite looks for `llama-server.exe` and the GGUF model under this directory, starts the server on `127.0.0.1:8282`, and calls its OpenAI-compatible `/v1/chat/completions` endpoint.

The large model and binaries are ignored by Git. Publish them through GitHub Releases or a separate downloadable Windows ZIP package instead of committing them to the repository.
