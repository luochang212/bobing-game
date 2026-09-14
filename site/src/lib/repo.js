import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';

/**
 * 定位仓库根（含 current 文件与 versions/ 目录）。
 * 预渲染打包后 import.meta.url 不再指向源码位置，改从 cwd 向上查找。
 */
export function findRepoRoot(start = process.cwd()) {
  let dir = path.resolve(start);
  for (let i = 0; i < 6; i++) {
    if (existsSync(path.join(dir, 'current')) && existsSync(path.join(dir, 'versions'))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  throw new Error('找不到仓库根（应含 current 文件与 versions/ 目录）');
}

export function readRepoText(...segments) {
  return readFileSync(path.join(findRepoRoot(), ...segments), 'utf-8');
}

/**
 * 活动场景指针（仓库根 scope 文件，一行）：multi ＝ 多桌含状元王加赛，single ＝ 单桌。
 * 交付集合与页脚都由它派生，与奖品模型版本（current）正交。
 */
export function readScope() {
  const scope = readRepoText('scope').trim();
  if (scope !== 'single' && scope !== 'multi') {
    throw new Error(`scope 文件内容须为 single 或 multi（当前 '${scope}'）`);
  }
  return scope;
}
