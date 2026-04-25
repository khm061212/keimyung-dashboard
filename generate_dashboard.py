# -*- coding: utf-8 -*-
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8')
import openpyxl

FILES = [
    {
        "path": "2022년 학교별 학과별 고등교육기관 취업통계_20240112.xlsx",
        "year": 2022,
        "sheet": "학교별 학과별",
        "data_row": 15,
    },
    {
        "path": "2023년 학교별 학과별 고등교육기관 졸업자 취업통계_241230.xlsx",
        "year": 2023,
        "sheet": "학교별 학과별",
        "data_row": 16,
    },
    {
        "path": "2024년 학교별 학과별 고등교육기관 졸업자 취업통계_260108.xlsx",
        "year": 2024,
        "sheet": "학교별",
        "data_row": 16,
    },
]

COL = {
    "학교명": 2,
    "과정구분": 8,
    "대계열": 9,
    "중계열": 10,
    "소계열": 11,
    "학과명": 13,
    "졸업자_계": 15,
    "취업률_계": 18,
    "취업자_합계_계": 21,
    "취업자_교외취업자_계": 24,
    "취업자_교내취업자_계": 27,
    "취업자_해외취업자_계": 30,
    "취업자_1인창(사)업자_계": 39,
    "취업자_프리랜서_계": 42,
    "진학률_계": 45,
    "1차 유지취업률_계": 70,
    "2차 유지취업률_계": 76,
    "3차 유지취업률_계": 82,
    "4차 유지취업률_계": 88,
}

FLOAT_COLS = {"취업률_계", "진학률_계", "1차 유지취업률_계", "2차 유지취업률_계", "3차 유지취업률_계", "4차 유지취업률_계"}
INT_COLS = {"졸업자_계", "취업자_합계_계", "취업자_교외취업자_계", "취업자_교내취업자_계", "취업자_해외취업자_계", "취업자_1인창(사)업자_계", "취업자_프리랜서_계"}


def to_float(v):
    if v is None:
        return None
    try:
        return float(str(v).strip())
    except:
        return None


def to_int(v):
    if v is None:
        return None
    try:
        return int(str(v).strip())
    except:
        return None


def read_file(cfg):
    rows = []
    wb = openpyxl.load_workbook(cfg["path"], read_only=True, data_only=True)
    ws = wb[cfg["sheet"]]
    for row in ws.iter_rows(min_row=cfg["data_row"], values_only=True):
        school = row[COL["학교명"]] if len(row) > COL["학교명"] else None
        if not school or "계명대학교" not in str(school):
            continue
        # 대학과정만 포함 (석사/박사 과정 제외)
        process = row[COL["과정구분"]] if len(row) > COL["과정구분"] else None
        if not process or str(process).strip() != "대학과정":
            continue
        rec = {}
        for name, idx in COL.items():
            if name in ("학교명", "과정구분"):
                continue
            val = row[idx] if len(row) > idx else None
            if name in FLOAT_COLS:
                rec[name] = to_float(val)
            elif name in INT_COLS:
                rec[name] = to_int(val)
            else:
                rec[name] = str(val).strip() if val is not None else None
        rows.append(rec)
    wb.close()
    print(f"  {cfg['year']}: {len(rows)} rows (대학과정)", flush=True)
    return rows


print("데이터 추출 중...", flush=True)
by_year = {}
for cfg in FILES:
    rows = read_file(cfg)
    rows = [r for r in rows if r.get("학과명")]
    by_year[cfg["year"]] = rows
    print(f"    유효 학과 수: {len(rows)}, 취업률 있는 학과: {sum(1 for r in rows if r['취업률_계'] is not None)}", flush=True)

years_list = sorted(by_year.keys())
json_data = json.dumps(by_year, ensure_ascii=False)

# ── HTML ─────────────────────────────────────────────────────────────────────

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>계명대학교 취업통계 대시보드</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>
:root {{
  --bg-base: #f4f6fb;
  --bg-card: #ffffff;
  --sidebar-bg: #1a2744;
  --sidebar-active: #2a3a5c;
  --accent-blue: #2563eb;
  --accent-blue-light: #eff6ff;
  --icon-blue-bg: #dbeafe;
  --icon-green: #10b981;
  --icon-green-bg: #d1fae5;
  --icon-orange: #f59e0b;
  --icon-orange-bg: #fef3c7;
  --icon-purple: #8b5cf6;
  --icon-purple-bg: #ede9fe;
  --text-primary: #111827;
  --text-secondary: #6b7280;
  --text-muted: #9ca3af;
  --border: #e5e7eb;
  --row-hover: #f9fafb;
  --sidebar-w: 200px;
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ height: 100%; }}
body {{
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: 'Noto Sans KR', sans-serif;
  font-size: 14px;
  display: flex;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}}
