#!/bin/bash
set -euo pipefail
app="${1:?请提供 Ice.app 路径}"
output="${2:?请提供输出目录}"
mkdir -p "$output"
# Xcode 会裁剪框架架构，因此社区包连同嵌套组件一起重新进行 ad-hoc 签名。
/usr/bin/codesign --force --sign - "$app/Contents/XPCServices/MenuBarItemService.xpc"
/usr/bin/codesign --force --deep --sign - "$app"
/usr/bin/codesign --verify --deep --strict "$app"
/usr/bin/lipo "$app/Contents/MacOS/Ice" -verify_arch arm64 x86_64
/usr/bin/lipo "$app/Contents/XPCServices/MenuBarItemService.xpc/Contents/MacOS/MenuBarItemService" -verify_arch arm64 x86_64
/usr/bin/plutil -lint "$app/Contents/Resources/zh-Hans.lproj/Localizable.strings"
python3 - "$app" <<'PY'
import plistlib, sys
from pathlib import Path
p = Path(sys.argv[1]) / 'Contents/Info.plist'
d = plistlib.loads(p.read_bytes())
assert d['CFBundleIdentifier'] == 'com.tokio233.Ice.zh', d
assert 'SUFeedURL' not in d, '社区版不能使用上游更新源'
PY
/usr/bin/ditto -c -k --sequesterRsrc --keepParent "$app" "$output/Ice-zh-universal.zip"
(cd "$output" && shasum -a 256 Ice-zh-universal.zip > SHA256SUMS.txt)
