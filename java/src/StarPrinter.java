public class StarPrinter {
    public static void main(String[] args) {

        // ----------------------------
        // 1) 왼쪽 정렬: 1개부터 5개까지
        // ----------------------------
        System.out.println("왼쪽 정렬 출력:");
        for (int i = 1; i <= 5; i++) {       //5개까지 증가하면서
            for (int j = 1; j <= i; j++) {   //i가 증가(아래로 내려갈때마다) 층수에 맞는 별 갯수 찍기
                System.out.print("*");
            }
            System.out.println(); //줄 바꾸기
        }

        System.out.println(); // 구분용 빈 줄

        // ----------------------------
        // 2) 가운데 정렬: 홀수 개 (1 ~ 9개)
        // ----------------------------
        System.out.println("가운데 정렬 출력:");
        int lines = 5; // 총 줄 수
        for (int i = 0; i < lines; i++) {             //5째 줄이 마지막줄
            // 왼쪽 공백
            for (int j = 0; j < lines - i - 1; j++) { //라인수에서 해당 단계와 1 뺀 만큼 공백 찍기
                System.out.print(" ");
            }
            // 별 출력 (홀수 개: 2*i + 1)
            for (int j = 0; j < 2 * i + 1; j++) {    //각 단계에 2 곱하고 1을 더한 수만큼 별 찍기
                System.out.print("*");
            }
            System.out.println(); // 줄 바꾸기
        }
    }
}
    