button {{ font-family: inherit; }}

/* ── SIDEBAR ── */
.sidebar {{
  width: var(--sidebar-w);
  background: var(--sidebar-bg);
  color: #fff;
  position: fixed;
  top: 0; left: 0; bottom: 0;
  display: flex;
  flex-direction: column;
  z-index: 60;
  transition: transform 0.25s ease;
}}
.brand {{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 22px 18px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}}
.brand-shield {{
  width: 36px; height: 36px; flex-shrink: 0;
}}
.brand-text h1 {{
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  line-height: 1.15;
  letter-spacing: 0.2px;
}}
.brand-text p {{
  font-size: 9px;
  font-weight: 500;
  color: #94a3b8;
  letter-spacing: 0.6px;
  margin-top: 2px;
}}
.menu {{ padding: 16px 0; flex: 1; }}
.menu-item {{
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 18px;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border-left: 3px solid transparent;
  user-select: none;
  transition: background 0.15s, color 0.15s;
  min-height: 44px;
}}
.menu-item:hover {{ color: #fff; background: rgba(255,255,255,0.04); }}
.menu-item.active {{
  color: #fff;
  background: var(--sidebar-active);
  border-left-color: #fff;
}}
.menu-item svg {{ width: 18px; height: 18px; flex-shrink: 0; }}

.menu-item[data-tooltip] {{ position: relative; }}
.menu-item[data-tooltip]::after {{
  content: attr(data-tooltip);
  position: absolute;
  left: calc(100% + 12px);
  top: 50%;
  transform: translateY(-50%) translateX(-6px);
  background: #1f2937;
  color: #f9fafb;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.5;
  padding: 10px 14px;
  border-radius: 8px;
  white-space: pre-line;
  width: 220px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.25);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.18s ease, transform 0.18s ease;
  z-index: 70;
}}
.menu-item[data-tooltip]::before {{
  content: '';
  position: absolute;
  left: 100%;
  top: 50%;
  transform: translateY(-50%) translateX(-6px);
  border: 6px solid transparent;
  border-right-color: #1f2937;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.18s ease, transform 0.18s ease;
  z-index: 71;
}}
.menu-item[data-tooltip]:hover::after {{
  opacity: 1;
  transform: translateY(-50%) translateX(0);
}}
.menu-item[data-tooltip]:hover::before {{
  opacity: 1;
  transform: translateY(-50%) translateX(0);
}}
@media (max-width: 767px) {{
  .menu-item[data-tooltip]::after,
  .menu-item[data-tooltip]::before {{ display: none; }}
}}
.sidebar-footer {{
  padding: 16px 18px 18px;
  font-size: 10px;
  color: #64748b;
  line-height: 1.55;
  border-top: 1px solid rgba(255,255,255,0.06);
}}
.sidebar-footer .info-block {{ margin-bottom: 10px; }}
.sidebar-footer .info-label {{
  font-weight: 700;
  color: #94a3b8;
  display: block;
  margin-bottom: 2px;
}}
.sidebar-footer .copyright {{
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(255,255,255,0.06);
  color: #475569;
  font-size: 9px;
  letter-spacing: 0.5px;
}}

.sidebar-overlay {{
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 55;
  display: none;
}}
.sidebar-overlay.show {{ display: block; }}

/* ── MAIN ── */
.main {{
  flex: 1;
  margin-left: var(--sidebar-w);
  display: flex;
  flex-direction: column;
  min-width: 0;
}}

/* mobile top bar (hidden on desktop) */
.mobile-bar {{
  display: none;
  background: #fff;
  border-bottom: 1px solid var(--border);
  padding: 10px 16px;
  align-items: center;
  gap: 12px;
  position: sticky;
  top: 0;
  z-index: 25;
}}
.mobile-bar .ham {{
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  min-height: 44px;
  min-width: 44px;
  color: var(--text-primary);
}}
.mobile-bar h2 {{ font-size: 14px; font-weight: 700; }}

/* sticky header bar */
.header-bar {{
  background: #fff;
  border-bottom: 1px solid var(--border);
  padding: 12px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  position: sticky;
  top: 0;
  z-index: 20;
}}
.year-tabs {{ display: flex; gap: 8px; flex-shrink: 0; }}
.year-tab {{
  background: #fff;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: 6px 20px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  min-height: 36px;
  transition: all 0.15s;
}}
.year-tab:hover {{ border-color: var(--accent-blue); color: var(--accent-blue); }}
.year-tab.active {{
  background: var(--accent-blue);
  color: #fff;
  border-color: var(--accent-blue);
  font-weight: 700;
}}
.filter-area {{
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
  flex-wrap: wrap;
}}
.filter-label {{
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
  white-space: nowrap;
}}
.filter-pills {{
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}}
.pill {{
  background: #fff;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  min-height: 32px;
  white-space: nowrap;
  transition: all 0.15s;
}}
.pill:hover {{ border-color: var(--accent-blue); color: var(--accent-blue); }}
.pill.active {{
  background: var(--accent-blue);
  color: #fff;
  border-color: var(--accent-blue);
}}

.page {{
  padding: 24px;
  flex: 1;
}}

/* ── KPI ── */
.kpi-grid {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}}
.kpi-card {{
  background: var(--bg-card);
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  min-height: 110px;
}}
.kpi-icon {{
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}}
.kpi-icon svg {{ width: 26px; height: 26px; }}
.kpi-body {{ flex: 1; min-width: 0; }}
.kpi-label {{
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 6px;
}}
.kpi-value {{
  font-size: 32px;
  font-weight: 700;
  line-height: 1.1;
  color: var(--text-primary);
}}
.kpi-name {{
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}}
.kpi-pct {{
  font-size: 22px;
  font-weight: 700;
  margin-top: 4px;
  line-height: 1.1;
}}
.kpi-arrow {{
  position: absolute;
  top: 16px;
  right: 16px;
  color: var(--text-muted);
  font-size: 18px;
  font-weight: 400;
  user-select: none;
}}

