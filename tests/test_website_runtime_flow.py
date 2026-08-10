from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
WEBSITE_PATH = ROOT / 'index.html'

EXPECTED_STAGES = (
    ('1', 'Task Lock', '任务锁定'),
    ('2', 'Literature Grounding', '文献与背景'),
    ('3', 'Hypothesis Framing', '假设构建'),
    ('4', 'Method Design', '方法设计'),
    ('5', 'Experiment Design', '实验设计'),
    ('6', 'Implementation & Execution', '实现与执行'),
    ('7', 'Analysis & Review', '分析与评审'),
    ('8', 'Claim Gate', '结论审查'),
    ('9', 'Paper Writing & Artifact Package', '论文撰写与产物打包'),
)

EXPECTED_KNOWLEDGE_NODES = (
    ('M01', 'method', 'Evidence Routing', '证据归类'),
    ('M02', 'method', 'Case Grouping', '汇总同类案例'),
    ('M03', 'method', 'Pattern Induction', '归纳共性规律'),
    ('M04', 'method', 'Method Knowledge', '形成方法知识'),
    ('R01', 'strategy', 'Paper Blueprint', '梳理论文框架'),
    ('R02', 'strategy', 'Strategy Profile', '提炼研究思路'),
    ('R03', 'strategy', 'Cross-paper Distillation', '比较多篇论文'),
    ('R04', 'strategy', 'Research Strategies', '形成研究策略'),
)

EXPECTED_SKILL_GROUPS = (
    ('design', 'Research design', '研究设计'),
    ('brain', 'Brain data processing', '脑数据处理'),
    ('analysis', 'Modeling and analysis', '建模与分析'),
    ('writing', 'Paper writing', '论文写作'),
    ('review', 'Review and reproducibility', '审查与复现'),
)


def _page() -> tuple[str, BeautifulSoup]:
    source = WEBSITE_PATH.read_text(encoding='utf-8')
    return source, BeautifulSoup(source, 'html.parser')


def test_runtime_flow_has_exact_nine_stage_model() -> None:
    _, soup = _page()
    flow = soup.select_one('#runtimeFlow')
    assert flow is not None

    stages = flow.select('[data-stage]')
    assert [stage['data-stage'] for stage in stages] == [item[0] for item in EXPECTED_STAGES]
    assert len({stage['data-stage'] for stage in stages}) == 9

    for stage, (_, english, chinese) in zip(stages, EXPECTED_STAGES, strict=True):
        assert stage.select_one('.flow-stage-name.lang-en').get_text(' ', strip=True) == english
        assert stage.select_one('.flow-stage-name.lang-zh').get_text(' ', strip=True) == chinese


def test_runtime_flow_exposes_all_main_and_revisit_routes() -> None:
    _, soup = _page()
    required_path_ids = {
        'flow-entry',
        'flow-main-3-4',
        'flow-main-4-5',
        'flow-main-5-6',
        'flow-main-6-7',
        'flow-revisit-in',
        'flow-revisit-3',
        'flow-revisit-4',
        'flow-revisit-5',
        'flow-revisit-6',
        'flow-pass',
    }
    paths = soup.select('#runtimeFlow path[id]')
    path_ids = [path['id'] for path in paths]
    assert required_path_ids <= set(path_ids)
    assert len(path_ids) == len(set(path_ids))

    revisit_routes = soup.select('#runtimeFlow path[data-route-target]')
    assert [path['data-route-target'] for path in revisit_routes] == ['3', '4', '5', '6']
    assert all('flow-path--revisit' in path.get('class', []) for path in revisit_routes)
    assert soup.select_one('#flow-deliver-8-9') is not None


def test_runtime_flow_has_one_clean_entry_and_exit_visual_language() -> None:
    source, soup = _page()
    loop = soup.select_one('#runtimeFlow .flow-loop')
    assert loop is not None

    router_label = loop.select_one('.flow-router-label')
    assert router_label.select_one('.lang-en').get_text(' ', strip=True) == 'REVISIT DECISION'
    assert router_label.select_one('.lang-zh').get_text(' ', strip=True) == '判断回跳阶段'

    entry_path = soup.select_one('#flow-entry')
    assert entry_path is not None
    assert 'flow-shell-links' in entry_path.parent.get('class', [])
    assert entry_path.get('marker-end') == 'url(#flowArrowShell)'
    pass_path = soup.select_one('#flow-pass')
    assert pass_path is not None
    assert pass_path.parent is entry_path.parent
    assert pass_path.get('marker-end') == 'url(#flowArrowShell)'
    assert all(marker.get('markerunits') == 'userSpaceOnUse' for marker in soup.select('#runtimeFlow marker'))
    assert 'function updateFlowShellPaths()' in source
    assert '.flow-phase--prepare { transform: translateY(-120px); }' in source
    assert '.flow-phase--deliver [data-stage="8"]::before' not in source
    assert '.flow-phase--deliver [data-stage="8"]::after' not in source
    assert '.flow-phase--prepare [data-stage="2"]::before' not in source
    assert '.flow-phase--prepare [data-stage="2"]::after' not in source
    assert '.flow-stage-name { font: 500 16.25px/1.28' in source


