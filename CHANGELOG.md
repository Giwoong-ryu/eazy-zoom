# Eazy Zoom - 개발 이슈 및 해결 기록

## v1.0.0 (2026-03-12)

### 해결된 이슈

| # | 증상 | 원인 | 해결 |
|---|------|------|------|
| 1 | 버튼이 안 보이고 마우스오버 시에만 보임 | QGraphicsDropShadowEffect가 objectName 기반 QSS를 덮어씀 | GlowButton 제거, setStyleSheet 직접 적용 + _hover_btn() 헬퍼 |
| 2 | QLabel에 테두리 박스가 생김 | _PANEL_BG 스타일이 border:1px solid을 모든 자식에 적용 | QWidget#panel {} 셀렉터 스코핑 + QLabel에 border:none 명시 |
| 3 | 설정 변경 시 화면 깜박임 | _apply_settings()가 overlay를 삭제 후 재생성 | live_update() 메서드로 프로퍼티만 변경 (위젯 재생성 없음) |
| 4 | run.bat 실행 시 cmd만 뜨고 프로그램 안 뜸 | WindowsApps의 python이 스토어 리다이렉터 | py 런처 사용, 최종적으로 VBS 래퍼(EazyZoom.vbs)로 해결 |
| 5 | .pyw 더블클릭 시 아무 반응 없음 | .pyw 파일 연결이 시스템에 미등록 | VBS 래퍼로 cmd 창 없이 py main.py 실행 |
| 6 | pip install이 매번 실행되어 시작 지연 | run.bat에 pip install -r requirements.txt 포함 | 제거 (이미 설치된 환경 전제) |

### 구현된 기능

| 기능 | 설명 |
|------|------|
| 네온 글로우 UI | 라운드 코너(12px) + 3겹 글로우 보더 + 다크 테마 |
| 5가지 커서 스타일 | 줄 하이라이트, 원형 링, 점, 사각, 없음 |
| 줌 배지 애니메이션 | 배율 변경 시 우하단 배지 페이드인/아웃 |
| 실시간 설정 | 슬라이더+스핀박스, 저장 버튼 없이 즉시 반영 |
| Ctrl 고정 모드 | Ctrl 누르면 캡처 영역 고정, 커서만 독립 이동 |
| 캡처 영역 하이라이트 | 실제 화면에 캡처 범위 표시 (브리딩 애니메이션) |
| 가장자리 리사이즈 | 8방향 드래그로 오버레이 크기 조절 |
| 상태 유지 | 창 위치, 크기, 커서 스타일 재시작 후 복원 |
| 한글 UI | 모든 텍스트 한글화 (Eazy Zoom) |
