#!/usr/bin/env python3
"""生成原生语言资源，并检查 Swift 编译器提取的文案和占位符。"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'localization/zh-Hans.json'
RESOURCE = ROOT / 'Ice/Resources/zh-Hans.lproj/Localizable.strings'
FORMAT = re.compile(r'%(?:\d+\$)?(?:@|lld|llu|ld|lu|d|u|f|g|s)')


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'重复翻译键：{key}')
        result[key] = value
    return result


def read_catalog():
    catalog = json.loads(CATALOG.read_text(), object_pairs_hook=unique_pairs)
    for key, value in catalog.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'译文为空：{key}')
        source = Counter(FORMAT.findall(key.replace('%%', '')))
        translated = Counter(FORMAT.findall(value.replace('%%', '')))
        if source != translated:
            raise ValueError(f'占位符不一致：{key} -> {value}')
    return catalog


def render(catalog):
    quote = lambda s: json.dumps(s, ensure_ascii=False)
    return '\n'.join(f'{quote(k)} = {quote(v)};' for k, v in sorted(catalog.items())) + '\n'


def audit(derived, catalog):
    keys = set()
    files = 0
    for path in derived.rglob('*.stringsdata'):
        data = json.loads(path.read_text())
        source = Path(data.get('source', ''))
        if not source.is_relative_to(ROOT / 'Ice'):
            continue
        files += 1
        keys.update(item['key'] for item in data.get('tables', {}).get('Localizable', []))
    if files == 0 or len(keys) < 80:
        raise ValueError('缺少 Swift 编译器文案数据；请使用 SWIFT_EMIT_LOC_STRINGS=YES 构建。')
    # 这些名称先作为 String 保存，再由 SwiftUI 动态加载，编译器无法自动提取。
    for relative in [
        'Ice/Main/Navigation/NavigationIdentifiers/SettingsNavigationIdentifier.swift',
        'Ice/MenuBar/ControlItem/ControlItemImageSet.swift',
    ]:
        keys.update(re.findall(r'case \w+ = "([^"]+)"', (ROOT / relative).read_text()))
    section = (ROOT / 'Ice/MenuBar/MenuBarSection.swift').read_text()
    display = section.split('var displayString: String {', 1)[1].split('var logString:', 1)[0]
    keys.update(re.findall(r'case \.\w+: "([^"]+)"', display))
    permission = (ROOT / 'Ice/Permissions/Permission.swift').read_text()
    keys.update(re.findall(r'title: "([^"]+)"', permission))
    for details in re.findall(r'details: \[(.*?)\]', permission, re.S):
        keys.update(re.findall(r'"([^"]+)"', details))
    missing = sorted(keys - catalog.keys())
    report = {'extracted_keys': len(keys), 'translated_keys': len(catalog), 'missing': missing}
    report_path = ROOT / 'build/translation-report.json'
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if missing:
        raise ValueError('存在新增未翻译文案。更新 localization/zh-Hans.json 后重新构建。')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['generate', 'check', 'audit'])
    parser.add_argument('--derived-data', type=Path)
    args = parser.parse_args()
    catalog = read_catalog()
    expected = render(catalog)
    if args.command == 'generate':
        RESOURCE.parent.mkdir(parents=True, exist_ok=True)
        RESOURCE.write_text(expected)
    else:
        if RESOURCE.read_text() != expected:
            raise ValueError('语言资源尚未生成：运行 python3 scripts/localization.py generate')
        if args.command == 'audit':
            if args.derived_data is None:
                parser.error('audit 需要 --derived-data')
            audit(args.derived_data, catalog)
    print(f'语言资源检查通过：{len(catalog)} 条')


if __name__ == '__main__':
    main()