def test_runtime_flow_controls_are_accessible_and_keyboard_native() -> None:
    _, soup = _page()
    flow = soup.select_one('#runtimeFlow')
    assert flow is not None
    assert flow['aria-labelledby'] == 'runtimeFlowCaption'
    assert flow['aria-describedby'] == 'runtimeFlowSummary'
    assert soup.select_one('#runtimeFlowCaption') is not None
    assert soup.select_one('#runtimeFlowSummary') is not None

    targets = flow.select('button[data-revisit-target]')
    assert [target['data-revisit-target'] for target in targets] == ['3', '4', '5', '6']
    for target in targets:
        assert target['type'] == 'button'
        assert target['aria-pressed'] == 'false'
        assert target.get('aria-label')

    replay = flow.select_one('#flowReplay')
    assert replay is not None
    assert replay['type'] == 'button'
    assert replay.has_attr('disabled')
    assert replay.get('aria-label')
    status = flow.select_one('#flowStatus')
    assert status is not None
    assert status['aria-live'] == 'polite'


def test_runtime_flow_is_static_until_explicit_interaction() -> None:
    source, soup = _page()
    flow = soup.select_one('#runtimeFlow')
    assert flow is not None
    assert flow['data-flow-state'] == 'idle'
    assert not flow.has_attr('data-selected-target')
    assert soup.select_one('animateMotion') is None

    assert "button.addEventListener('click', function () { runFlow(Number(target)); });" in source
    assert "flowReplay.addEventListener('click'" in source
    assert 'IntersectionObserver' in source
    assert 'runFlow(' not in source.split('/* ---------- iterative research flow ---------- */', 1)[0]


def test_runtime_flow_has_reduced_motion_and_no_legacy_figure_content() -> None:
    source, _ = _page()
    assert '@media (prefers-reduced-motion: reduce)' in source
    assert 'completeFlowImmediately(selectedFlowTarget)' in source
    assert '.flow-pulse { display: none !important; }' in source

    for legacy_text in (
        'DIRECT QA',
        'checkpoint.json ×8',
        'dg-node',
        'dg-loop',
        'dgPath',
        'animateMotion',
    ):
        assert legacy_text not in source


def test_runtime_flow_keeps_default_language_theme_and_persistence_note() -> None:
    source, soup = _page()
    html = soup.select_one('html')
    assert html is not None
    assert html['data-lang'] == 'zh'
    assert html['data-theme'] == 'dark'

    note = soup.select_one('#runtimeFlow .flow-persistence')
    assert note is not None
    assert note.select_one('.lang-en').get_text(' ', strip=True) == (
        'Each stage persists a checkpoint for inspection, resume, and replay.'
    )
    assert note.select_one('.lang-zh').get_text(' ', strip=True) == '每个阶段均持久化检查点，可检查、恢复与回放。'
    assert 'border-block: 1px solid var(--stroke-strong)' in source
    assert 'font: 500 15.625px/1.55 var(--font-mono)' in source


def test_page_order_and_three_mechanism_chapters_are_explicit() -> None:
    _, soup = _page()
    main = soup.select_one('main')
    direct_children = [child.get('id') or child.name for child in main.find_all(recursive=False)]
    how = soup.select_one('#how')
    chapters = how.select(':scope > .mechanism-chapter')

    assert direct_children[:3] == ['header', 'problem', 'how']
    assert how is not None
    assert [chapter['data-mechanism'] for chapter in chapters] == ['workflow', 'knowledge', 'skills']
    assert soup.select_one('.hero #runtimeFlow') is None
    assert chapters[0].select_one('#runtimeFlow') is not None
    assert chapters[1].select_one('#knowledgeFlow') is not None
    assert chapters[2].select_one('#skillFlow') is not None
    assert how.select_one('.mechanism-grid') is None


def test_knowledge_flow_accessibility_contract_and_native_replay() -> None:
    _, soup = _page()
    flow = soup.select_one('#knowledgeFlow')
    assert flow is not None
    assert flow['aria-labelledby'] == 'knowledgeFlowCaption'
    assert flow['aria-describedby'] == 'knowledgeFlowSummary'
    assert soup.select_one('#knowledgeFlowCaption') is not None
    assert soup.select_one('#knowledgeFlowSummary') is not None

    replay = flow.select_one('#knowledgeReplay')
    assert replay is not None
    assert replay['type'] == 'button'
    assert replay.has_attr('disabled')
    assert replay.get('aria-label')
    status = flow.select_one('#knowledgeFlowStatus')
    assert status is not None
    assert status['aria-live'] == 'polite'


