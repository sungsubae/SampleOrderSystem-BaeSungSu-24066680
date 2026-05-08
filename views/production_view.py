from controllers.production_controller import ProductionController
from views.common import header, section, divider, success, error, ask


class ProductionView:
    def __init__(self, ctrl: ProductionController):
        self._ctrl = ctrl

    def show(self):
        header("생산 라인")
        self._show_current()
        self._show_queue()
        self._handle_complete()

    def _show_current(self):
        section("현재 생산 중")
        job = self._ctrl.get_current_job()
        if job is None:
            print("  현재 생산 중인 작업이 없습니다.")
            return
        print(f"  주문 ID  : {job.order_id[:8]}…")
        print(f"  시료 ID  : {job.sample_id}")
        print(f"  생산 수량: {job.actual_production}개")
        print(f"  예상 시간: {job.total_time:.1f}h")

    def _show_queue(self):
        section("대기 큐 (FIFO)")
        queue = self._ctrl.list_queue()
        if not queue:
            print("  대기 중인 작업이 없습니다.")
            return
        print(f"  {'순서':<5} {'주문 ID':<14} {'시료 ID':<10} {'생산 수량':>8}  {'예상 시간':>8}")
        divider()
        for i, job in enumerate(queue, 1):
            print(f"  [{i}]   {job.order_id[:8]:<14} {job.sample_id:<10} {job.actual_production:>8}  {job.total_time:>7.1f}h")

    def _handle_complete(self):
        if self._ctrl.get_current_job() is None:
            return
        print()
        order_id = ask("완료 처리할 주문 ID 입력 (건너뛰려면 Enter) >")
        if not order_id:
            return
        try:
            self._ctrl.complete_job(order_id)
            success("생산 완료 처리되었습니다.")
        except (ValueError, IndexError) as e:
            error(str(e))
