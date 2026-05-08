# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

반도체 회사 S-Semi의 **시료 생산주문관리 시스템** — 주문 접수부터 생산·출고까지 전 과정을 관리하는 Python 콘솔 애플리케이션이다.

## 실행 및 테스트 명령어

```bash
# 애플리케이션 실행
python main.py

# 전체 테스트 실행
python -m pytest

# 단일 테스트 파일 실행
python -m pytest tests/test_order.py

# 단일 테스트 함수 실행
python -m pytest tests/test_order.py::test_approve_order_with_sufficient_stock

# 커버리지 포함 테스트
python -m pytest --cov=. --cov-report=term-missing

# 더미 데이터 생성 (구현 후)
python tools/dummy_data.py

# 관리자용 데이터 모니터링 (구현 후)
python tools/monitor.py
```

## 참고 문서

기능 구현 전 아래 문서를 먼저 확인한다.

| 문서 | 설명 |
|------|------|
| [`docs/SPEC.md`](docs/SPEC.md) | 시스템 배경, 역할, 주문 상태 흐름, 기능별 요구사항 원문 |
| [`docs/PRD.md`](docs/PRD.md) | SPEC 기반의 구조화된 제품 요구사항 — 상태 전이 다이어그램, 생산량 계산 공식, 재고 상태 기준 등 포함 |
| [`docs/PLAN.md`](docs/PLAN.md) | TDD 기반 단계별 구현 계획 — Phase 1~12, 각 Phase별 테스트 케이스 및 구현 체크리스트 포함 |
| `docs/designs/phase{N}.md` | 각 Phase의 세부 설계 — 클래스 다이어그램, 필드 명세, 테스트 코드, 구현 코드 포함. Phase 진행 전 해당 문서를 먼저 확인한다. |

## 아키텍처

MVC 패턴을 따르며, JSON 파일로 데이터를 영속한다.

## 의존성

`.venv`에 파이썬 가상환경이 구성되어있다.
표준 라이브러리 외 추가 패키지 설치가 필요한 경우 `.venv`에 설치 후 `requirements.txt`를 업데이트한다.
