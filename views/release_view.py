from controllers.release_controller import ReleaseController
from views.common import header, section, divider, success, error, ask, col


class ReleaseView:
    def __init__(self, ctrl: ReleaseController):
        self._ctrl = ctrl

    def show(self):
        header("출고 처리")
        confirmed = self._ctrl.list_confirmed()
        section("출고 대기 주문")
        if not confirmed:
            print("  출고 대기 중인 주문이 없습니다.")
            return
        print(f"  {col('No',5)} {col('주문ID',12)} {col('시료ID',8)} {col('고객명',12)} {'수량':>5}")
        divider()
        for i, o in enumerate(confirmed, 1):
            print(f"  [{i}]  {col(o.order_id[:8],12)} {col(o.sample_id,8)} {col(o.customer,12)} {o.quantity:>5}")
        print()
        try:
            idx = int(ask("번호 선택 >")) - 1
            if not (0 <= idx < len(confirmed)):
                error("올바른 번호를 선택해주세요.")
                return
            self._ctrl.release(confirmed[idx].order_id)
            success("출고 완료")
        except (ValueError, IndexError) as e:
            error(str(e))
