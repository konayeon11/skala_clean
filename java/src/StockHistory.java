import java.text.DecimalFormat;

public class StockHistory {
    public static void main(String[] args) {
        // 데이터
        String[] stocks = {"SKALA", "EDUAI", "KQTECH"};
        int[] prices = {12300, 9850, 23000};
        int[] yesterdayPrices = {12000, 10200, 22000};

        // 숫자 포맷 (가격: 천 단위 콤마 / 등락률: 소수점 둘째 자리)
        DecimalFormat priceFormat = new DecimalFormat("#,###");
        DecimalFormat rateFormat = new DecimalFormat("+0.00%;-0.00%"); 
        // ↑ 양수면 + 붙고, 음수면 - 표시됨

        // StringBuilder로 출력 문자열 조립
        StringBuilder sb = new StringBuilder();
        sb.append(String.format("%-8s %-10s %-10s %-8s\n", "종목명", "전일가", "현재가", "등락률"));

        for (int i = 0; i < stocks.length; i++) {
            double rate = (double)(prices[i] - yesterdayPrices[i]) / yesterdayPrices[i];
            sb.append(String.format(
                "%-8s %-10s %-10s %-8s\n",
                stocks[i],
                priceFormat.format(yesterdayPrices[i]),
                priceFormat.format(prices[i]),
                rateFormat.format(rate)
            ));
        }

        // 최종 출력
        System.out.println(sb.toString());
    }
}