"""现场读规则的浏览器回归检查；依赖 Playwright，运行方式见 docs/移动端阅读核查.md。"""
import argparse
import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--url', default='http://127.0.0.1:4322/bobing-game/')
parser.add_argument('--browser', choices=['chromium', 'webkit'], default='chromium')
parser.add_argument('--channel', help='使用本机 Chrome 时传 chrome，仅限 Chromium')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
tex = (root / '博饼规则-A4黑白.tex').read_text()
source_rolls = {tuple(re.findall(r'\d', group)) for group in re.findall(r'\\roll((?:\{\d\}){6})', tex)}
source_rolls.update(tuple(re.findall(r'\d', group)) for group in re.findall(r'[1-6](?:、[1-6]){5}', tex))

with sync_playwright() as p:
    launch = {'headless': True}
    if args.channel:
        assert args.browser == 'chromium', '--channel 仅用于 Chromium'
        launch['channel'] = args.channel
    browser = getattr(p, args.browser).launch(**launch)
    try:
        for width, height in [(320, 740), (360, 800), (390, 844), (430, 932), (768, 1024), (1024, 768), (1440, 1000)]:
            context = browser.new_context(viewport={'width': width, 'height': height}, is_mobile=width<=430, has_touch=width<=430, reduced_motion='reduce')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            response = page.goto(args.url, wait_until='networkidle')
            assert response.status == 200
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'{width}px 横向溢出'
            assert page.locator('.game-intro:visible').count() == 1, '先建立游戏与两种发奖方式的整体认识'
            assert page.locator('.game-route > li:visible').count() == 3
            section_ids = page.locator('main > section[id]').evaluate_all('(items) => items.map(el => el.id)')
            assert section_ids == ['overview', 'start', 'prizes', 'champion', 'ending', 'questions'], '先全局，再个人操作、判奖、状元与收尾'
            assert page.locator('.prize-condition:visible').count() == 6, '六档判定必须无需点击全部展开'
            assert page.locator('.rank-row:visible').count() == 6
            assert page.locator('.exception-list article:visible').count() == 2, '出碗和叠骰规则不能藏在折叠区'
            assert page.locator('.worked-example').inner_text().find('不另领二举') >= 0
            assert page.locator('.roll').count() == 13
            for roll in page.locator('.roll').all():
                label = roll.get_attribute('aria-label')
                assert tuple(re.findall(r'\d', label)) in source_rolls, label
            if width == 390:
                metrics = page.evaluate('''() => ({introBottom:document.querySelector('.game-intro').getBoundingClientRect().bottom,overviewBottom:document.querySelector('.game-route').getBoundingClientRect().bottom,rankRuleFont:parseFloat(getComputedStyle(document.querySelector('.rank-name p')).fontSize),rankCompareFont:parseFloat(getComputedStyle(document.querySelector('.rank-example > p')).fontSize)})''')
                assert metrics['introBottom'] <= height, '首屏先解释游戏与发奖方式，不要求把个人操作挤进首屏'
                assert metrics['rankRuleFont'] >= 16 and metrics['rankCompareFont'] >= 16
                print(f'{args.browser} 手机指标：{json.dumps(metrics, ensure_ascii=False)}')
            nav = page.get_by_role('navigation', name='规则目录')
            assert nav.get_by_role('link').count() == 6
            for link in nav.get_by_role('link').all():
                box = link.bounding_box()
                assert box['height'] >= 44 and box['width'] >= 44
                target = link.get_attribute('href')
                if width <= 430:
                    link.tap()
                else:
                    link.click()
                page.wait_for_function('(hash) => location.hash === hash', arg=target)
                top = page.locator(target).bounding_box()['y']
                nav_box = nav.bounding_box()
                assert top >= nav_box['y'] + nav_box['height'], f'{width}px {target} 被目录遮挡'
                assert top < height * .6, f'{width}px {target} 未跳到可阅读位置'
                assert nav_box['y'] >= 0 and nav_box['y'] < height, '目录滚动后仍应可见'
            for detail in page.locator('details').all():
                detail.locator('summary').click()
                assert detail.get_attribute('open') is not None
                detail.locator('summary').click()
                assert detail.get_attribute('open') is None
            # 二次访问与直接分享章节链接同样不能遮住标题。
            page.goto(args.url + '#champion', wait_until='networkidle')
            assert page.locator('#champion').bounding_box()['y'] >= nav.bounding_box()['y'] + nav.bounding_box()['height']
            pdf = page.request.get(args.url + 'rules-paper.pdf')
            assert pdf.status == 200 and pdf.body().startswith(b'%PDF')
            assert page.locator('img').evaluate_all('(images) => images.every(i => i.complete && i.naturalWidth > 0)')
            assert not errors, errors
            context.close()
        # 阅读与目录都不依赖 JavaScript；断脚本也能查全规则。
        context = browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844})
        page = context.new_page()
        page.goto(args.url, wait_until='networkidle')
        # WebKit 的默认 Tab 策略跳过普通链接；显式聚焦后验证 Enter 激活与落点。
        page.locator('.skip-link').focus()
        page.keyboard.press('Enter')
        page.wait_for_url('**/#main')
        assert page.url.endswith('#main')
        assert page.locator('#overview-title').bounding_box()['y'] >= page.locator('.reading-nav').bounding_box()['height']
        assert page.locator('.prize-condition:visible').count() == 6
        page.get_by_role('navigation', name='规则目录').get_by_role('link', name='小提醒', exact=True).click()
        assert page.url.endswith('#questions')
        page.locator('.faq-list summary').first.click()
        assert page.locator('.faq-list details[open]').count() == 1
        context.close()
        print(f'PASS {args.browser}：7 种视口、六档直接阅读、13 组源稿骰面、目录触摸/鼠标跳转、章节直达、问答、PDF、无脚本阅读。')
    finally:
        browser.close()
