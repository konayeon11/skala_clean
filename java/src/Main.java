/**
==========================================
파일명   : Main.java
목적     : 자바의 4대 OOP 개념(캡슐화·추상화·다형성·상속)을
          하나의 실행 파일로 데모하는 학습용 코드 모음
작성자   : 고나연
작성일   : 2025-09-01
버전     : Java 17+
설명     :
    - 본 파일 하나에 여러 클래스를 정의하여, 각 개념을 독립 섹션으로 시연
    - 섹션 구성
        (1) 캡슐화: Person, BankAccount
        (2) 추상화: abstract class Asset, interface Valuable, 구현 Stock
        (3) 다형성: Animal–Dog–Cat(상속 기반), Drivable–Electric/GasolineCar(인터페이스 기반)
        (4) 상속: Stock → PreferredStock(오버라이딩, 업캐스팅/다운캐스팅)
    - 모든 클래스는 package-private로 두고, 파일명과 동일한 public 클래스(Main)만 둠
    - 각 섹션별로 콘솔 출력 예시를 통해 동작 확인

주요 기능(실행 흐름):
    1) main()에서 섹션별 데모 메서드 호출
    2) 캡슐화  : private 필드 + getter/setter 유효성 검사
    3) 추상화  : "무엇(인터페이스/추상메서드)"만 정해두고 구현은 구체 클래스에서
    4) 다형성  : 같은 메서드 호출이라도 실제 타입에 따라 다른 동작(오버라이딩)
    5) 상속    : is-a 관계, super()로 부모 초기화, 업/다운캐스팅

참고     :
    - 캡슐화   : 접근 제어자(public/protected/default/private)와 getter/setter
    - 추상화   : abstract class(공통 속성/일부 구현 공유), interface(역할/규약, 다중 구현)
    - 다형성   : 상속 + 오버라이딩 + 업캐스팅, 또는 인터페이스 다형성
    - 상속     : 재사용/확장, 단 남용 시 강결합 → 조합(Composition)도 고려
==========================================
*/

// ==============================
// (1) 캡슐화 (Encapsulation)
//  - 필드를 private으로 은폐하고, 공개 메서드(getter/setter)로만 간접 접근
//  - setter에서 유효성 검사/로깅/권한체크 등을 수행 가능
// ==============================
class Person {
    // 외부 직접 접근 차단
    private String name;
    private int age;

    public Person(String name, int age) {
        this.name = name;
        setAge(age); // 생성 시에도 동일한 유효성 정책 적용
    }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public int getAge() { return age; }

    // 캡슐화의 핵심: setter에서 유효성 검사
    public void setAge(int age) {
        if (age >= 0) this.age = age;
        else System.out.println("[WARN] 나이는 음수가 될 수 없습니다. 값 무시됨.");
    }
}

// 은행 계좌 예제: 은폐된 잔액은 입금/출금 메서드로만 변경 가능
class BankAccount {
    private int balance;

    public BankAccount(int initialBalance) {
        this.balance = Math.max(0, initialBalance);
    }

    public int getBalance() { return balance; }

    public void deposit(int amount) {
        if (amount > 0) balance += amount;
    }

    public void withdraw(int amount) {
        if (amount > 0 && amount <= balance) balance -= amount;
    }
}

// ==============================
// (2) 추상화 (Abstraction)
//  - "무엇을 해야 하는지(What)"만 노출하고 "어떻게(How)"는 감춤
//  - 도구: abstract class, interface
//  - abstract class: 공통 속성/일부 구현 공유 + 추상 메서드로 규약
//  - interface: 역할/계약(규약) 정의, 다중 구현 가능, default 메서드로 공통 동작 제공 가능
// ==============================

// 공통 추상 클래스: 자산(공통 속성 보유 + 정보 출력 규약만 정의)
abstract class Asset {
    protected String name;
    protected double price;

    public Asset(String name, double price) {
        this.name = name;
        this.price = price;
    }

    // "자산 정보는 출력할 수 있어야 한다"라는 규약(무엇)
    public abstract void printInfo(); // 구현은 자식이 결정(어떻게)
}

// 역할/규약 인터페이스: 가치가 있는 대상
interface Valuable {
    void printInfo(); // 구현 강제(규약)

    // 자바 8+: 구현을 포함한 기본 동작 제공도 가능
    default void updatePrice(double newPrice) {
        System.out.println("가격 갱신: " + newPrice + "원");
    }
}

// 구체 클래스: 주식(자산의 일종이며, 가치 있는 대상 역할을 수행)
class Stock extends Asset implements Valuable {
    public Stock(String name, double price) {
        super(name, price);
    }

    // 추상화된 규약을 구체 구현(오버라이딩)
    @Override
    public void printInfo() {
        System.out.println("[일반주] 종목: " + name + ", 가격: " + price + "원");
    }
}