/* ── SECTIONS ── */
.row {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}}
.card {{
  background: var(--bg-card);
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  padding: 24px;
  min-width: 0;
}}
.card-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}}
.card-title {{
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}}
.card-unit {{
  font-size: 11px;
  color: var(--text-muted);
}}
.chart-wrap {{
  height: 320px;
  position: relative;
}}

/* ── DONUT ── */
.donut-row {{
  display: flex;
  gap: 24px;
  align-items: center;
}}
.donut-canvas-wrap {{
  position: relative;
  width: 220px;
  height: 220px;
  flex-shrink: 0;
}}
.donut-center {{
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  text-align: center;
}}
.donut-center-top {{
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 4px;
}}
.donut-center-year {{
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}}
.donut-legend {{
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}}
.donut-legend-item {{
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}}
.donut-dot {{
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}}
.donut-lbl {{ flex: 1; color: var(--text-secondary); }}
.donut-val {{
  font-weight: 700;
  color: var(--text-primary);
  text-align: right;
}}

/* ── TABLE ── */
.table-wrap {{
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}}
thead th {{
  background: var(--bg-base);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
  padding: 12px 16px;
  text-align: left;
  cursor: pointer;
  user-select: none;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
  transition: color 0.15s;
}}
thead th:hover {{ color: var(--accent-blue); }}
thead th.sorted-asc::after {{ content: ' ↑'; color: var(--accent-blue); }}
thead th.sorted-desc::after {{ content: ' ↓'; color: var(--accent-blue); }}
thead th.num {{ text-align: right; }}
tbody tr {{ transition: background 0.12s; }}
tbody tr:hover {{ background: var(--row-hover); }}
tbody td {{
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  color: var(--text-primary);
}}
.td-num {{ text-align: right; font-weight: 500; }}
.td-rate {{ text-align: right; font-weight: 700; color: var(--accent-blue); }}

.pagination {{
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  padding: 16px 0 4px;
}}
.page-btn {{
  background: #fff;
  border: 1px solid var(--border);
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 13px;
  transition: all 0.15s;
}}
.page-btn:hover:not(:disabled) {{ color: var(--accent-blue); border-color: var(--accent-blue); }}
.page-btn:disabled {{ opacity: 0.35; cursor: not-allowed; }}
.page-info {{
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
  min-width: 50px;
  text-align: center;
}}
.table-note {{
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 8px;
}}

