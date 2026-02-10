#!/bin/bash
# Build go-audio-converter as WebAssembly
# Run from the go-audio-converter repo root
#
# Prerequisites:
#   - Go 1.22+ installed
#   - go-audio-converter cloned
#
# Usage:
#   ./build-wasm.sh
#
# Output:
#   wasm/converter.wasm  — the WASM binary (~2-4 MB)
#   wasm/wasm_exec.js    — Go's WASM runtime (from Go installation)

set -e

echo "🔨 Building go-audio-converter WASM..."

# Copy wasm main.go into the project if not exists
mkdir -p cmd/wasm
if [ ! -f cmd/wasm/main.go ]; then
    cp wasm/main.go cmd/wasm/main.go 2>/dev/null || echo "⚠️  Copy wasm/main.go to cmd/wasm/main.go manually"
fi

# Build WASM
GOOS=js GOARCH=wasm go build -o wasm/converter.wasm -ldflags="-s -w" ./cmd/wasm/

# Copy Go's WASM exec JS
GOROOT=$(go env GOROOT)
cp "$GOROOT/misc/wasm/wasm_exec.js" wasm/wasm_exec.js

# Show sizes
echo ""
echo "✅ Build complete!"
echo "   converter.wasm: $(du -h wasm/converter.wasm | cut -f1)"
echo "   wasm_exec.js:   $(du -h wasm/wasm_exec.js | cut -f1)"
echo ""
echo "📁 Copy these files to your audiotools.dev/wasm/ directory:"
echo "   cp wasm/converter.wasm  /path/to/audiotools.dev/wasm/"
echo "   cp wasm/wasm_exec.js    /path/to/audiotools.dev/wasm/"
echo ""
echo "🌐 The converter page will auto-detect WASM and enable FLAC encoding."