def test_knowledge_flow_has_exact_parallel_bilingual_nodes() -> None:
    _, soup = _page()
    nodes = soup.select('#knowledgeFlow .kb-node')
    assert len(nodes) == len(EXPECTED_KNOWLEDGE_NODES)

    actual = []
    for node in nodes:
        actual.append((
            node.select_one('.kb-node-code').get_text(' ', strip=True),
            node['data-kb-lane'],
            node.select_one('.kb-node-name.lang-en').get_text(' ', strip=True),
            node.select_one('.kb-node-name.lang-zh').get_text(' ', strip=True),
        ))
    assert tuple(actual) == EXPECTED_KNOWLEDGE_NODES


def test_knowledge_flow_paths_connect_source_and_release() -> None:
    source, soup = _page()
    paths = soup.select('#knowledgeFlow .kb-path[id]')
    assert [path['id'] for path in paths] == ['kbMethodPath', 'kbStrategyPath']
    assert len({path['id'] for path in paths}) == 2
    assert all(path['d'].startswith('M0 220') for path in paths)
    assert all(path['d'].endswith('660 220') for path in paths)
    assert len(soup.select('#knowledgeFlow .kb-junction')) == 2
    assert soup.select_one('#knowledgeFlow .kb-vector-label') is None
    assert '.kb-source-wrap, .kb-release-wrap { position: relative; z-index: 3; min-width: 0; height: 440px; }' in source
    assert 'display: grid; align-content: center; transform: translateY(-50%);' in source
    assert 'position: absolute; top: calc(50% + 116px); left: 0; right: 0;' in source


def test_knowledge_flow_delivers_two_distinct_knowledge_bases() -> None:
    _, soup = _page()
    release = soup.select_one('#knowledgeFlow [data-kb-release]')
    rows = release.select('.kb-release-row')

    assert len(rows) == 2
    assert rows[0].select_one('.kb-release-title .lang-zh').get_text(' ', strip=True) == '方法知识库'
    assert rows[1].select_one('.kb-release-title .lang-zh').get_text(' ', strip=True) == '研究策略库'
    assert 'kb-release-row--method' in rows[0].get('class', [])
    assert 'kb-release-row--strategy' in rows[1].get('class', [])
    assert len(release.select('.kb-release-divider')) == 1


def test_knowledge_flow_uses_independent_animation_lifecycle() -> None:
    source, _ = _page()
    assert 'function runKnowledgeFlow()' in source
    assert 'var kbRunToken = 0;' in source
    assert 'var kbAnimations = [];' in source
    assert 'var kbWaiters = [];' in source
    assert "knowledgeReplay.addEventListener('click', runKnowledgeFlow);" in source
    assert 'animateKnowledgePath(kbMethodPath, kbMethodPulse, 2400, token)' in source
    assert 'animateKnowledgePath(kbStrategyPath, kbStrategyPulse, 2400, token)' in source


def test_knowledge_flow_autostarts_once_and_respects_reduced_motion() -> None:
    source, _ = _page()
    assert 'var knowledgeObserver = new IntersectionObserver' in source
    assert 'knowledgeObserver.unobserve(entry.target);' in source
    assert 'knowledgeObserver.observe(knowledgeFlow);' in source
    assert 'if (reduceMotion) {' in source
    assert 'completeKnowledgeImmediately();' in source
    assert '.kb-pulse { display: none !important; }' in source


def test_knowledge_flow_has_mobile_layout_and_language_control() -> None:
    source, _ = _page()
    assert '@media (max-width: 820px)' in source
    responsive = source.split('@media (max-width: 820px)', 1)[1].split('@media (max-width: 600px)', 1)[0]
    assert '.kb-lens-svg, .kb-lens-center { display: none; }' in responsive
    assert '.kb-lane {' in responsive
    assert 'grid-template-columns: repeat(2, minmax(0, 1fr))' in responsive
    assert 'updateKbControlLabels();' in source
    assert "zh ? '重播知识库构建' : 'Replay knowledge build'" in source