/* ── ANIMATIONS ── */
@keyframes slideUp {{
  from {{ opacity: 0; transform: translateY(20px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
.section-anim {{
  animation: slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}}
.kpi-card.section-anim:nth-child(1) {{ animation-delay: 0ms; }}
.kpi-card.section-anim:nth-child(2) {{ animation-delay: 60ms; }}
.kpi-card.section-anim:nth-child(3) {{ animation-delay: 120ms; }}
.kpi-card.section-anim:nth-child(4) {{ animation-delay: 180ms; }}
.row .card.section-anim:nth-child(1) {{ animation-delay: 240ms; }}
.row .card.section-anim:nth-child(2) {{ animation-delay: 300ms; }}

@keyframes fadeIn {{
  from {{ opacity: 0.2; }}
  to {{ opacity: 1; }}
}}
.fade-cycle {{ animation: fadeIn 0.4s ease both; }}

/* ── RESPONSIVE ── */
@media (max-width: 1023px) {{
  .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
  .row {{ grid-template-columns: 1fr; }}
  .donut-canvas-wrap {{ width: 180px; height: 180px; }}
}}

@media (max-width: 767px) {{
  body {{ display: block; }}
  .sidebar {{
    transform: translateX(-100%);
    width: 240px;
  }}
  .sidebar.open {{ transform: translateX(0); }}
  .main {{ margin-left: 0; }}
  .mobile-bar {{ display: flex; }}
  .header-bar {{
    flex-direction: column;
    align-items: stretch;
    padding: 12px 16px;
  }}
  .year-tabs {{ overflow-x: auto; flex-wrap: nowrap; padding-bottom: 2px; }}
  .year-tabs::-webkit-scrollbar {{ display: none; }}
  .filter-area {{ margin-left: 0; flex-direction: column; align-items: stretch; gap: 8px; }}
  .filter-pills {{
    overflow-x: auto;
    flex-wrap: nowrap;
    padding-bottom: 2px;
  }}
  .filter-pills::-webkit-scrollbar {{ display: none; }}
  .page {{ padding: 16px; }}
  .kpi-grid {{ grid-template-columns: 1fr; gap: 12px; }}
  .kpi-card {{ min-height: 90px; padding: 18px; }}
  .kpi-value {{ font-size: 28px; }}
  .chart-wrap {{ height: 240px; }}
  .donut-row {{ flex-direction: column; align-items: center; }}
  .donut-canvas-wrap {{ width: 200px; height: 200px; }}
  .donut-legend {{ width: 100%; }}
  table {{ table-layout: fixed; }}
  .col-grad {{ display: none; }}
  thead th, tbody td {{ padding: 12px 8px; font-size: 12px; }}
}}
</style>
</head>
<body>

<aside class="sidebar" id="sidebar">
  <div class="brand">
    <svg class="brand-shield" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg">
      <path d="M18 2 L31 6.5 V17 C31 25 25.5 31 18 33.5 C10.5 31 5 25 5 17 V6.5 Z"
            fill="#c9a84c" stroke="#fff" stroke-width="0.8"/>
      <text x="18" y="22" text-anchor="middle"
            font-family="Georgia, serif" font-size="11" font-weight="700" fill="#1a2744">KMU</text>
    </svg>
    <div class="brand-text">
      <h1>계명대학교</h1>
      <p>KEIMYUNG UNIVERSITY</p>
    </div>
  </div>

  <nav class="menu">
    <div class="menu-item active" data-page="dashboard">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="7" height="9"/>
        <rect x="14" y="3" width="7" height="5"/>
        <rect x="14" y="12" width="7" height="9"/>
        <rect x="3" y="16" width="7" height="5"/>
      </svg>
      <span>대시보드</span>
    </div>
    <div class="menu-item" data-page="info" data-tooltip="출처: 한국교육개발원 고등교육기관 졸업자 취업통계&#10;기준일: 매년 12월 31일&#10;대상: 계명대학교 대학과정 졸업자&#10;집계: 학교별 학과별 시트, 학교명='계명대학교' 필터">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="16" x2="12" y2="12"/>
        <circle cx="12" cy="8" r="0.6" fill="currentColor"/>
      </svg>
      <span>데이터 안내</span>
    </div>
  </nav>

  <div class="sidebar-footer">
    <div class="info-block">
      <span class="info-label">데이터 출처</span>
      한국교육개발원<br>고등교육기관 졸업자<br>취업통계
    </div>
    <div class="info-block">
      <span class="info-label">조사 기준일</span>
      매년 12월 31일
    </div>
    <div class="info-block">
      <span class="info-label">대상</span>
      대학과정 졸업자
    </div>
    <div class="copyright">© KEIMYUNG UNIVERSITY</div>
  </div>
</aside>

<div class="sidebar-overlay" id="sidebarOverlay"></div>

<div class="main">
  <div class="mobile-bar">
    <button class="ham" id="hamburger" aria-label="메뉴 열기">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <line x1="3" y1="6" x2="21" y2="6"/>
        <line x1="3" y1="12" x2="21" y2="12"/>
        <line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
    </button>
    <h2>계명대학교 취업통계</h2>
  </div>

  <div class="header-bar">
    <div class="year-tabs" id="yearTabs"></div>
    <div class="filter-area">
      <span class="filter-label">계열 필터</span>
      <div class="filter-pills" id="filterPills"></div>
    </div>
  </div>

  <div class="page">
    <!-- KPI -->
    <div class="kpi-grid">
      <div class="kpi-card section-anim">
        <div class="kpi-icon" style="background:var(--icon-blue-bg);">
          <svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 10 12 5 2 10l10 5z"/>
            <path d="M6 12v5c0 1.5 3 3 6 3s6-1.5 6-3v-5"/>
          </svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">총 학과 수</div>
          <div class="kpi-value" id="kpiTotal" style="color:var(--accent-blue);">—</div>
        </div>
        <span class="kpi-arrow">›</span>
      </div>

      <div class="kpi-card section-anim">
        <div class="kpi-icon" style="background:var(--icon-green-bg);">
          <svg viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
            <polyline points="16 7 22 7 22 13"/>
          </svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">평균 취업률</div>
          <div class="kpi-value" id="kpiAvg" style="color:var(--icon-green);">—</div>
        </div>
        <span class="kpi-arrow">›</span>
      </div>

      <div class="kpi-card section-anim">
        <div class="kpi-icon" style="background:var(--icon-orange-bg);">
          <svg viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 15 8.5 22 9.5 17 14.5 18.2 21.5 12 18 5.8 21.5 7 14.5 2 9.5 9 8.5"/>
          </svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">최고 취업률 학과</div>
          <div class="kpi-name" id="kpiBestName">—</div>
          <div class="kpi-pct" id="kpiBestRate" style="color:var(--icon-orange);">—</div>
        </div>
        <span class="kpi-arrow">›</span>
      </div>

      <div class="kpi-card section-anim">
        <div class="kpi-icon" style="background:var(--icon-purple-bg);">
          <svg viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <path d="M16 16s-1.5-2-4-2-4 2-4 2"/>
            <line x1="9" y1="9" x2="9.01" y2="9"/>
            <line x1="15" y1="9" x2="15.01" y2="9"/>
          </svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">최저 취업률 학과</div>
          <div class="kpi-name" id="kpiWorstName">—</div>
          <div class="kpi-pct" id="kpiWorstRate" style="color:var(--icon-purple);">—</div>
        </div>
        <span class="kpi-arrow">›</span>
      </div>
    </div>

    <!-- Middle row: bar + donut -->
    <div class="row">
      <div class="card section-anim">
        <div class="card-header">
          <span class="card-title">대계열별 평균 취업률 비교</span>
          <span class="card-unit">(단위: %)</span>
        </div>
        <div class="chart-wrap"><canvas id="barChart"></canvas></div>
      </div>
      <div class="card section-anim">
        <div class="card-header">
          <span class="card-title">취업 유형 분포</span>
        </div>
        <div class="donut-row">
          <div class="donut-canvas-wrap">
            <canvas id="donutChart"></canvas>
            <div class="donut-center">
              <div class="donut-center-top">취업자 기준</div>
              <div class="donut-center-year" id="donutYear">—</div>
            </div>
          </div>
          <div class="donut-legend" id="donutLegend"></div>
        </div>
      </div>
    </div>

    <!-- Bottom row: table + retention -->
    <div class="row">
      <div class="card section-anim">
        <div class="card-header">
          <span class="card-title">학과별 취업 현황</span>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th data-col="학과명" id="th-학과명">학과명</th>
                <th class="num col-grad" data-col="졸업자_계" id="th-졸업자_계">졸업자 수</th>
                <th class="num" data-col="취업자_합계_계" id="th-취업자_합계_계">취업자 수</th>
                <th class="num" data-col="취업률_계" id="th-취업률_계">취업률(%)</th>
              </tr>
            </thead>
            <tbody id="tableBody"></tbody>
          </table>
        </div>
        <div class="pagination">
          <button class="page-btn" id="prevPage" aria-label="이전 페이지">‹</button>
          <span class="page-info" id="pageInfo">1/1</span>
          <button class="page-btn" id="nextPage" aria-label="다음 페이지">›</button>
        </div>
        <div class="table-note">※ 컬럼 헤더를 클릭하면 오름차순/내림차순 정렬이 가능합니다.</div>
      </div>
      <div class="card section-anim">
        <div class="card-header">
          <span class="card-title">유지취업률 추이</span>
        </div>
        <div class="chart-wrap"><canvas id="retentionChart"></canvas></div>
      </div>
    </div>
  </div>
</div>

<script>
const DATA = {json_data};
const YEARS = {json.dumps(years_list)};

let activeYear = YEARS[YEARS.length - 1];
let seriesFilter = 'ALL';
let sortCol = '취업률_계';
let sortDir = -1;
let currentPage = 1;
const PAGE_SIZE = 10;
let initialAnim = true;

let barInst = null, donutInst = null, retInst = null;

const DONUT_COLORS = ['#2563eb','#0d9488','#8b5cf6','#f59e0b','#fbbf24'];
const DONUT_LABELS = ['교외취업','교내취업','해외취업','프리랜서','1인창업'];
const DONUT_KEYS   = ['취업자_교외취업자_계','취업자_교내취업자_계','취업자_해외취업자_계','취업자_프리랜서_계','취업자_1인창(사)업자_계'];
const RET_KEYS = ['1차 유지취업률_계','2차 유지취업률_계','3차 유지취업률_계','4차 유지취업률_계'];
const RET_LABELS = ['1차 (1년)','2차 (2년)','3차 (3년)','4차 (4년)'];
const YEAR_COLORS = {{ 2022: '#9ca3af', 2023: '#0d9488', 2024: '#2563eb' }};

const avg = arr => arr.length ? arr.reduce((a,b)=>a+b,0)/arr.length : null;
const fmtRate = v => v == null ? '—' : v.toFixed(1) + '%';
const fmtInt = v => v == null ? '—' : Number(v).toLocaleString();

function yearRows(withRate = true) {{
  const rows = DATA[activeYear] || [];
  return withRate ? rows.filter(r => r.취업률_계 != null) : rows;
}}
function filteredRows() {{
  let rows = yearRows(true);
  if (seriesFilter !== 'ALL') rows = rows.filter(r => r.대계열 === seriesFilter);
  return rows;
}}

// ── tabs ──
function buildTabs() {{
  const c = document.getElementById('yearTabs');
  c.innerHTML = '';
  YEARS.forEach(y => {{
    const b = document.createElement('button');
    b.className = 'year-tab' + (y === activeYear ? ' active' : '');
    b.textContent = y;
    b.onclick = () => switchYear(y);
    c.appendChild(b);
  }});
}}

// ── filter pills ──
function buildPills() {{
  const all = [...new Set((DATA[activeYear]||[]).map(r=>r.대계열).filter(Boolean))].sort();
  const c = document.getElementById('filterPills');
  c.innerHTML = '';
  ['ALL', ...all].forEach(s => {{
    const b = document.createElement('button');
    b.className = 'pill' + (s === seriesFilter ? ' active' : '');
    b.textContent = s === 'ALL' ? '전체' : s;
    b.onclick = () => {{
      seriesFilter = s;
      buildPills();
      currentPage = 1;
      renderTable();
      updateDonut(false);
    }};
    c.appendChild(b);
  }});
}}

// ── KPI ──
function updateKPI() {{
  const rows = yearRows(true);
  const total = (DATA[activeYear] || []).length;
  const avgR = avg(rows.map(r => r.취업률_계));
  const sorted = [...rows].sort((a,b) => b.취업률_계 - a.취업률_계);
  const best = sorted[0], worst = sorted[sorted.length - 1];

  document.getElementById('kpiTotal').textContent = total;
  document.getElementById('kpiAvg').textContent = fmtRate(avgR);
  document.getElementById('kpiBestName').textContent = best ? best.학과명 : '—';
  document.getElementById('kpiBestRate').textContent = best ? fmtRate(best.취업률_계) : '';
  document.getElementById('kpiWorstName').textContent = worst ? worst.학과명 : '—';
  document.getElementById('kpiWorstRate').textContent = worst ? fmtRate(worst.취업률_계) : '';
  document.getElementById('donutYear').textContent = activeYear + '년';
}}

// ── bar chart (vertical) ──
const barLabelPlugin = {{
  id: 'barLabels',
  afterDatasetsDraw(chart) {{
    const ds = chart.getDatasetMeta(0);
    if (!ds || !ds.data) return;
    const ctx = chart.ctx;
    const values = chart.data.datasets[0].data;
    ctx.save();
    ctx.fillStyle = '#111827';
    ctx.font = '700 12px "Noto Sans KR"';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ds.data.forEach((bar, i) => {{
      const v = values[i];
      if (v == null) return;
      ctx.fillText(v.toFixed(1), bar.x, bar.y - 6);
    }});
    ctx.restore();
  }}
}};

function updateBarChart(animate=true) {{
  const rows = yearRows(true);
  const map = {{}};
  rows.forEach(r => {{
    if (!r.대계열) return;
    (map[r.대계열] = map[r.대계열] || []).push(r.취업률_계);
  }});
  const labels = Object.keys(map).sort();
  const values = labels.map(s => parseFloat(avg(map[s]).toFixed(1)));

  if (barInst) {{ barInst.destroy(); barInst = null; }}
  const ctx = document.getElementById('barChart').getContext('2d');
  barInst = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels,
      datasets: [{{
        data: values,
        backgroundColor: '#2563eb',
        hoverBackgroundColor: '#1d4ed8',
        borderRadius: 6,
        barPercentage: 0.65,
        categoryPercentage: 0.8,
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      animation: animate ? {{ duration: 800, easing: 'easeOutQuart' }} : {{ duration: 400 }},
      layout: {{ padding: {{ top: 20 }} }},
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{ label: c => ' 평균 취업률: ' + c.parsed.y.toFixed(1) + '%' }}
        }}
      }},
      scales: {{
        x: {{
          grid: {{ display: false }},
          ticks: {{ color: '#6b7280', font: {{ size: 12, family: 'Noto Sans KR' }} }}
        }},
        y: {{
          min: 0, max: 100,
          grid: {{ color: '#e5e7eb' }},
          border: {{ display: false }},
          ticks: {{ color: '#9ca3af', font: {{ size: 11 }}, callback: v => v + '%' }}
        }}
      }}
    }},
    plugins: [barLabelPlugin]
  }});
}}

