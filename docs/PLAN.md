# 구현 계획 — 반도체 시료 생산주문관리 시스템

> 상세 요구사항은 `docs/SPEC.md` · `docs/PRD.md` 참고  
> **모든 Phase는 테스트 작성 → 구현 → 통과 확인 → 리팩토링 → 통과 확인 순서(TDD)로 진행한다.**

---

## Phase 1 — 도메인 모델

**대상 파일:** `models/order.py`, `models/sample.py`, `models/production_line.py`  
**테스트 파일:** `tests/test_models.py`

### 테스트 케이스 (먼저 작성)

- `Order` 생성 시 기본 상태가 `RESERVED`인지 확인
- `Sample` 의 `yield_rate`가 0 이하이면 예외 발생
- `ProductionQueue`에 Job을 추가하면 FIFO 순서로 꺼내지는지 확인

### 구현

- `OrderStatus` enum: `RESERVED` / `REJECTED` / `PRODUCING` / `CONFIRMED` / `RELEASE`
- `Order` dataclass: `order_id`, `sample_id`, `customer`, `quantity`, `status`
- `Sample` dataclass: `sample_id`, `name`, `avg_production_time`, `yield_rate`, `stock`
- `ProductionJob` dataclass: `order_id`, `sample_id`, `actual_production`, `total_time`, `produced_so_far`
- `ProductionQueue`: `deque` 기반 FIFO 큐

### 체크리스트

- [x] `test_models.py` 테스트 케이스 작성
- [x] `models/` 구현 후 테스트 통과 확인

---

## Phase 2 — Repository (영속성 레이어)

**대상 파일:** `repositories/json_repository.py`, `repositories/sample_repository.py`, `repositories/order_repository.py`, `repositories/production_repository.py`  
**테스트 파일:** `tests/test_repositories.py`

### 테스트 케이스 (먼저 작성)

- `SampleRepository`: 저장 후 로드 시 동일한 데이터가 반환되는지 확인
- `OrderRepository`: 상태별 필터 조회(`find_by_status`) 결과가 정확한지 확인
- `ProductionRepository`: 큐 저장 후 로드 시 순서가 유지되는지 확인
- JSON 파일이 없을 때 빈 결과를 반환하는지 확인

### 구현

- `json_repository.py`: `load(filepath) -> list`, `save(filepath, data)` (indent=2) — 파일 없을 때 `[]` 반환
- `base_repository.py`: `find_all` / `find_by_id` / `save(upsert)` 공통 추상 베이스 클래스
- `SampleRepository` / `OrderRepository`는 `BaseRepository` 상속, 직렬화 메서드(`_to_dict`, `_from_dict`, `_id_of`)만 구현
- 변경 발생 즉시 저장

### 체크리스트

- [x] `test_repositories.py` 테스트 케이스 작성
- [x] `repositories/` 구현 후 테스트 통과 확인

---

## Phase 3 — SampleController

**대상 파일:** `controllers/sample_controller.py`  
**테스트 파일:** `tests/test_sample_controller.py`

### 테스트 케이스 (먼저 작성)

- `register()` 호출 후 `list_all()`에 해당 시료가 포함되는지 확인
- 동일 `sample_id`로 중복 등록 시 예외 발생
- `search(keyword)` 가 이름에 키워드를 포함한 시료만 반환하는지 확인

### 구현

| 메서드 | 설명 |
|--------|------|
| `register(sample_id, name, avg_time, yield_rate)` | 시료 등록 |
| `list_all() -> list[Sample]` | 전체 시료 목록 반환 |
| `search(keyword) -> list[Sample]` | 이름 포함 검색 |

### 체크리스트

- [x] `test_sample_controller.py` 테스트 케이스 작성
- [x] `SampleController` 구현 후 테스트 통과 확인

---

## Phase 4 — OrderController (접수·거절)

**대상 파일:** `controllers/order_controller.py`  
**테스트 파일:** `tests/test_order_controller.py`

### 테스트 케이스 (먼저 작성)

- `reserve()` 호출 후 주문 상태가 `RESERVED`인지 확인
- 등록되지 않은 `sample_id`로 예약 시 예외 발생
- `reject()` 호출 후 주문 상태가 `REJECTED`인지 확인
- `list_reserved()`가 `RESERVED` 상태 주문만 반환하는지 확인