def test_knowledge_flow_chinese_copy_and_typographic_hierarchy_are_explicit() -> None:
    source, soup = _page()
    flow = soup.select_one('#knowledgeFlow')
    chinese = ' '.join(element.get_text(' ', strip=True) for element in flow.select('.lang-zh'))

    for forbidden in ('Pattern', 'Case', 'supporting paper', '证据路由', '策略画像', '跨文献蒸馏', '可选向量'):
        assert forbidden not in chinese
    assert '知识经过提炼，但证据链始终保留' in chinese
    assert 'font: 600 16.25px/1.25 var(--font-b-en)' in source
    assert 'font: 600 15.625px/1.4 var(--font-b-en)' in source


def test_skill_flow_accessibility_and_group_catalog() -> None:
    _, soup = _page()
    flow = soup.select_one('#skillFlow')
    assert flow is not None
    assert flow['aria-labelledby'] == 'skillFlowCaption'
    assert flow['aria-describedby'] == 'skillFlowSummary'
    assert flow['data-skill-state'] == 'idle'

    replay = flow.select_one('#skillReplay')
    assert replay['type'] == 'button'
    assert replay.has_attr('disabled')
    assert flow.select_one('#skillFlowStatus')['aria-live'] == 'polite'
    assert flow.select_one('.skill-library-count .lang-zh').get_text(' ', strip=True) == '39 项技能'

    actual = []
    for group in flow.select('[data-skill-group]'):
        actual.append((
            group['data-skill-group'],
            group.select_one('.skill-group-name .lang-en').get_text(' ', strip=True),
            group.select_one('.skill-group-name .lang-zh').get_text(' ', strip=True),
        ))
    assert tuple(actual) == EXPECTED_SKILL_GROUPS


def test_skill_flow_exposes_agent_selection_record_without_user_picker_semantics() -> None:
    source, soup = _page()
    flow = soup.select_one('#skillFlow')
    agent = flow.select_one('[data-agent-router]')
    decision = flow.select_one('[data-skill-decision]')
    candidates = flow.select('.skill-item[data-skill-name]')
    decision_items = decision.select('.skill-decision-item')

    assert agent is not None
    assert agent.select_one('.skill-agent-mark').get_text('', strip=True) == 'NeuroAgent'
    assert flow.select_one('#skillFlowCaption .lang-zh').get_text(' ', strip=True) == '图 3 · NeuroAgent 自主调用科研技能'
    assert decision.select_one('.skill-decision-title .lang-zh').get_text(' ', strip=True) == 'NeuroAgent 选择结果'
    assert [item['data-skill-name'] for item in candidates if item['data-skill-name'] in {
        'method-selection', 'data-audit', 'decoding-strategy', 'run-verification'
    }] == ['method-selection', 'data-audit', 'decoding-strategy', 'run-verification']
    assert [item['data-skill-name'] for item in decision_items] == [
        'method-selection', 'data-audit', 'decoding-strategy', 'run-verification'
    ]
    assert [item.select_one('.lang-zh').get_text(' ', strip=True) for item in decision_items] == [
        '方法选择',
        '脑数据审计',
        '解码建模策略',
        '运行验证',
    ]
    assert [item.get_text(' ', strip=True) for item in flow.select('.skill-stage-output .lang-zh')] == [
        '操作步骤',
        '检查清单',
        '输出规范',
    ]
    assert not flow.select('[data-skill-pick], [data-skill-order], input[type="checkbox"], [aria-pressed]')
    assert '.skill-item.is-agent-selected, .skill-item:hover' not in source
    assert len(flow.select('[data-skill-route]')) == 2


def test_skill_flow_uses_independent_lifecycle_and_responsive_completion() -> None:
    source, _ = _page()
    assert 'function runSkillFlow()' in source
    assert 'var skillRunToken = 0;' in source
    assert 'var skillWaiters = [];' in source
    assert "var skillRoutes = Array.prototype.slice.call(skillFlow.querySelectorAll('[data-skill-route]'));" in source
    assert "skillReplay.addEventListener('click', runSkillFlow);" in source
    assert 'var skillObserver = new IntersectionObserver' in source
    assert 'skillObserver.unobserve(entry.target);' in source
    assert 'skillObserver.observe(skillFlow);' in source
    assert 'completeSkillImmediately();' in source
    assert 'grid-template-columns: 180px 132px minmax(0, 1fr) 248px' in source
    assert '.skill-shell { grid-template-columns: 1fr;' in source
    assert "zh ? '重播科研技能装配' : 'Replay research skill assembly'" in source
    assert 'var skillSelectionNames = [\'method-selection\', \'data-audit\', \'decoding-strategy\', \'run-verification\'];' in source
    assert 'html[data-lang="en"] .skill-decision-item.is-loaded::after { content: "Loaded"; }' in source


def test_website_has_no_duplicate_ids() -> None:
    _, soup = _page()
    ids = [element['id'] for element in soup.find_all(id=True)]
    assert len(ids) == len(set(ids))