// ── donut ──
function updateDonut(animate=true) {{
  const rows = filteredRows().length ? filteredRows() : yearRows(false);
  const data = DONUT_KEYS.map(k => rows.reduce((s,r) => s + (r[k] || 0), 0));
  const total = data.reduce((a,b)=>a+b,0);

  const leg = document.getElementById('donutLegend');
  leg.innerHTML = '';
  DONUT_LABELS.forEach((lbl,i) => {{
    const pct = total ? ((data[i]/total)*100).toFixed(1) : '0.0';
    const item = document.createElement('div');
    item.className = 'donut-legend-item';
    item.innerHTML =
      '<span class="donut-dot" style="background:'+DONUT_COLORS[i]+'"></span>' +
      '<span class="donut-lbl">'+lbl+'</span>' +
      '<span class="donut-val">'+pct+'%</span>';
    leg.appendChild(item);
  }});

  if (donutInst) {{ donutInst.destroy(); donutInst = null; }}
  const ctx = document.getElementById('donutChart').getContext('2d');
  donutInst = new Chart(ctx, {{
    type: 'doughnut',
    data: {{
      labels: DONUT_LABELS,
      datasets: [{{
        data,
        backgroundColor: DONUT_COLORS,
        borderColor: '#fff',
        borderWidth: 2,
        hoverOffset: 6,
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      animation: animate ? {{ animateRotate: true, animateScale: false, duration: 1000, easing: 'easeOutQuart' }} : {{ duration: 400 }},
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{ label: c => ' '+c.label+': '+Number(c.parsed).toLocaleString()+'명' }}
        }}
      }}
    }}
  }});
}}

