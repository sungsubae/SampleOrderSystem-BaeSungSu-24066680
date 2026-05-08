from controllers.sample_controller import SampleController
from views.common import header, section, divider, success, error, ask, ask_float, menu_item


class SampleView:
    def __init__(self, ctrl: SampleController):
        self._ctrl = ctrl

    def menu(self):
        while True:
            header("시료 관리")
            menu_item(1, "시료 등록")
            menu_item(2, "시료 목록 조회")
            menu_item(3, "시료 검색")
            menu_item(0, "돌아가기")
            print()
            choice = ask("선택 >")
            if choice == "1":
                self._register()
            elif choice == "2":
                self._list_all()
            elif choice == "3":
                self._search()
            elif choice == "0":
                break
            else:
                error("올바른 메뉴를 선택해주세요.")

    def _register(self):
        header("시료 등록")
        try:
            sample_id  = ask("시료 ID          >")
            name       = ask("이름             >")
            avg_time   = ask_float("평균 생산시간(h)  >")
            yield_rate = ask_float("수율 (0 초과 1 이하)>")
            self._ctrl.register(sample_id=sample_id, name=name, avg_time=avg_time, yield_rate=yield_rate)
            success(f"시료 '{name}' 등록 완료")
        except ValueError as e:
            error(str(e))

    def _list_all(self):
        samples = self._ctrl.list_all()
        section("시료 목록")
        if not samples:
            print("  등록된 시료가 없습니다.")
            return
        print(f"  {'ID':<12} {'이름':<14} {'생산시간':>8}  {'수율':>6}  {'재고':>5}")
        divider()
        for s in samples:
            print(f"  {s.sample_id:<12} {s.name:<14} {s.avg_production_time:>6.1f}h  {s.yield_rate*100:>5.1f}%  {s.stock:>5}")

    def _search(self):
        header("시료 검색")
        keyword = ask("검색어 >")
        results = self._ctrl.search(keyword)
        section(f"검색 결과 — '{keyword}'")
        if not results:
            print("  검색 결과가 없습니다.")
            return
        print(f"  {'ID':<12} {'이름':<14} {'재고':>5}")
        divider()
        for s in results:
            print(f"  {s.sample_id:<12} {s.name:<14} {s.stock:>5}")