// ==============================
// (3) 다형성 (Polymorphism)
//  - 같은 메서드 호출이라도 "실제 타입"에 따라 다른 동작
//  - 상속 + 오버라이딩 + 업캐스팅으로 실현되거나,
//    인터페이스 참조(역할 기반)로도 실현 가능
// ==============================

// 상속 기반 다형성
class Animal {
    public void makeSound() {
        System.out.println("동물이 소리를 낸다");
    }
}
class Dog extends Animal {
    @Override
    public void makeSound() { System.out.println("멍멍"); }
}
class Cat extends Animal {
    @Override
    public void makeSound() { System.out.println("야옹"); }
}

// 인터페이스 기반 다형성
interface Drivable {
    void drive();
}
class ElectricCar implements Drivable {
    @Override
    public void drive() { System.out.println("전기 모터로 달립니다"); }
}
class GasolineCar implements Drivable {
    @Override
    public void drive() { System.out.println("내연 기관으로 달립니다"); }
}

// ==============================
// (4) 상속 (Inheritance)
//  - is-a 관계(PreferredStock is a Stock)
//  - super()로 부모 초기화 → 공통 초기화 재사용
//  - 오버라이딩으로 차별화
//  - 업캐스팅(자식→부모 참조) 시에도 오버라이딩 메서드는 자식 구현이 실행
//  - 필요 시 instanceof 확인 후 다운캐스팅으로 자식 고유 기능 사용
// ==============================
class PreferredStock extends Stock {
    private double dividendRate;

    public PreferredStock(String name, double price, double dividendRate) {
        super(name, price);            // 부모(Stock) 초기화
        this.dividendRate = dividendRate;
    }

    @Override
    public void printInfo() {
        // 부모가 물려준 필드(name, price)를 활용하면서 표현은 확장
        System.out.println(
            "[우선주] 종목: " + name +
            ", 가격: " + /* price는 부모 protected 이므로 자식에서 접근 가능 */ 
            // 보호수준 시연을 위해 접근은 메서드로 표현
            getReadablePrice() + "원, 배당률: " + dividendRate + "%"
        );
    }

    // 데모 편의용: price를 문자열로 가공(보안/정책상 직접 노출 안 할 수도 있다는 가정)
    private String getReadablePrice() {
        return String.valueOf((long)super.price);
    }

    public void showDividend() {
        System.out.println("배당률 안내: " + dividendRate + "%");
    }
}

// ==============================
// 실행 진입점: 단일 public 클래스(Main)
// 각 섹션을 메서드로 분리 호출하여 콘솔에 결과를 시연
// ==============================
public class Main {

    public static void main(String[] args) {
        demoEncapsulation();
        demoAbstraction();
        demoPolymorphism();
        demoInheritance();
    }

    // --- (1) 캡슐화 데모 ---
    private static void demoEncapsulation() {
        System.out.println("\n=== (1) Encapsulation ===");
        Person p = new Person("Alice", 20);
        p.setAge(-5);  // 유효성 실패 → 경고 출력, 값 미변경
        p.setAge(25);
        System.out.println("이름=" + p.getName() + ", 나이=" + p.getAge());

        BankAccount account = new BankAccount(1000);
        account.deposit(500);
        account.withdraw(200);
        // account.balance = 99999; // 컴파일 오류(은폐) 예시 — 주석으로만 설명
        System.out.println("잔액=" + account.getBalance());
    }

    // --- (2) 추상화 데모 ---
    private static void demoAbstraction() {
        System.out.println("\n=== (2) Abstraction ===");
        Stock s = new Stock("ACME", 12345.0);
        s.printInfo();         // "무엇(정보 출력)"을 구현한 구체 동작
        s.updatePrice(15000);  // 인터페이스 default 메서드 사용
    }

    // --- (3) 다형성 데모 ---
    private static void demoPolymorphism() {
        System.out.println("\n=== (3) Polymorphism ===");

        // 상속 기반: 업캐스팅(부모 타입 참조) + 오버라이딩 실행
        Animal a1 = new Dog();
        Animal a2 = new Cat();
        a1.makeSound(); // 멍멍
        a2.makeSound(); // 야옹

        // 인터페이스 기반: 같은 역할(Drivable)로 서로 다른 구현 동작
        Drivable ev = new ElectricCar();
        Drivable gv = new GasolineCar();
        ev.drive(); // 전기 모터로 달립니다
        gv.drive(); // 내연 기관으로 달립니다
    }

    // --- (4) 상속 데모 ---
    private static void demoInheritance() {
        System.out.println("\n=== (4) Inheritance ===");

        // 우선주 is-a 주식 → 업캐스팅 가능
        Stock s = new PreferredStock("K-BlueChip", 50000.0, 5.0);
        s.printInfo();  // 자식의 오버라이딩이 실행됨

        // 부모 타입에는 없는 자식 고유 기능 사용하려면 다운캐스팅 필요
        if (s instanceof PreferredStock ps) {
            ps.showDividend(); // 배당률 안내: 5.0%
        }
    }
}