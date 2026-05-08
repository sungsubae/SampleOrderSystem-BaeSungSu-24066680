# SPEC/PRD 검증 보고서

**검증일**: 2026-05-08  
**기준 문서**: `docs/SPEC.md`, `docs/PRD.md`

---

## 검증 결과 요약

| # | 항목 | 파일 | 심각도 | 상태 |
|---|------|------|--------|------|
| 1 | 모니터링 주문 현황 — 건수만 출력, 목록 누락 | `views/monitoring_view.py:20-23` | **필수** | ✅ 수정 완료 |
| 2 | 출고(RELEASE) 시 재고 미차감 | `controllers/release_controller.py:18` | 필수 | ✅ 수정 완료 |

---

## 이슈 #1 — 모니터링 주문 현황: 목록 누락 (필수)

### 요구사항

**SPEC.md**
> 현재 상태별(RESERVED/CONFIRMED/PRODUCING/RELEASE) **목록을 확인**

**PRD.md 4.5.1**
> 현재 상태별(RESERVED / PRODUCING / CONFIRMED / RELEASE) **주문 목록을 표시**한다.

### 현재 구현 (`monitoring_view.py:20-23`)

```python
for status in [OrderStatus.RESERVED, OrderStatus.PRODUCING,
               OrderStatus.CONFIRMED, OrderStatus.RELEASE]:
    count = len(self._order_repo.find_by_status(status))
    print(f"  {status.value:<12} {count}건")   # 건수만 출력
```

### 문제

상태별 **건수(숫자)만** 출력하고 있음. 요구사항은 각 주문의 상세 정보를 포함한 **목록** 표시임.

### 기대 출력 (수정 후)

```
┌─ 주문 현황 ──────────────────────────────────────────────────┐

  ▶ RESERVED (2건)
  주문ID      시료ID    고객명        수량
  ──────────────────────────────────────────────────────────
  a1b2c3d4    S001      홍길동          10
  e5f6g7h8    S002      이순신           5

  ▶ CONFIRMED (1건)
  주문ID      시료ID    고객명        수량
  ──────────────────────────────────────────────────────────
  i9j0k1l2    S003      대학C           8
```

---

## 이슈 #2 — 출고(RELEASE) 시 재고 차감 (검토 필요)

### 현황

**SPEC/PRD** — 출고 시 재고 차감에 대한 **명시적 언급 없음**

**현재 구현 (`release_controller.py:18`)**
```python
order.status = OrderStatus.RELEASE
self._order_repo.save(order)  # 재고 차감 없음
```

**재고 흐름 분석**

| 시점 | 동작 | 재고 변화 |
|------|------|-----------|
| approve (재고 부족) | 생산 큐 등록 | 변화 없음 |
| complete_job | 생산 완료 | **+actual_production** |
| approve (재고 충분) | CONFIRMED | 변화 없음 |
| release | RELEASE | **변화 없음** (현재) |

### 논점

- SPEC에 재고 차감 미명시 → 설계 의도 확인 필요
- 출고 후에도 재고가 유지되면 **동일 재고로 중복 승인** 가능
- 모니터링의 "여유/부족/고갈" 판단 시 RELEASE된 주문도 active 주문처럼 집계될 수 있음
  - 현재 monitoring_view.py는 `RESERVED + PRODUCING` 주문 수량만 demand로 계산 → CONFIRMED 후 release 흐름에서는 큰 문제 없음

### 결론

SPEC 해석에 따라 두 가지 방향 가능:
- **A안**: 출고 시 재고 차감 (`sample.stock -= order.quantity`) — 물리적 재고 반영
- **B안**: 현행 유지 — 재고는 생산 투입 기준, 출고 여부와 무관

---

## 정상 구현 항목 ✅

| 항목 | 확인 |
|------|------|
| 주문 상태 전이 (RESERVED→CONFIRMED/PRODUCING→RELEASE) | ✅ |
| 생산량 계산 `ceil(부족분 / (수율 × 0.9))` | ✅ |
| 생산 큐 FIFO | ✅ |
| 생산 완료 시 재고 증가 + CONFIRMED 전환 | ✅ |
| 모니터링 재고 상태 태그 (여유/부족/고갈) | ✅ |
| MVC 아키텍처 | ✅ |
| JSON 영속성 | ✅ |
| Dummy Data 도구 | ✅ |
| 관리자 모니터링 도구 | ✅ |
| REJECTED 모니터링 제외 | ✅ |
| 시료 등록·조회·검색 | ✅ |
| 메인 메뉴 시료 요약 표시 | ✅ |