// ── retention (3 years) ──
const retLabelPlugin = {{
  id: 'retLabels',
  afterDatasetsDraw(chart) {{
    const ctx = chart.ctx;
    ctx.save();
    chart.data.datasets.forEach((ds, di) => {{
      if (!chart.isDatasetVisible(di)) return;
      const meta = chart.getDatasetMeta(di);
      ctx.fillStyle = ds.borderColor;
      ctx.font = '600 10px "Noto Sans KR"';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      meta.data.forEach((pt, i) => {{
        const v = ds.data[i];
        if (v == null) return;
        ctx.fillText(v.toFixed(1), pt.x, pt.y - 8);
      }});
    }});
    ctx.restore();
  }}
}};

function updateRetention(animate=true) {{
  const rows = (DATA[activeYear] || []).filter(r => r['취업률_계'] != null);
  const data = RET_KEYS.map(k => {{
    const v = rows.map(r => r[k]).filter(x => x != null);
    return v.length ? parseFloat(avg(v).toFixed(1)) : null;
  }});
  const color = YEAR_COLORS[activeYear] || '#2563eb';
  const datasets = [{{
    label: activeYear + '년',
    data,
    borderColor: color,
    backgroundColor: color,
    pointRadius: 5,
    pointHoverRadius: 7,
    pointBackgroundColor: color,
    pointBorderColor: '#fff',
    pointBorderWidth: 2,
    borderWidth: 3,
    tension: 0.25,
    fill: false,
  }}];

  if (retInst) {{ retInst.destroy(); retInst = null; }}
  const ctx = document.getElementById('retentionChart').getContext('2d');

  const animOpt = animate ? {{
    duration: 1000,
    easing: 'easeOutQuart',
    x: {{
      type: 'number',
      easing: 'linear',
      duration: 1000,
      from: NaN,
      delay(c) {{
        if (c.type !== 'data' || c.xStarted) return 0;
        c.xStarted = true;
        return c.dataIndex * (1000 / RET_LABELS.length);
      }}
    }},
    y: {{
      type: 'number',
      easing: 'linear',
      duration: 0
    }}
  }} : {{ duration: 400 }};

  retInst = new Chart(ctx, {{
    type: 'line',
    data: {{ labels: RET_LABELS, datasets }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      animation: animOpt,
      layout: {{ padding: {{ top: 24, right: 8 }} }},
      plugins: {{
        legend: {{
          position: 'top',
          align: 'end',
          labels: {{
            usePointStyle: true,
            pointStyle: 'circle',
            boxWidth: 8,
            color: '#6b7280',
            font: {{ size: 12, family: 'Noto Sans KR' }}
          }}
        }},
        tooltip: {{ mode: 'index', intersect: false }}
      }},
      interaction: {{ mode: 'nearest', axis: 'x', intersect: false }},
      scales: {{
        x: {{
          grid: {{ display: false }},
          ticks: {{ color: '#6b7280', font: {{ size: 11 }} }}
        }},
        y: {{
          min: 50, max: 100,
          grid: {{ color: '#e5e7eb' }},
          border: {{ display: false }},
          ticks: {{ color: '#9ca3af', callback: v => v + '%' }}
        }}
      }}
    }},
    plugins: [retLabelPlugin]
  }});
}}

