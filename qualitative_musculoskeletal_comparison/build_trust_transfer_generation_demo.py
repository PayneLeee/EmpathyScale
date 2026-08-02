"""Create a presentation-oriented replay for the trust-transfer scale."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent


def esc(value: Any) -> str:
    return html.escape(str(value))


def demo_data() -> dict[str, Any]:
    return {
        "title": "信任-物品传递共情量表生成回放",
        "duration": 78,
        "conversation": [
            {
                "speaker": "研究人员",
                "type": "user",
                "text": "请为共情机械臂共同取用任务生成评价量表。现场有高、中、低三件取用难度不同的物品；参与者依据对机器人能力的信任自主选择目标。",
            },
            {
                "speaker": "InterviewAgentGroup",
                "type": "agent",
                "text": "请补充机器人如何与参与者配合，以及任务结束后需要收集哪些反馈。",
            },
            {
                "speaker": "研究人员",
                "type": "user",
                "text": "机器人先依据初始信任移动到对应物品，同时通过情感识别判断无需沟通、确认一次或确认两次。确认无误后抓取传递；若物品不符则更换并再次确认。任务后反馈更新后的信任和机器人意图判断是否正确。",
            },
            {
                "speaker": "InterviewAgentGroup",
                "type": "agent",
                "text": "访谈解析完成。已输出结构化场景摘要：信任-物品难度映射、三类沟通分支、抓取传递和任务后反馈。现在将摘要移交至 LiteratureSearchAgentGroup。",
            },
        ],
        "steps": [
            {
                "title": "场景访谈解析",
                "group": "InterviewAgentGroup",
                "detail": "结构化场景摘要",
                "result": [
                    "评估场景：共情机械臂与人类共同取用高、中、低难度物品",
                    "关键变量：初始信任、物品难度、情感状态、确认次数",
                    "失败/调整节点：目标不符时更换物品并重新确认",
                ],
            },
            {
                "title": "文献检索",
                "group": "LiteratureSearchAgentGroup",
                "detail": "复用仓库中的肌肉骨骼协作检索中间结果",
                "result": [
                    "生成场景相关检索问题并执行多源检索",
                    "检索到 602 篇论文，筛读 24 篇，高相关 8 篇",
                    "证据主题：共享空间、身体人机交互、动作可预期、口头修复",
                ],
            },
            {
                "title": "构念界定与初始题项生成",
                "group": "EmpathyScaleGenerationAgentGroup",
                "detail": "复用仓库中的构念与候选题项生成过程",
                "result": [
                    "整合访谈摘要、文献发现与专家 PDF 指南",
                    "构建机制卡片：共享工位协调、碰撞恢复、显式沟通修复",
                    "生成第一版候选题项池，供后续语义筛选与模拟评估",
                ],
            },
            {
                "title": "语义去重",
                "group": "EmpathyScaleGenerationAgentGroup",
                "detail": "复用仓库中的内容评估与去重过程",
                "result": [
                    "删除近似重复与过泛表述",
                    "保留共享料架、让行、手臂轨迹、碰后修复等现场锚点",
                    "输出可由单次协作体验回答的候选题项",
                ],
            },
            {
                "title": "双组模拟参与者评估",
                "group": "EvaluationAgentGroup",
                "detail": "复用仓库中的双组 Persona 评分过程",
                "result": [
                    "运行共情机器人组模拟参与者评分",
                    "运行非共情机器人组模拟参与者评分",
                    "生成参与者层级评分数据，用于后续统计分析",
                ],
            },
            {
                "title": "双组合并",
                "group": "EvaluationAgentGroup",
                "detail": "复用仓库中的合并评估数据",
                "result": [
                    "合并两组参与者的题项评分和体验摘要",
                    "形成统一统计分析数据集",
                    "合并结果可用于因子分析与区分性验证",
                ],
            },
            {
                "title": "探索性/验证性因子分析选题",
                "group": "ItemSelectionAgent",
                "detail": "复用仓库中的统计选题过程",
                "result": [
                    "依据因子结构、载荷和可解释性筛选题项",
                    "候选题项 -> 筛选后保留题项，保留率 30.3%",
                    "输出因子归属和统计选题结果",
                ],
            },
            {
                "title": "独立样本验证",
                "group": "EvaluationAgentGroup",
                "detail": "复用仓库中的验证集评估结果",
                "result": [
                    "在独立样本上检验内部一致性和区分能力",
                    "Cronbach's alpha = 0.936",
                    "Cohen's d = 0.931",
                ],
            },
            {
                "title": "输出最终量表与关键指标",
                "group": "量表输出模块",
                "detail": "根据新的任务输入重建最终量表",
                "result": [
                    "输出 2 个维度、10 条评价量表条目",
                    "维度一：协调沟通（6 条）",
                    "维度二：用户状态考量（4 条）",
                ],
            },
        ],
        "scale": [
            {
                "name": "协调沟通",
                "items": [
                    "机械臂的运动轨迹使我容易预判它接下来的动作。",
                    "通过观察机械臂的动作，我能预判它何时会抓取并向我传递物品。",
                    "机械臂采用的确认次数符合我当时的沟通需要。",
                    "机械臂的动作和语言提示使它的传递意图清晰易懂。",
                    "当目标物品不符合我的需要时，机械臂能够通过沟通及时调整。",
                    "在抓取和传递物品的过程中，我感觉机械臂能够与我有效协调。",
                ],
            },
            {
                "name": "用户状态考量",
                "items": [
                    "机械臂选择的物品符合我当时对它的信任程度。",
                    "机械臂的配合方式表明它注意到了我当时的情绪状态。",
                    "机械臂采用的沟通程度让我在物品传递过程中感到安心。",
                    "我感觉机械臂理解我当时希望它以何种方式与我配合。",
                ],
            },
        ],
    }


def render_html(data: dict[str, Any]) -> str:
    data_json = json.dumps(data, ensure_ascii=False)
    steps_html = "\n".join(
        f'''<div class="process-step" id="step-{number}">
  <div class="number">{number:02d}</div>
  <div><div class="step-title">{esc(step["title"])}</div><div class="step-group">{esc(step["group"])}</div></div>
  <div class="step-state">等待</div>
</div>'''
        for number, step in enumerate(data["steps"], 1)
    )
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(data["title"])}</title>
<style>
:root {{ --ink:#162235; --muted:#627184; --line:#dbe4ee; --blue:#156fc2; --teal:#0b766c; --green:#147a43; --bg:#f2f6fa; --paper:#fff; --soft:#ecf5ff; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; min-width:1180px; overflow:hidden; background:var(--bg); color:var(--ink); font-family:"Microsoft YaHei","Segoe UI",Arial,sans-serif; }}
.topbar {{ height:84px; padding:15px 34px; display:flex; align-items:center; justify-content:space-between; background:#fff; border-bottom:1px solid var(--line); }}
h1 {{ margin:0; font-size:32px; letter-spacing:0; }} .subline {{ margin-top:5px; color:var(--muted); font-size:18px; }}
.controls {{ display:flex; gap:8px; align-items:center; }} button {{ border:0; border-radius:6px; padding:10px 15px; background:var(--blue); color:#fff; font-size:16px; cursor:pointer; }} button.secondary {{ background:#e9eff5; color:#3e4d5f; }}
.progress-shell {{ height:6px; background:#e2eaf3; }} .progress {{ height:100%; width:0; background:linear-gradient(90deg,var(--blue),var(--teal)); transition:width .15s linear; }}
.screen {{ height:calc(100vh - 90px); min-height:720px; padding:28px 34px; }}
#interviewView {{ display:grid; place-items:center; }}
.interview-shell {{ width:min(1050px,90vw); height:calc(100vh - 176px); min-height:610px; display:grid; grid-template-rows:auto 1fr; border:1px solid var(--line); border-radius:9px; background:#fff; box-shadow:0 14px 38px rgba(21,45,73,.08); overflow:hidden; }}
.section-head {{ padding:20px 24px; border-bottom:1px solid var(--line); }} .section-head h2 {{ margin:0; font-size:30px; }}
.chat {{ padding:26px 32px; overflow:hidden; background:#f8fafc; }} .message {{ display:flex; margin:0 0 18px; opacity:0; transform:translateY(10px); transition:opacity .32s ease,transform .32s ease; }} .message.show {{ opacity:1; transform:translateY(0); }} .message.user {{ justify-content:flex-end; }}
.bubble-wrap {{ max-width:82%; }} .bubble {{ padding:15px 18px; border:1px solid var(--line); border-radius:13px; border-bottom-left-radius:4px; background:#fff; font-size:25px; line-height:1.55; box-shadow:0 2px 8px rgba(19,41,67,.05); }} .message.user .bubble {{ border-color:var(--blue); border-bottom-left-radius:13px; border-bottom-right-radius:4px; background:var(--blue); color:#fff; }}
#pipelineView {{ display:none; padding:22px 34px; }} .pipeline-heading {{ height:70px; display:flex; align-items:center; justify-content:space-between; }} .pipeline-heading h2 {{ margin:0; font-size:31px; }} .phase-chip {{ padding:8px 12px; border-radius:5px; background:#dff5f1; color:#0e625b; font-size:18px; font-weight:700; }}
.pipeline-grid {{ height:calc(100% - 66px); display:grid; grid-template-columns:minmax(435px,.88fr) minmax(560px,1.32fr); gap:20px; }}
.panel {{ overflow:hidden; border:1px solid var(--line); border-radius:9px; background:var(--paper); box-shadow:0 9px 26px rgba(21,45,73,.07); }} .panel-title {{ padding:17px 20px; border-bottom:1px solid var(--line); font-size:25px; font-weight:700; }}
.flow-panel {{ display:grid; grid-template-rows:auto 1fr; }} .flow-list {{ padding:12px 16px; overflow:hidden; }}
.process-step {{ min-height:61px; display:grid; grid-template-columns:48px 1fr 54px; gap:11px; align-items:center; padding:7px 9px; border-left:5px solid #d4dee9; }} .process-step + .process-step {{ border-top:1px solid #edf1f5; }} .process-step.running {{ background:#f0f7ff; border-left-color:var(--blue); }} .process-step.done {{ border-left-color:var(--green); }} .number {{ color:#728196; font-size:19px; font-weight:700; }} .step-title {{ font-size:20px; font-weight:700; line-height:1.25; }} .step-group {{ margin-top:2px; color:var(--teal); font-size:13px; }} .step-state {{ color:#7d8998; font-size:15px; text-align:right; }} .process-step.running .step-state {{ color:var(--blue); font-weight:700; }} .process-step.done .step-state {{ color:var(--green); font-weight:700; }}
.result-panel {{ display:grid; grid-template-rows:auto 1fr; }} .result-body {{ min-height:0; padding:23px 28px; overflow:hidden; }} .placeholder {{ height:100%; display:grid; place-items:center; color:#738398; font-size:19px; text-align:center; line-height:1.7; }}
.result-meta {{ padding:16px 18px; border-left:5px solid var(--teal); background:#eefaf8; }} .result-agent {{ color:var(--teal); font-size:17px; font-weight:700; }} .result-name {{ margin-top:4px; font-size:31px; font-weight:700; }} .result-detail {{ margin-top:5px; color:var(--muted); font-size:18px; }} .output-list {{ margin:22px 0 0; padding:0; list-style:none; }} .output-list li {{ position:relative; padding:14px 0 14px 26px; border-bottom:1px solid #e8edf2; color:#354559; font-size:20px; line-height:1.42; }} .output-list li:before {{ content:""; position:absolute; left:2px; top:23px; width:9px; height:9px; border-radius:50%; background:var(--blue); }}
.scale {{ display:grid; grid-template-columns:1fr 1fr; gap:15px; }} .dimension {{ border:1px solid var(--line); border-radius:7px; overflow:hidden; }} .dimension h3 {{ margin:0; padding:11px 14px; background:#f5f8fb; color:#1d5d8c; font-size:21px; }} .scale-item {{ padding:10px 13px; border-top:1px solid #e9eef3; font-size:17px; line-height:1.45; }} .scale-index {{ display:inline-block; width:24px; color:#8290a1; font-size:14px; }}
.statusline {{ margin-top:16px; color:#5d6b7d; font-size:17px; }}
</style>
</head>
<body>
<header class="topbar"><div><h1>{esc(data["title"])}</h1><div class="subline" id="subtitle">阶段一：InterviewAgentGroup 场景访谈</div></div><div class="controls"><button id="play" type="button">播放</button><button id="pause" class="secondary" type="button">暂停</button><button id="restart" class="secondary" type="button">重播</button></div></header>
<div class="progress-shell"><div class="progress" id="progress"></div></div>
<section class="screen" id="interviewView"><div class="interview-shell"><div class="section-head"><h2>智能访谈对话</h2></div><div class="chat" id="chat"></div></div></section>
<section class="screen" id="pipelineView"><div class="pipeline-heading"><h2>流程展示</h2><div class="phase-chip" id="phaseChip">等待移交</div></div><div class="pipeline-grid"><section class="panel flow-panel"><div class="panel-title">九步骤自动处理</div><div class="flow-list">{steps_html}</div></section><section class="panel result-panel"><div class="panel-title">中间结果展示</div><div class="result-body" id="resultBody"><div class="placeholder">等待 InterviewAgentGroup 完成场景解析<br>并移交至后续 AgentGroup。</div></div></section></div></section>
<script>
const demo = {data_json};
const chat = document.getElementById('chat'); const progress = document.getElementById('progress');
let playing=false, started=0, elapsedBefore=0, frame=null, fired=new Set();
const totalMs=demo.duration*1000;
const events=[];
demo.conversation.forEach((message,index) => events.push({{at:2+index*4.5,type:'message',payload:message,key:'message'+index}}));
events.push({{at:20,type:'transfer',key:'transfer'}});
demo.steps.forEach((step,index) => {{ events.push({{at:22+index*6,type:'run',payload:step,key:'run'+index}}); events.push({{at:26.2+index*6,type:'done',payload:step,key:'done'+index}}); }});
events.push({{at:76,type:'scale',key:'scale'}});
function escapeHtml(value) {{ return String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }}
function addMessage(message) {{ const element=document.createElement('div'); element.className='message ' + message.type; element.innerHTML='<div class="bubble-wrap"><div class="bubble">' + escapeHtml(message.text) + '</div></div>'; chat.appendChild(element); requestAnimationFrame(() => element.classList.add('show')); }}
function transfer() {{ document.getElementById('interviewView').style.display='none'; document.getElementById('pipelineView').style.display='block'; document.getElementById('subtitle').textContent='阶段二：九步骤自动处理与中间结果展示'; document.getElementById('phaseChip').textContent='已移交 LiteratureSearchAgentGroup'; }}
function setStep(index,status) {{ const card=document.getElementById('step-'+(index+1)); card.className='process-step ' + status; card.querySelector('.step-state').textContent=status==='running'?'进行中':'完成'; }}
function showIntermediate(index) {{ const step=demo.steps[index]; document.getElementById('phaseChip').textContent='当前：第 ' + (index+1) + ' / 9 步'; document.getElementById('resultBody').innerHTML='<div class="result-meta"><div class="result-agent">' + escapeHtml(step.group) + '</div><div class="result-name">' + escapeHtml(step.title) + '</div><div class="result-detail">' + escapeHtml(step.detail) + '</div></div><ul class="output-list">' + step.result.map(line => '<li>' + escapeHtml(line) + '</li>').join('') + '</ul><div class="statusline">中间结果已写入，等待下一步骤。</div>'; }}
function showScale() {{ document.getElementById('phaseChip').textContent='九步骤处理完成'; document.getElementById('resultBody').innerHTML='<div class="result-meta"><div class="result-agent">量表输出模块</div><div class="result-name">最终评价量表</div><div class="result-detail">新的信任-物品传递任务输入生成结果</div></div><div class="scale">' + demo.scale.map(section => '<section class="dimension"><h3>' + escapeHtml(section.name) + '（' + section.items.length + ' 条）</h3>' + section.items.map((item,index) => '<div class="scale-item"><span class="scale-index">' + (index+1) + '.</span>' + escapeHtml(item) + '</div>').join('') + '</section>').join('') + '</div>'; }}
function runEvent(event) {{ if(event.type==='message') addMessage(event.payload); if(event.type==='transfer') transfer(); if(event.type==='run') {{ const index=demo.steps.indexOf(event.payload); setStep(index,'running'); showIntermediate(index); }} if(event.type==='done') {{ const index=demo.steps.indexOf(event.payload); setStep(index,'done'); }} if(event.type==='scale') showScale(); }}
function tick() {{ if(!playing) return; const elapsed=elapsedBefore+(performance.now()-started); const seconds=elapsed/1000; progress.style.width=Math.min(100,elapsed/totalMs*100)+'%'; events.forEach(event => {{ if(seconds>=event.at&&!fired.has(event.key)) {{ fired.add(event.key); runEvent(event); }} }}); if(elapsed<totalMs) frame=requestAnimationFrame(tick); else playing=false; }}
function play() {{ if(playing) return; playing=true; started=performance.now(); frame=requestAnimationFrame(tick); }}
function pause() {{ if(!playing) return; elapsedBefore+=performance.now()-started; playing=false; if(frame) cancelAnimationFrame(frame); }}
function reset() {{ if(frame) cancelAnimationFrame(frame); playing=false; elapsedBefore=0; fired=new Set(); chat.innerHTML=''; progress.style.width='0%'; document.getElementById('interviewView').style.display='grid'; document.getElementById('pipelineView').style.display='none'; document.getElementById('subtitle').textContent='阶段一：InterviewAgentGroup 场景访谈'; document.getElementById('phaseChip').textContent='等待移交'; document.getElementById('resultBody').innerHTML='<div class="placeholder">等待 InterviewAgentGroup 完成场景解析<br>并移交至后续 AgentGroup。</div>'; demo.steps.forEach((step,index) => {{ const card=document.getElementById('step-'+(index+1)); card.className='process-step'; card.querySelector('.step-state').textContent='等待'; }}); }}
document.getElementById('play').addEventListener('click',play); document.getElementById('pause').addEventListener('click',pause); document.getElementById('restart').addEventListener('click',() => {{ reset(); play(); }}); reset(); play();
</script>
</body>
</html>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "output" / "trust_transfer_generation_demo.html")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(demo_data()), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
