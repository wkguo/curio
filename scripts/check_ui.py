"""Browser regressions for an isolated Curio test app (Playwright required).

Example: python scripts/check_ui.py --base-url http://127.0.0.1:3765 --artifacts-dir /tmp/curio-ui-check
The app should use a temporary database: this check starts one learning session.
"""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url', default='http://127.0.0.1:3765')
parser.add_argument('--artifacts-dir', type=Path, required=True)
args=parser.parse_args()
ROOT=args.artifacts_dir
ROOT.mkdir(parents=True,exist_ok=True)
BASE=args.base_url.rstrip('/')
checks=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
    page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
    console_errors=[]
    page.on('pageerror',lambda e:console_errors.append(str(e)))
    page.goto(BASE+'/dashboard')
    page.get_by_text('Rules live',exact=True).first.wait_for()
    page.screenshot(path=str(ROOT/'dashboard-desktop.png'))
    checks.append('Live dashboard identifies rules mode')
    page.goto(BASE+'/teacher/evaluation')
    page.get_by_text('Development vs held-out',exact=True).wait_for()
    assert 'draft labels' in page.locator('body').inner_text()
    assert page.get_by_role('button',name='Dev errors',exact=True).count()==1
    page.route('**/api/evaluation/run*',lambda route:route.fulfill(status=503,json={'code':'curio_unavailable','message':'Please try the evaluation again.'}))
    page.get_by_role('button',name='Re-run benchmark',exact=True).click()
    page.get_by_role('alert').filter(has_text='Please try the evaluation again.').wait_for()
    assert page.get_by_role('button',name='Re-run benchmark',exact=True).is_enabled()
    page.unroute('**/api/evaluation/run*')
    checks.append('Failed benchmark action shows error and recovers its button')
    page.screenshot(path=str(ROOT/'evaluation-desktop.png'))
    page.goto(BASE+'/teacher/content')
    page.get_by_role('button').filter(has_text='heat_001').first.click()
    page.route('**/api/teacher/pathways/*/review',lambda route:route.fulfill(status=503,json={'code':'curio_unavailable','message':'The review did not save. Please try again.'}))
    page.get_by_role('button',name='Approve',exact=True).click()
    page.get_by_role('alert').filter(has_text='The review did not save.').wait_for()
    assert page.get_by_role('button',name='Approve',exact=True).is_enabled()
    checks.append('Failed content approval reports an error and restores its button')
    mobile=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1)
    m=mobile.new_page()
    m.route('**/api/learning/sessions',lambda route:route.fulfill(status=422,json={'detail':'This session could not start. Please try again.'}))
    m.goto(BASE+'/learn?topic=heat_transfer')
    m.get_by_role('alert').filter(has_text='This session could not start.').wait_for()
    m.unroute('**/api/learning/sessions')
    m.get_by_role('button',name='Try again',exact=True).click()
    m.get_by_role('button',name='Submit Answer',exact=True).wait_for()
    assert m.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    m.wait_for_timeout(700)
    m.screenshot(path=str(ROOT/'learn-mobile.png'),full_page=True)
    checks.append('Mobile learning handles startup failure, retries and fits 390px')
    sample={'n':1,'classification_accuracy':0.5,'false_mastery_rate':0.1}
    comparison={'available':True,'model':'UI test fixture','cases':1,'systems':{
        key:{'label':label,'calls':1,'metrics':{'all':sample,'test':sample}}
        for key,label in [('rules','Curio (rules only)'),('harness','Curio + LLM'),('plain','LLM only (one prompt)')]
    }}
    m.route('**/api/evaluation/llm-baseline',lambda route:route.fulfill(json=comparison))
    m.goto(BASE+'/teacher/evaluation')
    m.get_by_role('columnheader',name='Curio + LLM',exact=False).wait_for()
    assert m.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    m.get_by_role('button',name='All cases',exact=True).click()
    m.unroute('**/api/evaluation/llm-baseline')
    checks.append('Mobile evaluation fits 390px and renders the comparison (synthetic UI fixture)')
    offline=browser.new_context(viewport={'width':1440,'height':1000})
    o=offline.new_page()
    o.route('**/api/**',lambda route:route.abort())
    o.goto(BASE+'/learn?topic=heat_transfer')
    o.get_by_text("You're exploring a recorded example.",exact=False).wait_for()
    o.get_by_text('Recorded demo',exact=True).first.wait_for()
    checks.append('Offline learning explicitly says recorded answers are replayed')
    o.goto(BASE+'/privacy')
    o.get_by_text('These are recorded demo records.',exact=False).wait_for()
    assert o.get_by_role('button',name='Delete my learning data',exact=True).is_disabled()
    o.screenshot(path=str(ROOT/'privacy-offline.png'))
    checks.append('Offline privacy does not simulate successful deletion')
    o.goto(BASE+'/teacher/content')
    o.get_by_text('Recorded content review.',exact=False).wait_for()
    o.get_by_role('button').filter(has_text='heat_001').first.click()
    assert o.get_by_role('button',name='Approve',exact=True).is_disabled()
    checks.append('Offline content review cannot simulate a saved approval')
    fx=json.loads((Path(__file__).resolve().parents[1]/'frontend/public/mock/fixtures.json').read_text())
    fx['queue']=[{'id':'ui-fixture','kind':'deferred','category':'unclear','severity':'medium',
                  'student_id':'demo_student','student_name':'UI fixture','avatar':'fox','excerpt':'Recorded fixture',
                  'question_prompt':'Fixture question','created_at':'2026-10-22T12:00:00Z','status':'open'}]
    o.route('**/mock/fixtures.json',lambda route:route.fulfill(json=fx))
    o.goto(BASE+'/teacher')
    o.get_by_role('button',name='Resolve',exact=False).wait_for()
    assert o.get_by_role('button',name='Resolve',exact=False).is_disabled()
    checks.append('Offline teacher queue cannot simulate resolving an item (synthetic UI fixture)')
    o.goto(BASE+'/teacher/evaluation')
    o.get_by_text('Recorded report.',exact=False).wait_for()
    assert o.get_by_role('button',name='Re-run benchmark',exact=True).is_disabled()
    checks.append('Offline evaluation cannot pretend to run a new benchmark')
    assert not console_errors,console_errors
    browser.close()
print(json.dumps(checks,indent=2))
(ROOT/'ui_checks.json').write_text(json.dumps(checks,indent=2))