### 구현

| 메서드 | 설명 |
|--------|------|
| `reserve(sample_id, customer, quantity) -> Order` | 주문 접수 → `RESERVED` |
| `list_reserved() -> list[Order]` | `RESERVED` 목록 반환 |
| `reject(order_id)` | `REJECTED` 전환 |

### 체크리스트

- [x] `test_order_controller.py` 접수·거절 테스트 케이스 작성
- [x] `OrderController` 접수·거절 구현 후 테스트 통과 확인

---

## Phase 5 — OrderController (승인·재고 분기)

**대상 파일:** `controllers/order_controller.py` (승인 로직 추가)  
**테스트 파일:** `tests/test_order_controller.py` (케이스 추가)

### 테스트 케이스 (먼저 작성)

- 재고 ≥ 주문 수량일 때 `approve()` 호출 → 주문 상태가 `CONFIRMED`인지 확인
- 재고 < 주문 수량일 때 `approve()` 호출 → 주문 상태가 `PRODUCING`이고 생산 큐에 Job이 추가됐는지 확인
- 생산 큐 Job의 `actual_production`이 `ceil(부족분 / (yield_rate * 0.9))`와 일치하는지 확인

### 구현

```
shortage = order.quantity - sample.stock
actual   = ceil(shortage / (sample.yield_rate * 0.9))
total_time = sample.avg_production_time * actual
```

- 재고 충분 → `order.status = CONFIRMED`
- 재고 부족 → `ProductionJob` 생성 후 큐 등록, `order.status = PRODUCING`

### 체크리스트

- [x] 승인 재고 분기 테스트 케이스 작성
- [x] 생산량 계산 공식 테스트 케이스 작성
- [x] `OrderController.approve` 구현 후 테스트 통과 확인

---

## Phase 6 — ProductionController

**대상 파일:** `controllers/production_controller.py`  
**테스트 파일:** `tests/test_production_controller.py`

### 테스트 케이스 (먼저 작성)

- `list_queue()`가 FIFO 순서대로 대기 목록을 반환하는지 확인
- `complete_job()` 호출 후 해당 주문 상태가 `CONFIRMED`으로 전환되는지 확인
- `complete_job()` 호출 후 시료 재고가 `actual_production`만큼 증가하는지 확인

### 구현

| 메서드 | 설명 |
|--------|------|
| `get_current_job() -> ProductionJob \| None` | 현재 생산 중인 작업 반환 |
| `list_queue() -> list[ProductionJob]` | 대기 중인 생산 큐 목록 반환 |
| `complete_job(job_id)` | 생산 완료 → 재고 추가 → 주문 `CONFIRMED` 전환 |

### 체크리스트

- [x] `test_production_controller.py` 테스트 케이스 작성
- [x] `ProductionController` 구현 후 테스트 통과 확인

---

## Phase 7 — ReleaseController

**대상 파일:** `controllers/release_controller.py`  
**테스트 파일:** `tests/test_release_controller.py`

### 테스트 케이스 (먼저 작성)

- `release()` 호출 후 주문 상태가 `RELEASE`인지 확인
- `CONFIRMED`가 아닌 주문에 `release()` 호출 시 예외 발생
- `list_confirmed()`가 `CONFIRMED` 상태 주문만 반환하는지 확인

### 구현

| 메서드 | 설명 |
|--------|------|
| `list_confirmed() -> list[Order]` | `CONFIRMED` 목록 반환 |
| `release(order_id)` | `CONFIRMED` → `RELEASE` 전환 |

### 체크리스트

- [x] `test_release_controller.py` 테스트 케이스 작성
- [x] `ReleaseController` 구현 후 테스트 통과 확인

---

## Phase 8 — View (메인·시료·주문)

**대상 파일:** `views/common.py`, `views/main_view.py`, `views/sample_view.py`, `views/order_view.py`  
**테스트 파일:** `tests/test_views.py` (`monkeypatch` + `capsys` 활용, pexpect는 Windows 미지원)

View는 입력 수집과 결과 출력만 담당한다. 비즈니스 로직은 Controller에 위임한다.