// ── table ──
function renderTable() {{
  let rows = filteredRows();
  rows = [...rows].sort((a,b) => {{
    const av = a[sortCol], bv = b[sortCol];
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    if (typeof av === 'string') return sortDir * av.localeCompare(bv,'ko');
    return sortDir * (av - bv);
  }});

  const totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  if (currentPage > totalPages) currentPage = totalPages;
  if (currentPage < 1) currentPage = 1;
  const start = (currentPage - 1) * PAGE_SIZE;
  const pageRows = rows.slice(start, start + PAGE_SIZE);

  const tbody = document.getElementById('tableBody');
  if (!pageRows.length) {{
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:40px;color:#9ca3af;">데이터 없음</td></tr>';
  }} else {{
    tbody.innerHTML = pageRows.map(r => `
      <tr>
        <td>${{r.학과명 || '—'}}</td>
        <td class="td-num col-grad">${{fmtInt(r.졸업자_계)}}</td>
        <td class="td-num">${{fmtInt(r.취업자_합계_계)}}</td>
        <td class="td-rate">${{fmtRate(r.취업률_계)}}</td>
      </tr>`).join('');
  }}

  document.getElementById('pageInfo').textContent = currentPage + '/' + totalPages;
  document.getElementById('prevPage').disabled = currentPage <= 1;
  document.getElementById('nextPage').disabled = currentPage >= totalPages;

  ['학과명','졸업자_계','취업자_합계_계','취업률_계'].forEach(k => {{
    const el = document.getElementById('th-'+k);
    if (el) el.classList.remove('sorted-asc','sorted-desc');
  }});
  const th = document.getElementById('th-'+sortCol);
  if (th) th.classList.add(sortDir > 0 ? 'sorted-asc' : 'sorted-desc');
}}

