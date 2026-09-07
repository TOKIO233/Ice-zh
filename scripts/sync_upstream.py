#!/usr/bin/env python3
"""检查正式版和测试版发布；普通合并保留汉化改动，冲突时停止。"""
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'localization/upstream.json'
UPSTREAM = 'jordanbaird/Ice'


def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def select_release(releases):
    candidates = [r for r in releases if not r['draft'] and r.get('published_at')
                  and re.fullmatch(r'v?\d+\.\d+\.\d+(?:[-.][A-Za-z0-9.]+)?', r['tag_name'])]
    if not candidates:
        raise ValueError('未找到有效的上游发布版本')
    return max(candidates, key=lambda r: r['published_at'])


def sync(release):
    current = json.loads(STATE.read_text())
    if release['tag_name'] == current['tag']:
        return False
    if release['published_at'] <= current['published_at']:
        raise ValueError('上游最新发布比当前基线旧；保留当前版本并停止自动回退。')
    tag = release['tag_name']
    # Fetch a specific tag into FETCH_HEAD, without overwriting local tags.
    run('git', 'fetch', '--no-tags', f'https://github.com/{UPSTREAM}.git', f'refs/tags/{tag}')
    upstream_sha = run('git', 'rev-parse', 'FETCH_HEAD^{commit}')
    try:
        run('git', 'merge', '--no-edit', upstream_sha)
    except subprocess.CalledProcessError:
        conflicts = run('git', 'diff', '--name-only', '--diff-filter=U')
        run('git', 'merge', '--abort')
        raise RuntimeError(f'上游合并冲突；远端和现有发布均保留。冲突文件：\n{conflicts}')
    state = {'repository': UPSTREAM, 'tag': tag, 'sha': upstream_sha,
             'published_at': release['published_at'], 'prerelease': release['prerelease']}
    STATE.write_text(json.dumps(state, indent=2) + '\n')
    run('git', 'add', 'localization/upstream.json')
    run('git', 'commit', '-m', f'chore: track upstream {tag}')
    run('git', 'push', 'origin', 'HEAD:zh-CN')
    return True


def main():
    changed = os.environ.get('GITHUB_EVENT_NAME') != 'schedule'
    releases = json.loads(run('gh', 'api', f'repos/{UPSTREAM}/releases?per_page=100'))
    changed = sync(select_release(releases)) or changed
    state = json.loads(STATE.read_text())
    output = {'build': str(changed).lower(), 'sha': run('git', 'rev-parse', 'HEAD'),
              'tag': state['tag'], 'prerelease': str(state['prerelease']).lower()}
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        for key, value in output.items():
            f.write(f'{key}={value}\n')
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
        f.write(f"上游基线：`{state['tag']}`。本次构建：{changed}。\n")
    print(json.dumps(output))


if __name__ == '__main__':
    main()
