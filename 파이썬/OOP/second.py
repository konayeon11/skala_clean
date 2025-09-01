class User:
    def __init__(self, name: str):
    self.name = name
    self.orders: List[Order] = []

    def add_order(self, order: Order):
    self.orders.append(order)

    def get_total_spent(self) -> float:
    return sum(order.total_price for order in self.orders)

    def get_recent_tags(self, n: int = 3) -> List[str]:
        tags = []

        for order in self.orders[-n:]:
            tags.extend(order.beverage.tags)
        return list(set(tags))