document.querySelectorAll('thead th[data-col]').forEach(th => {{
  th.onclick = () => {{
    const col = th.getAttribute('data-col');
    if (sortCol === col) sortDir *= -1;
    else {{ sortCol = col; sortDir = -1; }}
    renderTable();
  }};
}});

// pagination
document.getElementById('prevPage').onclick = () => {{ if (currentPage > 1) {{ currentPage--; renderTable(); }} }};
document.getElementById('nextPage').onclick = () => {{ currentPage++; renderTable(); }};

// ── year switch with fade ──
function switchYear(year) {{
  if (year === activeYear) return;
  activeYear = year;
  seriesFilter = 'ALL';
  sortCol = '취업률_계';
  sortDir = -1;
  currentPage = 1;

  document.querySelectorAll('.year-tab').forEach(t =>
    t.classList.toggle('active', parseInt(t.textContent) === year));

  const cards = document.querySelectorAll('.kpi-card, .row .card');
  cards.forEach(c => {{
    c.classList.remove('fade-cycle');
    void c.offsetWidth;
    c.classList.add('fade-cycle');
  }});

  updateKPI();
  buildPills();
  updateBarChart(false);
  renderTable();
  updateDonut(false);
  updateRetention(false);
}}

// ── sidebar mobile toggle ──
document.getElementById('hamburger').onclick = () => {{
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('sidebarOverlay').classList.toggle('show');
}};
document.getElementById('sidebarOverlay').onclick = () => {{
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sidebarOverlay').classList.remove('show');
}};

// ── init ──
buildTabs();
buildPills();
updateKPI();
updateBarChart(true);
renderTable();
updateDonut(true);
updateRetention(true);
</script>
</body>
</html>"""

out_path = "keimyung_employment_dashboard.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n완료: {out_path} ({os.path.getsize(out_path)//1024} KB)", flush=True)
