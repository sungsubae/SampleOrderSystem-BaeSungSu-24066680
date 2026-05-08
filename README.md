# 반도체 시료 생산주문관리 시스템

반도체 회사 S-Semi의 시료(Sample) 주문 접수부터 생산·출고까지 전 과정을 관리하는 콘솔 기반 애플리케이션입니다.

---

## 기능

| 메뉴 | 기능 |
|------|------|
| 시료 관리 | 시료 등록 · 목록 조회 · 이름 검색 |
| 주문 관리 | 주문 접수 · 승인 · 거절 |
| 모니터링 | 상태별 주문 목록 · 시료별 재고 현황(여유/부족/고갈) |
| 출고 처리 | CONFIRMED 주문 출고 실행 |
| 생산 라인 | 현재 생산 작업 정보 · 대기 큐 확인 · 생산 완료 처리 |

### 주문 상태 흐름

```
RESERVED ──(승인, 재고 충분)──► CONFIRMED ──► RELEASE
         ──(승인, 재고 부족)──► PRODUCING ──► CONFIRMED ──► RELEASE
         ──(거절)────────────► REJECTED
```

- 승인 시 재고가 충분하면 즉시 재고를 차감하고 CONFIRMED로 전환합니다.
- 재고가 부족하면 생산 큐(FIFO)에 등록하고 PRODUCING으로 전환합니다.
- REJECTED 주문은 모니터링에서 제외됩니다.

---

## 기술 스택

- **언어**: Python 3.14
- **아키텍처**: MVC (models / controllers / views)
- **영속성**: JSON 파일 (`data/*.json`)
- **테스트**: pytest + pytest-cov

---

## 설치 및 실행

```bash
# 가상환경 활성화
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux

# 앱 실행
python main.py

# 더미 데이터 생성 (선택)
python tools/dummy_data.py

# 관리자 데이터 모니터링 (앱 외부에서 확인)
python tools/monitor.py
```

---

## 테스트

```bash
# 전체 테스트
python -m pytest

# 커버리지 포함
python -m pytest --cov=models --cov=repositories --cov=controllers --cov=views --cov-report=term-missing

# E2E 테스트만
python -m pytest tests/test_e2e.py -v

# 단일 테스트
python -m pytest tests/test_order_controller.py::TestApproveWithSufficientStock -v
```

---

## 프로젝트 구조

```
main.py                         # 진입점
models/                         # 도메인 모델
  order.py                      # Order, OrderStatus
  sample.py                     # Sample
  production_line.py            # ProductionJob, ProductionQueue
repositories/                   # JSON 영속성 레이어
  base_repository.py            # 공통 CRUD 추상 베이스
  json_repository.py            # load / save 유틸
  sample_repository.py
  order_repository.py
  production_repository.py
controllers/                    # 비즈니스 로직
  sample_controller.py
  order_controller.py           # approve 시 재고 차감
  production_controller.py
  release_controller.py
views/                          # 콘솔 UI
  common.py                     # 공통 출력 유틸 (colorama 기반)
  main_view.py
  sample_view.py
  order_view.py
  monitoring_view.py
  production_view.py
  release_view.py
tools/
  dummy_data.py                 # 테스트용 더미 데이터 생성
  monitor.py                    # 관리자용 독립 실행 모니터링
data/                           # 런타임 생성 JSON 파일
tests/
  test_models.py
  test_repositories.py
  test_sample_controller.py
  test_order_controller.py
  test_production_controller.py
  test_release_controller.py
  test_views.py
  test_dummy_data.py
  test_monitor.py
  test_e2e.py                   # E2E 시나리오 테스트
```

---

## 생산량 계산 공식

```
실 생산량 = ceil(부족분 / (수율 × 0.9))
총 생산 시간 = 평균 생산시간 × 실 생산량
```
