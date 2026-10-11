#!/bin/bash
# 等待大规模 run 完成后，自动做 CFA 复核 + NMI 网络重画 + 汇总
set -e
RUN="${RUN_ID:-2026-10-08_144539}"   # 设为 data/runs/<run_id> 下的实际 run id
ROOT="${EMPATHYSCALE_ROOT:-.}"          # 设为你的 EmpathyScale-main 目录；如 ../EmpathyScale-main
VENV="$ROOT/venv/Scripts/python.exe"
RD="$ROOT/data/runs/$RUN"

echo "[pp] waiting for run $RUN to finish (max ~90 min) ..."
for i in $(seq 1 90); do
  PROC_ALIVE=$(ps aux | grep -c "[v]env/Scripts/python" || true)
  CFA_DONE=$( [ -f "$RD/statistical_selection/efa_cfa_results.json" ] && echo 1 || echo 0 )
  EVAL_DONE=$( [ -f "$RD/evaluation_agent_group/selection/combined/participant_level_evaluations.json" ] && echo 1 || echo 0 )
  if [ "$CFA_DONE" = "1" ] && [ "$EVAL_DONE" = "1" ]; then
    echo "[pp] completion markers present (iter $i)"; break
  fi
  if [ "$PROC_ALIVE" = "0" ] && [ "$CFA_DONE" = "1" ]; then
    echo "[pp] process gone + CFA done (iter $i)"; break
  fi
  sleep 60
done

echo "[pp] === verify CFA (N=40) ==="
"$VENV" tools/verify_run_cfa.py "$RUN" 2>&1 | tee "$RD/verify_cfa.log"

echo "[pp] === NMI network viz ==="
"$VENV" tools/nmi_network_viz.py "$RUN" 2>&1 | tee "$RD/nmi_viz.log"

echo "[pp] === build summary ==="
{
  echo "# 大规模 run $RUN 后处理汇总"
  echo ""
  echo "## CFA 复核（verify_run_cfa.py）"
  echo '```'
  cat "$RD/verify_cfa.log"
  echo '```'
  echo ""
  echo "## NMI 网络可视化（nmi_network_viz.py）"
  echo '```'
  cat "$RD/nmi_viz.log"
  echo '```'
  echo ""
  echo "产物: $RD/statistical_selection/cfa_recheck.json, $RD/viz/nmi_item_network.png"
} > "$RD/POSTPROCESS_SUMMARY.md"

echo "[pp] DONE -> $RD/POSTPROCESS_SUMMARY.md"
