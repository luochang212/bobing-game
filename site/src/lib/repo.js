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
