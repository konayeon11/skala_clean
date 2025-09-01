from dataclasses import dataclass
from typing import List, Dict, Optional
import random

@dataclass
class Beverage:
    """
    개별 음료(메뉴) 정보를 담는 데이터 클래스.
    - name: 음료 이름 (예: '아이스 아메리카노')
    - price: 가격(원). float로 둔 이유는 소수점 가격 정책을 허용하기 위함.
    - tags: 검색/추천 용도의 태그 목록 (예: ['커피', '콜드'])
    """
    name: str
    price: float
    tags: List[str]

class Order:
    """
    사용자의 '한 번의 주문 항목'을 표현하는 클래스.
    한 번의 주문은 특정 음료(Beverage)와 수량(quantity)로 구성된다.
    """
    __slots__ = ('beverage', 'quantity')  # 메모리 절약 및 속성 고정(오타/임의추가 방지)

    def __init__(self, beverage: Beverage, quantity: int):
        # 주문 대상 음료 객체
        self.beverage = beverage
        # 주문 수량 (1 이상 가정. 실제 서비스라면 유효성 검증 필요)
        self.quantity = quantity

    @property
    def total_price(self) -> float:
        """
        해당 주문 항목의 총금액 = 음료 단가 * 수량
        property로 노출해 읽기 전용 계산 속성처럼 사용.
        """
        return self.beverage.price * self.quantity
class User:
    """
    사용자(고객)를 표현하는 클래스.
    - name: 사용자 이름(식별자 대용)
    - orders: 사용자가 지금까지 담아온 주문 목록(List[Order])
    """
    def __init__(self, name: str):
        self.name = name
        self.orders: List[Order] = []  # 초기 주문 내역은 비어 있음

    def add_order(self, order: Order):
        """
        사용자의 주문 내역에 새로운 주문 항목(Order)을 추가.
        """
        self.orders.append(order)

    def get_total_spent(self) -> float:
        """
        지금까지 해당 사용자가 지출한 총액(원)을 계산.
        모든 주문 항목의 total_price 합.
        """
        return sum(order.total_price for order in self.orders)

    def get_recent_tags(self, n: int = 3) -> List[str]:
        """
        최근 n개의 주문을 기준으로 태그를 수집하여 반환.
        - 최근 주문일수록 사용자 취향 반영도가 높다고 가정.
        - set으로 중복을 제거 후 list로 변환해 반환.
        """
        tags = []
        # 슬라이싱 self.orders[-n:]: 주문 수가 n보다 적어도 안전하게 동작.
        for order in self.orders[-n:]:
            # 각 주문의 음료가 가진 태그들을 누적
            tags.extend(order.beverage.tags)
        # 중복 제거를 위해 set으로 변환했다가 다시 list로 변환
        return list(set(tags))

class OrderSystem:
    """
    주문/추천 시스템의 메인 진입점.
    - menu: 판매 중인 전체 음료 목록(List[Beverage])
    - users: 시스템에 등록된 사용자 목록(List[User])
    """
    def __init__(self, menu: List['Beverage']):
        self.menu = menu
        self.users: List[User] = []

    def find_beverage(self, name: str) -> Optional['Beverage']:
        """
        메뉴 목록에서 이름으로 음료를 검색해 반환.
        - 동일 이름이 여러 개인 경우 첫 번째 항목을 반환(일반적으로는 이름이 유니크라고 가정)
        - 없으면 None 반환
        """
        for beverage in self.menu:
            if beverage.name == name:
                return beverage
        return None

    def add_user(self, user: User):
        """
        새로운 사용자를 시스템에 등록.
        (간단한 리스트 추가지만, 확장 시 중복 사용자 검증/ID 발급 등 로직 추가 가능)
        """
        self.users.append(user)

    def recommend(self, user: User, count: int = 3) -> List['Beverage']:
        """
        최근 주문의 태그를 바탕으로 '태그가 겹치는' 다른 음료를 추천.
        - 이미 사용자가 주문했던 음료는 제외(새로운 경험 제공 가정)
        - count 개수만큼 잘라서 반환
        - 추천 로직은 단순 교집합 기반. (스코어링/정렬 로직은 필요 시 확장 가능)
        """
        if not user.orders:
            # 주문 내역이 없으면 랜덤 추천
            # 메뉴 개수가 count보다 적을 경우에도 min()을 써서 안전하게 처리.
            return random.sample(self.menu, min(count, len(self.menu)))

        # 사용자 최근 n(기본 3)건의 주문에서 모은 태그 집합
        recent_tags = set(user.get_recent_tags())

        # 메뉴 전체를 순회하며, (1) 아직 안 사봤고 (2) 태그 교집합이 있는 음료만 필터링
        recommendations = [
            b for b in self.menu
            if b not in [o.beverage for o in user.orders] and recent_tags & set(b.tags)
        ]

        # 상위 count개만 반환 (현재는 정렬 없이 필터링된 순서 그대로)
        return recommendations[:count]

# ---------------- 실행 예시 ----------------
if __name__ == "__main__":
    menu = [
        Beverage("아이스 아메리카노", 3000, ["커피", "콜드"]),
        Beverage("카페라떼", 3500, ["커피", "밀크"]),
        Beverage("녹차", 2800, ["차", "뜨거운"]),
        Beverage("허브티", 3000, ["차", "차가운"]),
        Beverage("아이스 라떼", 3700, ["커피", "밀크", "콜드"]),
        Beverage("에스프레소", 2500, ["커피", "뜨거운"]),
        Beverage("카푸치노", 3800, ["커피", "밀크", "뜨거운"]),
        Beverage("레몬에이드", 4000, ["에이드", "콜드"]),
        Beverage("홍차", 3200, ["차", "뜨거운"]),
        Beverage("민트초코프라푸치노", 4500, ["커피", "콜드", "스페셜"])
    ]

    system = OrderSystem(menu)

    # 사용자 등록
    user1 = User("홍길동")
    user2 = User("김영희")

    system.add_user(user1)
    system.add_user(user2)

    # 홍길동 주문
    bev = system.find_beverage("아이스 아메리카노")
    if bev:
        user1.add_order(Order(bev, 1))

    bev = system.find_beverage("카페라떼")
    if bev:
        user1.add_order(Order(bev, 2))

    # 김영희 주문
    bev = system.find_beverage("레몬에이드")
    if bev:
        user2.add_order(Order(bev, 1))

    bev = system.find_beverage("홍차")
    if bev:
        user2.add_order(Order(bev, 1))

    # 홍길동 추천 & 통계
    print("\n[홍길동]")
    print("추천 음료:", system.recommend(user1))
    print(f"총 주문 금액: {user1.get_total_spent()}원")
    print(f"평균 주문 금액: {user1.get_average_spent():.0f}원")

    # 김영희 추천 & 통계
    print("\n[김영희]")
    print("추천 음료:", system.recommend(user2))
    print(f"총 주문 금액: {user2.get_total_spent()}원")
    print(f"평균 주문 금액: {user2.get_average_spent():.0f}원")