### 구현

- `common.py`: 공통 출력 유틸 (`header`, `section`, `success`, `error`, `divider`, `ask`, `ask_int`, `ask_float`, `menu_item`) — colorama 활용
- `main_view.py`: 메인 메뉴 5개 항목 출력, 전체 시료 요약 표시
- `sample_view.py`: 시료 등록 입력 폼, 목록 테이블(재고 포함), 검색 결과
- `order_view.py`: 주문 접수 입력 폼, `RESERVED` 목록, 승인/거절 선택

### 체크리스트

- [x] `views/common.py` 공통 유틸 구현
- [x] `main_view.py` 메뉴 루프 구현
- [x] `sample_view.py` 구현
- [x] `order_view.py` 구현
- [x] `tests/test_views.py` 작성 및 통과

---

## Phase 9 — View (모니터링·생산라인·출고)

**대상 파일:** `views/monitoring_view.py`, `views/production_view.py`, `views/release_view.py`

### 구현

- `monitoring_view.py`
  - 상태별 주문 수 요약 (`RESERVED` / `PRODUCING` / `CONFIRMED` / `RELEASE`, `REJECTED` 제외)
  - 시료별 재고 현황 + 상태 태그: `여유` (재고 ≥ 주문) / `부족` (0 < 재고 < 주문) / `고갈` (재고 = 0)
- `production_view.py`: 현재 생산 작업 정보, 대기 큐 목록
- `release_view.py`: `CONFIRMED` 주문 목록, 출고 선택 UI

### 체크리스트

- [x] `monitoring_view.py` 구현
- [x] `production_view.py` 구현
- [x] `release_view.py` 구현
- [x] `tests/test_views.py` 케이스 추가 및 통과

---

## Phase 10 — main.py 통합

**대상 파일:** `main.py`

### 구현

- 컨트롤러 초기화 및 Repository 인스턴스 공유 연결
- 메뉴 선택값 → View·Controller 호출 라우팅
- 잘못된 입력 재입력 처리 및 종료 옵션

### 통합 시나리오 검증 (수동)

1. 시료 등록 → 주문 접수 → 승인(재고 부족) → 생산 완료 → 출고
2. 시료 등록 → 주문 접수 → 승인(재고 충분) → 출고
3. 주문 접수 → 거절 → 모니터링에서 미노출 확인

### 체크리스트

- [x] `main_view.py` Phase 9 View 연결 (`order_repo` 파라미터 추가)
- [x] `main.py` 진입점 구현
- [x] `tests/test_views.py` `TestMainView` 7개 케이스 추가 및 통과
- [ ] 통합 시나리오 1·2·3 수동 검증 완료

---

## Phase 11 — 더미 데이터 생성 도구

**대상 파일:** `tools/dummy_data.py`

- 시료 3~5개, 다양한 상태(`RESERVED` / `PRODUCING` / `CONFIRMED` / `RELEASE`)의 주문 10개 이상 생성
- 실행 시 `data/*.json`에 직접 기록

```bash
python tools/dummy_data.py
```

### 체크리스트

- [ ] 시료·주문 더미 데이터 생성 구현
- [ ] `data/*.json` 저장 동작 확인

---

## Phase 12 — 관리자용 데이터 모니터링 도구

**대상 파일:** `tools/monitor.py`

- `data/*.json`을 읽어 시료·주문·생산 큐 현황을 콘솔에 출력
- 애플리케이션 실행 없이 독립 실행 가능

```bash
python tools/monitor.py
```

### 체크리스트

- [ ] `data/*.json` 직접 읽기 구현
- [ ] 시료·주문·생산 큐 포맷 출력 구현

---

## 구현 순서

```
Phase  1  도메인 모델
Phase  2  Repository
Phase  3  SampleController
Phase  4  OrderController — 접수·거절
Phase  5  OrderController — 승인·재고 분기
Phase  6  ProductionController
Phase  7  ReleaseController
Phase  8  View — 메인·시료·주문
Phase  9  View — 모니터링·생산라인·출고
Phase 10  main.py 통합
Phase 11  더미 데이터 도구
Phase 12  관리자 모니터링 도구
```
