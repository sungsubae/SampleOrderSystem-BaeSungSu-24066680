from pathlib import Path

from repositories.sample_repository import SampleRepository
from repositories.order_repository import OrderRepository
from repositories.production_repository import ProductionRepository
from controllers.sample_controller import SampleController
from controllers.order_controller import OrderController
from controllers.production_controller import ProductionController
from controllers.release_controller import ReleaseController
from views.main_view import MainView

DATA_DIR = Path("data")


def build_main_view(data_dir: Path = DATA_DIR) -> MainView:
    data_dir = Path(data_dir)
    data_dir.mkdir(exist_ok=True)

    sample_repo     = SampleRepository(data_dir / "samples.json")
    order_repo      = OrderRepository(data_dir / "orders.json")
    production_repo = ProductionRepository(data_dir / "production_queue.json")

    sample_ctrl     = SampleController(sample_repo)
    order_ctrl      = OrderController(sample_repo, order_repo, production_repo)
    production_ctrl = ProductionController(production_repo, order_repo, sample_repo)
    release_ctrl    = ReleaseController(order_repo=order_repo)

    return MainView(sample_ctrl, order_ctrl, production_ctrl, release_ctrl, order_repo)


if __name__ == "__main__":
    build_main_view().run()
